from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Residents per unit by room type (1r..5r).
CAPACITIES = np.array([1, 2, 4, 5, 6], dtype=np.int32)

BIRTH_RATE = 0.0085      # per resident per year (DOS 2024 baseline)
DEATH_RATE = 0.0061      # per resident per year
MOVE_FRACTION = 0.015    # share of residents who relocate each year
MOVE_BATCH_MEAN = 2.0    # mean household size per move


@dataclass
class TickResult:
    new_occupancy: np.ndarray
    new_residents: np.ndarray
    births: int
    deaths: int
    moves: int
    movement_records: list[tuple[int, int, int]]


def random_assign(units: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng()
    return rng.integers(low=0, high=units + 1)


def residents_from_occupancy(occupancy: np.ndarray) -> np.ndarray:
    return occupancy @ CAPACITIES


def tick(
    units: np.ndarray,
    occupancy: np.ndarray,
    rng: np.random.Generator | None = None,
) -> TickResult:
    rng = rng or np.random.default_rng()
    n_buildings = units.shape[0]

    residents = residents_from_occupancy(occupancy)
    total_pop = int(residents.sum())

    births = int(rng.poisson(max(total_pop * BIRTH_RATE, 0.0)))
    free_units = units - occupancy
    occupancy = _add_residents_random(occupancy, free_units, births, rng)

    deaths = int(rng.poisson(max(total_pop * DEATH_RATE, 0.0)))
    deaths = min(deaths, int(residents_from_occupancy(occupancy).sum()))
    occupancy = _remove_residents_random(occupancy, deaths, rng)

    residents_after = residents_from_occupancy(occupancy)
    moves_target = int(residents_after.sum() * MOVE_FRACTION)
    movement_records: list[tuple[int, int, int]] = []
    moves_done = 0

    if moves_target > 0 and n_buildings > 1:
        pop_weights = residents_after.astype(np.float64)
        pop_weights = pop_weights / pop_weights.sum() if pop_weights.sum() else None

        free_capacity = ((units - occupancy) * CAPACITIES).sum(axis=1).astype(np.float64)
        free_weights = free_capacity / free_capacity.sum() if free_capacity.sum() else None

        # Cap iterations so a degenerate distribution can't loop forever.
        for _ in range(min(moves_target, 5000)):
            if moves_done >= moves_target:
                break
            if pop_weights is None or free_weights is None:
                break
            src = int(rng.choice(n_buildings, p=pop_weights))
            dst = int(rng.choice(n_buildings, p=free_weights))
            if src == dst:
                continue
            batch = max(1, int(rng.poisson(MOVE_BATCH_MEAN)))
            actually_moved = _move_residents(occupancy, units, src, dst, batch, rng)
            if actually_moved > 0:
                movement_records.append((src, dst, actually_moved))
                moves_done += actually_moved

    return TickResult(
        new_occupancy=occupancy,
        new_residents=residents_from_occupancy(occupancy),
        births=births,
        deaths=deaths,
        moves=moves_done,
        movement_records=movement_records,
    )


def _add_residents_random(occupancy, free_units, count, rng):
    if count <= 0:
        return occupancy
    free_flat = free_units.reshape(-1).astype(np.float64)
    if free_flat.sum() == 0:
        return occupancy
    probs = free_flat / free_flat.sum()
    n_cells = free_flat.size
    additions = np.zeros_like(free_flat, dtype=np.int32)
    picks = rng.choice(n_cells, size=count, replace=True, p=probs)
    for cell in picks:
        if free_flat[cell] - additions[cell] > 0:
            additions[cell] += 1
    return occupancy + additions.reshape(occupancy.shape)


def _remove_residents_random(occupancy, count, rng):
    if count <= 0:
        return occupancy
    occ_flat = occupancy.reshape(-1).astype(np.float64)
    if occ_flat.sum() == 0:
        return occupancy
    probs = occ_flat / occ_flat.sum()
    n_cells = occ_flat.size
    removals = np.zeros_like(occ_flat, dtype=np.int32)
    picks = rng.choice(n_cells, size=count, replace=True, p=probs)
    for cell in picks:
        if occ_flat[cell] - removals[cell] > 0:
            removals[cell] += 1
    return occupancy - removals.reshape(occupancy.shape)


def _move_residents(occupancy, units, src, dst, batch, rng):
    src_occupied_types = np.where(occupancy[src] > 0)[0]
    if len(src_occupied_types) == 0:
        return 0
    dst_free_types = np.where(units[dst] - occupancy[dst] > 0)[0]
    if len(dst_free_types) == 0:
        return 0
    src_type = int(rng.choice(src_occupied_types))
    dst_type = int(rng.choice(dst_free_types))
    occupancy[src, src_type] -= 1
    occupancy[dst, dst_type] += 1
    return int(CAPACITIES[src_type])
