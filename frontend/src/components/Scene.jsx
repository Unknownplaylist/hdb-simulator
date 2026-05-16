import { Canvas } from '@react-three/fiber'
import { MapControls } from '@react-three/drei'
import { Buildings } from './Buildings'
import { SingaporeBoundary } from './SingaporeBoundary'
import { useStore } from '../store/useStore'

export function Scene() {
  return (
    <Canvas
      camera={{ position: [0, 280, 450], fov: 45, near: 1, far: 6000 }}
      gl={{ antialias: true, alpha: false }}
      onPointerMissed={() => useStore.getState().selectBuilding(null)}
    >
      <color attach="background" args={['#0a0e14']} />
      <fog attach="fog" args={['#0a0e14', 700, 2200]} />

      <ambientLight intensity={0.45} />
      <directionalLight position={[300, 500, 200]} intensity={0.9} color="#cfe8ff" />
      <directionalLight position={[-200, 350, -300]} intensity={0.3} color="#7CFFB2" />

      <MapControls
        enableRotate
        enableDamping
        dampingFactor={0.08}
        maxPolarAngle={Math.PI / 2.2}
        minDistance={20}
        maxDistance={1500}
      />

      <SingaporeBoundary />
      <Buildings />

      <gridHelper args={[1200, 60, '#1d242e', '#11161d']} position={[0, 0.001, 0]} />
    </Canvas>
  )
}
