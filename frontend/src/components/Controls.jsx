import { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'

export function ControlBar() {
  const session = useStore(s => s.session)
  const isPlaying = useStore(s => s.isPlaying)
  const availableYears = useStore(s => s.availableYears)
  const scrubYear = useStore(s => s.scrubYear)
  const { randomize, tick, play, pause, refreshSnapshot } = useStore.getState()

  if (!session) return null

  const minY = availableYears[0] ?? 2025
  const maxY = availableYears[availableYears.length - 1] ?? 2025

  return (
    <div className="panel absolute bottom-4 left-4 right-4 mx-auto max-w-4xl px-4 py-3 rounded-md">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="mono text-xs text-neutral-500">SESSION</span>
        <span className="text-accent mono">{session.name}</span>
        <span className="tag">YEAR {scrubYear ?? session.current_year}</span>

        <div className="flex-1 min-w-[200px] mx-2">
          <input
            type="range"
            min={minY}
            max={maxY}
            value={scrubYear ?? maxY}
            disabled={availableYears.length <= 1}
            onChange={(e) => refreshSnapshot(parseInt(e.target.value))}
            className="w-full accent-[#7CFFB2]"
          />
          <div className="flex justify-between mono text-[10px] text-neutral-500 mt-0.5">
            <span>{minY}</span>
            <span>{maxY}</span>
          </div>
        </div>

        <button className="btn" onClick={randomize}>
          Randomize
        </button>
        {!isPlaying ? (
          <button className="btn primary" onClick={play}>▶ Start</button>
        ) : (
          <button className="btn" onClick={pause}>❚❚ Pause</button>
        )}
        <button className="btn" onClick={tick} disabled={isPlaying}>+1 Year</button>
      </div>
    </div>
  )
}

export function SessionManager() {
  const [open, setOpen] = useState(true)
  const [name, setName] = useState('')
  const [sessions, setSessions] = useState([])
  const session = useStore(s => s.session)
  const { newSession, loadSession, deleteSession } = useStore.getState()

  async function refresh() {
    const { api } = await import('../api/client')
    setSessions(await api.listSessions())
  }

  useEffect(() => { refresh() }, [session?.id, session?.status, session?.current_year])

  async function handleDelete(e, s) {
    e.stopPropagation()
    if (!confirm(`Delete session "${s.name}"? This removes its snapshots and movement log.`)) return
    await deleteSession(s.id)
    refresh()
  }

  return (
    <aside className="panel absolute top-4 left-4 w-72 p-4 rounded-md text-sm">
      <header className="flex items-center justify-between mb-3">
        <h2 className="mono text-lg text-accent">SESSIONS</h2>
        <button className="btn" onClick={() => { setOpen(o => !o); refresh() }}>
          {open ? '–' : '+'}
        </button>
      </header>
      {open && (
        <>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              placeholder="session name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="flex-1 bg-ink border border-edge rounded px-2 py-1 text-sm focus:border-accent outline-none"
            />
            <button
              className="btn primary"
              disabled={!name.trim()}
              onClick={async () => { await newSession(name.trim()); setName(''); refresh() }}
            >New</button>
          </div>

          <div className="max-h-44 overflow-auto -mx-1 px-1">
            {sessions.length === 0 && (
              <p className="text-neutral-500 text-xs italic">No saved sessions yet.</p>
            )}
            {sessions.map(s => (
              <div
                key={s.id}
                role="button"
                tabIndex={0}
                onClick={() => loadSession(s.id)}
                onKeyDown={(e) => { if (e.key === 'Enter') loadSession(s.id) }}
                className={`group relative w-full text-left px-2 py-1.5 my-0.5 border rounded text-xs cursor-pointer hover:border-accent
                  ${session?.id === s.id ? 'border-accent text-accent' : 'border-edge text-neutral-300'}`}
              >
                <div className="flex justify-between pr-5">
                  <span className="truncate">{s.name}</span>
                  <span className="mono text-neutral-500">y{s.current_year}</span>
                </div>
                <div className="mono text-[10px] text-neutral-500">
                  {new Date(s.created_at).toLocaleDateString()} · {s.status}
                </div>
                <button
                  type="button"
                  aria-label={`Delete session ${s.name}`}
                  title="Delete session"
                  onClick={(e) => handleDelete(e, s)}
                  className="absolute top-1 right-1 px-1.5 text-neutral-500 hover:text-red-400 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          {sessions.length === 0 && (
            <p className="mt-2 text-[11px] text-neutral-500 leading-snug">
              Tip: Create a session, click <span className="mono">Randomize</span> to seed initial residents,
              then <span className="mono">Start</span> to run the simulation.
            </p>
          )}
        </>
      )}
    </aside>
  )
}
