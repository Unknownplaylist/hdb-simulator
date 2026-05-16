import { useStore } from '../store/useStore'

export function SidePanel() {
  const session = useStore(s => s.session)
  const snapshot = useStore(s => s.snapshot)
  const detail = useStore(s => s.selectedDetail)
  const selectBuilding = useStore(s => s.selectBuilding)

  const totals = snapshot?.state?.totals || {}

  return (
    <aside className="panel absolute top-4 right-4 w-80 p-4 rounded-md text-sm">
      <header className="flex items-baseline justify-between mb-3">
        <h2 className="mono text-lg text-accent">HDB · STATS</h2>
        <span className="tag">{session?.status || '—'}</span>
      </header>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <Stat label="Year" value={snapshot?.year ?? '—'} />
        <Stat label="Years sim'd" value={(snapshot?.year ?? 2025) - 2025} />
        <Stat label="Residents" value={fmt(totals.residents)} />
        <Stat label="Passed away" value={fmt(totals.deaths_total)} />
        <Stat label="Deaths /yr" value={fmt(totals.deaths_this_year)} />
        <Stat label="Births /yr" value={fmt(totals.births_this_year)} />
      </div>

      <div className="divider my-3" />

      <h3 className="mono text-xs uppercase tracking-wider text-neutral-400 mb-2">
        Selected Building
      </h3>
      {!detail && (
        <p className="text-neutral-500 text-xs italic">
          Click a building in the scene to inspect.
        </p>
      )}
      {detail && (
        <div className="space-y-1">
          <p className="text-neutral-100 leading-tight">{detail.full_address}</p>
          <p className="text-xs text-neutral-400">Postal {detail.postal_code}</p>
          <div className="mt-2 grid grid-cols-3 gap-x-2 gap-y-1 text-xs">
            <span className="col-span-3 mono text-neutral-500 mt-1">UNITS BY ROOM TYPE</span>
            <UnitRow label="1-rm" total={detail.units_1r} occ={detail.occupied_units_1r} />
            <UnitRow label="2-rm" total={detail.units_2r} occ={detail.occupied_units_2r} />
            <UnitRow label="3-rm" total={detail.units_3r} occ={detail.occupied_units_3r} />
            <UnitRow label="4-rm" total={detail.units_4r} occ={detail.occupied_units_4r} />
            <UnitRow label="5-rm" total={detail.units_5r} occ={detail.occupied_units_5r} />
            <span className="col-span-3 divider my-1" />
            <span className="mono text-neutral-400">Total units</span>
            <span className="col-span-2 text-right">{detail.total_units}</span>
            <span className="mono text-neutral-400">Residents</span>
            <span className="col-span-2 text-right text-accent">{detail.residents}</span>
          </div>
          <button className="btn mt-3 w-full" onClick={() => selectBuilding(null)}>
            Clear
          </button>
        </div>
      )}
    </aside>
  )
}

function Stat({ label, value }) {
  return (
    <div className="border border-edge rounded px-2 py-1.5">
      <div className="mono text-[10px] uppercase tracking-wider text-neutral-500">{label}</div>
      <div className="text-base text-neutral-100">{value}</div>
    </div>
  )
}

function UnitRow({ label, total, occ }) {
  return (
    <>
      <span className="mono text-neutral-400">{label}</span>
      <span className="text-right">{occ}/{total}</span>
      <Bar pct={total > 0 ? occ / total : 0} />
    </>
  )
}

function Bar({ pct }) {
  return (
    <div className="h-1.5 bg-edge rounded overflow-hidden mt-1.5 self-center">
      <div className="h-full bg-accent" style={{ width: `${pct * 100}%` }} />
    </div>
  )
}

function fmt(n) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-US').format(n)
}
