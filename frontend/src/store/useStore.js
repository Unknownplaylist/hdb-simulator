import { create } from 'zustand'
import { api } from '../api/client'

export const useStore = create((set, get) => ({
  buildings: [],
  buildingIndex: {},

  session: null,
  snapshot: null,
  movements: [],

  availableYears: [],
  scrubYear: null,
  snapshotCache: {},
  _scrubSeq: 0,

  selectedBuildingId: null,
  selectedDetail: null,

  isPlaying: false,
  playInterval: null,

  async loadBuildings() {
    const buildings = await api.getBuildings()
    const idx = {}
    buildings.forEach((b, i) => { idx[b.id] = i })
    set({ buildings, buildingIndex: idx })
  },

  async newSession(name) {
    const session = await api.createSession(name)
    set({ session, snapshot: null, movements: [], availableYears: [2025],
          scrubYear: 2025, snapshotCache: {} })
    await get().refreshSnapshot(2025)
  },

  async loadSession(id) {
    const sessions = await api.listSessions()
    const session = sessions.find(s => s.id === id)
    const years = await api.listYears(id)
    set({ session, availableYears: years, scrubYear: session.current_year,
          snapshotCache: {} })
    await get().refreshSnapshot(session.current_year)
    get()._prefetchYears(years)
  },

  async _prefetchYears(years) {
    const { session } = get()
    if (!session) return
    for (const y of years) {
      const key = `${session.id}:${y}`
      if (get().snapshotCache[key]) continue
      try {
        const snapshot = await api.getSnapshot(session.id, y)
        const movements = y > 2025 ? await api.getMovements(session.id, y, 100) : []
        if (get().session?.id !== session.id) return
        set({ snapshotCache: { ...get().snapshotCache, [key]: { snapshot, movements } } })
      } catch (_) {}
    }
  },

  async deleteSession(id) {
    const { session, playInterval } = get()
    if (playInterval) clearInterval(playInterval)
    await api.deleteSession(id)
    if (session?.id === id) {
      set({
        session: null, snapshot: null, movements: [],
        availableYears: [], scrubYear: null,
        isPlaying: false, playInterval: null,
        selectedBuildingId: null, selectedDetail: null,
      })
    } else {
      set({ isPlaying: false, playInterval: null })
    }
  },

  async refreshSnapshot(year) {
    const { session, snapshotCache } = get()
    if (!session) return

    set({ scrubYear: year })  // keep slider thumb responsive

    const key = `${session.id}:${year}`
    const cached = snapshotCache[key]
    if (cached) {
      set({ snapshot: cached.snapshot, movements: cached.movements })
      return
    }

    const mySeq = get()._scrubSeq + 1
    set({ _scrubSeq: mySeq })
    try {
      const snapshot = await api.getSnapshot(session.id, year)
      const movements = year > 2025
        ? await api.getMovements(session.id, year, 100)
        : []
      set({ snapshotCache: { ...get().snapshotCache, [key]: { snapshot, movements } } })
      if (get()._scrubSeq !== mySeq) return  // a newer scrub raced ahead
      set({ snapshot, movements })
    } catch (e) {
      console.warn(`No snapshot for year ${year}`)
    }
  },

  async randomize() {
    const { session } = get()
    if (!session) return
    const snapshot = await api.randomize(session.id)
    set({ snapshot, movements: [], availableYears: [2025], scrubYear: 2025,
          snapshotCache: { [`${session.id}:2025`]: { snapshot, movements: [] } },
          session: { ...session, current_year: 2025, status: 'created' } })
  },

  async tick() {
    const { session } = get()
    if (!session) return
    const snapshot = await api.tick(session.id)
    const movements = await api.getMovements(session.id, snapshot.year, 100)
    // Read fresh state so pause/delete during the await doesn't get clobbered.
    set((state) => {
      if (!state.session || state.session.id !== session.id) return {}
      return {
        snapshot,
        movements,
        availableYears: [...state.availableYears, snapshot.year],
        scrubYear: snapshot.year,
        snapshotCache: {
          ...state.snapshotCache,
          [`${session.id}:${snapshot.year}`]: { snapshot, movements },
        },
        session: { ...state.session, current_year: snapshot.year },
      }
    })
  },

  play() {
    const { isPlaying, playInterval, session } = get()
    if (isPlaying) return
    const interval = setInterval(() => { get().tick() }, 1500)
    set({
      isPlaying: true,
      playInterval: interval,
      session: session ? { ...session, status: 'running' } : null,
    })
  },

  pause() {
    const { playInterval, session } = get()
    if (playInterval) clearInterval(playInterval)
    set({ isPlaying: false, playInterval: null })
    if (session) {
      api.pause(session.id).catch(() => {})
      set({ session: { ...session, status: 'paused' } })
    }
  },

  async selectBuilding(id) {
    const { session } = get()
    set({ selectedBuildingId: id })
    if (id == null) {
      set({ selectedDetail: null })
      return
    }
    const detail = await api.getBuildingDetail(id, session?.id)
    set({ selectedDetail: detail })
  },
}))
