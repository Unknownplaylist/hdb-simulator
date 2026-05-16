import { useEffect } from 'react'
import { Scene } from './components/Scene'
import { SidePanel } from './components/SidePanel'
import { ControlBar, SessionManager } from './components/Controls'
import { MovementLog } from './components/MovementLog'
import { useStore } from './store/useStore'

export default function App() {
  const loadBuildings = useStore(s => s.loadBuildings)
  const buildings = useStore(s => s.buildings)

  useEffect(() => { loadBuildings() }, [loadBuildings])

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <Scene />

      {/* Top-left title bar */}
      <header className="absolute top-4 left-1/2 -translate-x-1/2 panel px-4 py-2 rounded">
        <h1 className="mono text-sm tracking-widest text-accent">
          SG · HDB FLATS · POPULATION SIMULATOR
        </h1>
      </header>

      <SessionManager />
      <SidePanel />
      <MovementLog />
      <ControlBar />

      {/* Loading state */}
      {buildings.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="mono text-neutral-500 text-sm">
            Loading buildings… If this hangs, start the backend (see README).
          </div>
        </div>
      )}
    </div>
  )
}
