import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { useStore } from '../store/useStore'
import { projectLonLat, buildingHeight, buildingSide } from './geo'

const VACANT = new THREE.Color('#1d4ed8')
const MID    = new THREE.Color('#a855f7')
const FULL   = new THREE.Color('#dc2626')
const SELECTED = new THREE.Color('#ffffff')

function rampColor(t) {
  const out = new THREE.Color()
  if (t < 0.5) {
    out.lerpColors(VACANT, MID, t * 2)
  } else {
    out.lerpColors(MID, FULL, (t - 0.5) * 2)
  }
  return out
}

export function Buildings() {
  const meshRef = useRef()
  const buildings = useStore(s => s.buildings)
  const snapshot = useStore(s => s.snapshot)
  const selectedId = useStore(s => s.selectedBuildingId)
  const selectBuilding = useStore(s => s.selectBuilding)

  const tempObj = useMemo(() => new THREE.Object3D(), [])

  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh || buildings.length === 0) return

    buildings.forEach((b, i) => {
      const [x, z] = projectLonLat(b.lon, b.lat)
      const h = Math.max(0.3, buildingHeight(b.height_m))
      const side = Math.max(0.15, buildingSide(b.footprint_area))
      tempObj.position.set(x, h / 2, z)
      tempObj.scale.set(side, h, side)
      tempObj.updateMatrix()
      mesh.setMatrixAt(i, tempObj.matrix)
    })
    mesh.instanceMatrix.needsUpdate = true
    // Required: base BoxGeometry bounding sphere only covers the origin, so without
    // recomputing the whole InstancedMesh gets frustum-culled when the camera flies in.
    mesh.computeBoundingSphere()
  }, [buildings, tempObj])

  useEffect(() => {
    const mesh = meshRef.current
    if (!mesh || buildings.length === 0) return

    const occupancy = snapshot?.state?.occupancy || {}
    const c = new THREE.Color()
    buildings.forEach((b, i) => {
      if (b.id === selectedId) {
        mesh.setColorAt(i, SELECTED)
        return
      }
      const occ = occupancy[String(b.id)]
      const totalUnits = (b.units_1r + b.units_2r + b.units_3r + b.units_4r + b.units_5r) || 1
      const occupiedUnits = occ ? (occ.u1 + occ.u2 + occ.u3 + occ.u4 + occ.u5) : 0
      const t = Math.min(1, occupiedUnits / totalUnits)
      c.copy(rampColor(t))
      mesh.setColorAt(i, c)
    })
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
  }, [buildings, snapshot, selectedId])

  if (buildings.length === 0) return null

  return (
    <instancedMesh
      ref={meshRef}
      args={[null, null, buildings.length]}
      onClick={(e) => {
        e.stopPropagation()
        const id = buildings[e.instanceId]?.id
        if (id != null) selectBuilding(id)
      }}
      onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer' }}
      onPointerOut={() => { document.body.style.cursor = 'default' }}
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshLambertMaterial toneMapped={false} />
    </instancedMesh>
  )
}
