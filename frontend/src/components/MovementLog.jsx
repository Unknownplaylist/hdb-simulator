import { useStore } from '../store/useStore'

export function MovementLog() {
  const movements = useStore(s => s.movements)
  const buildings = useStore(s => s.buildings)
  const buildingIndex = useStore(s => s.buildingIndex)
  const snapshot = useStore(s => s.snapshot)

  if (!snapshot) return null

  const labelFor = (id) => {
    const b = buildings[buildingIndex[id]]
    return b ? `Blk ${b.block_no} ${b.street}` : `Blk #${id}`
  }

  return (
    <aside className="panel absolute bottom-0 right-4 w-80 max-h-56 rounded-md p-3 flex flex-col">
      <header className="flex items-center justify-between mb-2">
        <h2 className="mono text-sm text-accent">MOVEMENTS · Y{snapshot.year}</h2>
        <span className="tag">{movements.length}</span>
      </header>
      {movements.length === 0 && (
        <p className="text-neutral-500 text-xs italic">No moves yet — run a tick to populate.</p>
      )}
      <div className="overflow-auto flex-1 -mx-1 px-1">
        {movements.map((m, i) => (
          <div key={i} className="text-[11px] py-0.5 border-b border-edge last:border-0">
            <span className="mono text-accent">{m.residents}</span>
            <span className="text-neutral-400"> from </span>
            <span className="text-neutral-200">{labelFor(m.from_building_id)}</span>
            <span className="text-neutral-400"> → </span>
            <span className="text-neutral-200">{labelFor(m.to_building_id)}</span>
          </div>
        ))}
      </div>
    </aside>
  )
}
