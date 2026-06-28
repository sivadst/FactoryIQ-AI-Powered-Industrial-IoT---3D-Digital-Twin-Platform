'use client'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Box, Cylinder, Text, Plane } from '@react-three/drei'
import { useFactoryStore, Machine } from '@/lib/store'
import { useMemo } from 'react'
import * as THREE from 'three'

const getStatusColor = (status: string) => {
    switch (status) {
        case 'Running': return '#10b981' // emerald-500
        case 'Idle': return '#f59e0b' // amber-500
        case 'Fault': return '#ef4444' // red-500
        case 'Maintenance': return '#3b82f6' // blue-500
        default: return '#6b7280' // gray-500
    }
}

function MachineNode({ machine, isSelected, onClick }: { machine: Machine, isSelected: boolean, onClick: () => void }) {
    const color = getStatusColor(machine.status)
    const material = useMemo(() => new THREE.MeshStandardMaterial({ 
        color,
        emissive: color,
        emissiveIntensity: isSelected ? 0.8 : 0.2,
        roughness: 0.2,
        metalness: 0.8
    }), [color, isSelected])

    return (
        <group position={[machine.pos_x - 50, machine.pos_y + 1, machine.pos_z - 50]} onClick={(e) => { e.stopPropagation(); onClick() }}>
            {machine.type === 'Lathe' ? (
                <Cylinder args={[0.5, 0.5, 2, 16]} rotation={[0, 0, Math.PI / 2]} material={material} castShadow />
            ) : machine.type === 'Mill' ? (
                <Box args={[1.5, 2, 1.5]} material={material} castShadow />
            ) : machine.type === 'Grinder' ? (
                <Box args={[1, 1.5, 2]} material={material} castShadow />
            ) : (
                <Cylinder args={[1, 1, 1, 16]} material={material} castShadow />
            )}
            
            {/* Status Halo (Selection) */}
            {isSelected && (
                 <mesh position={[0, -0.9, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                    <ringGeometry args={[1.5, 1.7, 32]} />
                    <meshBasicMaterial color="#ffffff" side={THREE.DoubleSide} />
                 </mesh>
            )}

            {/* Label */}
            <Text position={[0, 2, 0]} fontSize={0.4} color="white" anchorX="center" anchorY="middle">
                {machine.name}
            </Text>
        </group>
    )
}

export function FactoryFloor() {
    const machines = useFactoryStore((state) => state.machines)
    const selectedId = useFactoryStore((state) => state.selectedMachineId)
    const setSelectedId = useFactoryStore((state) => state.setSelectedMachineId)

    return (
        <div className="w-full h-full bg-slate-950 rounded-xl overflow-hidden shadow-inner border border-slate-800">
            <Canvas shadows camera={{ position: [0, 60, 80], fov: 45 }}>
                <color attach="background" args={['#020617']} />
                <ambientLight intensity={0.5} />
                <directionalLight 
                    position={[50, 50, 50]} 
                    intensity={1.5} 
                    castShadow 
                    shadow-mapSize-width={2048} 
                    shadow-mapSize-height={2048} 
                />
                
                {/* Floor */}
                <Plane args={[150, 150]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow onClick={() => setSelectedId(null)}>
                    <meshStandardMaterial color="#0f172a" roughness={0.8} metalness={0.2} />
                </Plane>

                {/* Grid */}
                <gridHelper args={[150, 30, '#1e293b', '#0f172a']} position={[0, 0.01, 0]} />

                {/* Machines */}
                {machines.map(m => (
                    <MachineNode 
                        key={m.id} 
                        machine={m} 
                        isSelected={m.id === selectedId}
                        onClick={() => setSelectedId(m.id)}
                    />
                ))}

                <OrbitControls 
                    maxPolarAngle={Math.PI / 2 - 0.05} 
                    minDistance={10} 
                    maxDistance={150} 
                    enableDamping
                />
            </Canvas>
        </div>
    )
}
