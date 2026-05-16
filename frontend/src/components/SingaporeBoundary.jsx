import { useEffect, useState, useMemo } from 'react'
import * as THREE from 'three'
import { api } from '../api/client'
import { projectLonLat } from './geo'

export function SingaporeBoundary() {
  const [geojson, setGeojson] = useState(null)

  useEffect(() => {
    api.getBoundary().then(setGeojson).catch(err => console.warn('No boundary:', err))
  }, [])

  const shapes = useMemo(() => {
    if (!geojson) return []
    const out = []
    for (const feature of geojson.features) {
      const geom = feature.geometry
      const polys = geom.type === 'MultiPolygon' ? geom.coordinates : [geom.coordinates]
      for (const poly of polys) {
        // Negate z: the mesh is rotated -PI/2 around X, which already flips Y -> -Z,
        // so feeding raw z would mirror N/S against the buildings.
        const outer = poly[0]
        const shape = new THREE.Shape()
        outer.forEach(([lon, lat], idx) => {
          const [x, z] = projectLonLat(lon, lat)
          if (idx === 0) shape.moveTo(x, -z)
          else shape.lineTo(x, -z)
        })
        for (let h = 1; h < poly.length; h++) {
          const hole = new THREE.Path()
          poly[h].forEach(([lon, lat], idx) => {
            const [x, z] = projectLonLat(lon, lat)
            if (idx === 0) hole.moveTo(x, -z)
            else hole.lineTo(x, -z)
          })
          shape.holes.push(hole)
        }
        out.push(shape)
      }
    }
    return out
  }, [geojson])

  if (shapes.length === 0) return null

  return (
    <group>
      {shapes.map((shape, i) => (
        <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
          <shapeGeometry args={[shape]} />
          <meshStandardMaterial
            color="#2f9e44"
            emissive="#1b6b2c"
            emissiveIntensity={0.3}
            roughness={0.9}
            metalness={0}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  )
}
