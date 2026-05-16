# HDB Flats 3D Simulator

A full-stack web app that visualizes Singapore's HDB flats in 3D and simulates residence growth, decline, and inter-flat moves year-over-year.



---

## What it does

- Renders HDB blocks in 3D (React + three.js via react-three-fiber) on top of a green-filled Singapore boundary.
- Click any building to see full address, 1- to 5-room unit counts, and occupied units in the side panel.
- **Randomize**: assigns a random number of residents to each flat based on available units.
- **Start**: ticks the simulation yearly. Each year applies births (~0.85% / pop), deaths (~0.61% / pop), and ~1.5% of residents move to other flats. Singapore rates used by default.
- Buildings are colored on a gradient from most vacant (blue) to mid (violet) to most populated (red).
- Side panel shows current year, years simulated, total residents, cumulative deaths, and deaths/births this year.
- Movement log entries read like "12 residents from Blk 1 Ang Mo Kio Ave 3 to Blk 88 Marine Parade Central".
- Timeline scrubber: drag back through any year of a simulation.
- Sessions: create, save, list, re-load, and delete. Each year's state is a DB snapshot.
- Pause halts ticking.

---

## Repo layout

```
hdb-simulator/
├── README.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   ├── scripts/ingest.py
│   ├── data/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── store/useStore.js
│   │   └── api/client.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
└── infra/
    ├── cloudbuild.yaml
    └── main.tf
```

---

## Quick start (Docker)

Requires Docker and Docker Compose.

```bash
git clone https://github.com/Unknownplaylist/hdb-simulator.git
cd hdb-simulator
docker compose up --build
```

Open http://localhost:8080.

1. `backend` runs FastAPI on `:8000` (container port 8080).
2. `ingest` seeds SQLite with the bundled 10,966 HDB buildings.
3. `frontend` builds the React app and serves it from nginx on `:8080`, proxying `/api/*` to the backend.

---

## Quick start (without Docker)

Requires Python 3.11+ and Node 20+.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.ingest
uvicorn app.main:app --reload --port 8000
```

API at http://localhost:8000. Swagger UI at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api/*` to http://localhost:8000.

---

## Usage

1. Create a session in the top-left panel.
2. Click `Randomize` in the bottom bar to seed initial occupancy.
3. Click `+1 Year` to advance one year, or `Start` to auto-tick every 1.5s.
4. Drag the timeline slider to scrub through past years.
5. Click any building to inspect its address and unit-level occupancy.
6. Reload the page and pick a session from the list to restore its history.

---

## Dataset

`backend/data/buildings_sample.geojson` contains 10,966 HDB blocks extracted from [`ualsg/hdb3d-data`](https://github.com/ualsg/hdb3d-data): Point features with WGS84 centroids, real heights (4-141 m), real footprint areas, and per-block 1- to 5-room unit counts joined from `hdb_<n>room_sold + hdb_<n>room_rental`. The boundary in `data/sg_boundary.geojson` is the dissolved MultiPolygon from [`yinshanyang/singapore`](https://github.com/yinshanyang/singapore).

Two ingest scripts:

- **`scripts/ingest.py`** — loads the bundled GeoJSON (Polygon or Point) into the `buildings` table. Idempotent.
- **`scripts/ingest_cityjson.py`** — re-runs SVY21 to WGS84 reprojection from raw CityJSON:

```bash
git clone https://github.com/ualsg/hdb3d-data.git external/hdb3d-data
python -m scripts.ingest_cityjson external/hdb3d-data/hdb.json
```

It decodes the CityJSON quantized vertex pool, picks the bottom face of each LoD 1.2 prism as the footprint, reprojects centroids with `pyproj`, and writes both DB rows and a refreshed GeoJSON.

---



## Running the simulation engine standalone

```python
import numpy as np
from app import simulation

units = np.array([[0, 12, 48, 30, 24], [6, 18, 60, 36, 30]], dtype=np.int32)
rng = np.random.default_rng(42)
occ = simulation.random_assign(units, rng)

for year in range(5):
    r = simulation.tick(units, occ, rng)
    occ = r.new_occupancy
    print(f"Y+{year+1}  pop={r.new_residents.sum()}  +{r.births}  -{r.deaths}  moves={r.moves}")
```

---

## API reference

FastAPI auto-docs at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/buildings` | List all HDB buildings |
| `GET` | `/buildings/{id}?session_id=X` | Building + occupancy from session X's current year |
| `GET` | `/geo/boundary` | SG boundary GeoJSON |
| `POST` | `/sessions` | Create session |
| `GET` | `/sessions` | List sessions |
| `DELETE` | `/sessions/{id}` | Delete session |
| `POST` | `/sessions/{id}/randomize` | Random initial occupancy |
| `POST` | `/sessions/{id}/tick` | Advance one year |
| `POST` | `/sessions/{id}/pause` | Mark session paused |
| `GET` | `/sessions/{id}/snapshots` | Years with snapshots |
| `GET` | `/sessions/{id}/snapshots/{year}` | Snapshot for a year |
| `GET` | `/sessions/{id}/movements?year=Y` | Movement log for a year |

---

