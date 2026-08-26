'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Plane, Html } from '@react-three/drei'
import { useFactoryStore, Machine, HeatmapMode } from '@/lib/store'
import { useMemo, useRef, useState } from 'react'
import * as THREE from 'three'

// Helper to determine machine color based on heatmap mode
function getMachineHeatmapColor(machine: Machine, telemetryPoint: any, mode: HeatmapMode): string {
  if (mode === 'HEALTH') {
    const score = machine.health_score ?? 95.0
    if (score > 85) return '#10b981' // emerald
    if (score > 70) return '#eab308' // yellow
    if (score > 50) return '#f97316' // orange
    return '#ef4444' // red
  }
  
  if (mode === 'RISK') {
    const risk = telemetryPoint?.risk_score ?? 10.0
    if (risk < 25) return '#10b981' // low
    if (risk < 55) return '#eab308' // medium
    if (risk < 80) return '#f97316' // high
    return '#ef4444' // critical
  }

  if (mode === 'TEMP') {
    const temp = telemetryPoint?.temperature_spindle ?? 48.0
    if (temp < 55) return '#3b82f6' // cool blue
    if (temp < 70) return '#eab308' // warm amber
    return '#ef4444' // hot red
  }

  if (mode === 'VIBRATION') {
    const vib = telemetryPoint?.vibration_x ?? 0.35
    if (vib < 0.6) return '#10b981'
    if (vib < 1.2) return '#f59e0b'
    return '#ef4444'
  }

  // Default: STATUS
  switch (machine.status) {
    case 'Running':
      return machine.degradation_state === 'CRITICAL' ? '#ef4444' :
             machine.degradation_state === 'ANOMALOUS' ? '#f97316' : '#10b981'
    case 'Idle': return '#eab308'
    case 'Fault': return '#ef4444'
    case 'Maintenance': return '#3b82f6'
    default: return '#64748b'
  }
}

// 1. CNC Lathe 3D Geometry
function CNCLatheMesh({ color, isRunning }: { color: string; isRunning: boolean }) {
  const spindleRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (isRunning && spindleRef.current) {
      spindleRef.current.rotation.x += delta * 12
    }
  })

  return (
    <group>
      {/* Base Cabinet */}
      <mesh position={[0, 0.75, 0]} castShadow receiveShadow>
        <boxGeometry args={[4.2, 1.5, 2.4]} />
        <meshStandardMaterial color="#1e293b" metalness={0.8} roughness={0.3} />
      </mesh>
      {/* Enclosure Hood with Color Tint */}
      <mesh position={[0, 2.1, 0]} castShadow>
        <boxGeometry args={[4.0, 1.2, 2.2]} />
        <meshStandardMaterial color={color} metalness={0.6} roughness={0.2} />
      </mesh>
      {/* Spindle Workpiece (Rotating) */}
      <mesh ref={spindleRef} position={[-0.8, 1.8, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.3, 0.3, 1.8, 16]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.1} />
      </mesh>
      {/* Safety Glass Window */}
      <mesh position={[0, 2.1, 1.11]}>
        <planeGeometry args={[2.5, 0.8]} />
        <meshPhysicalMaterial color="#38bdf8" transmission={0.7} opacity={0.8} transparent roughness={0.1} />
      </mesh>
    </group>
  )
}

// 2. 5-Axis Milling Center 3D Geometry
function FiveAxisMillMesh({ color, isRunning }: { color: string; isRunning: boolean }) {
  const toolRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (isRunning && toolRef.current) {
      toolRef.current.rotation.y += delta * 20
    }
  })

  return (
    <group>
      {/* Main Casting Bed */}
      <mesh position={[0, 1.0, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.6, 2.0, 3.6]} />
        <meshStandardMaterial color="#0f172a" metalness={0.85} roughness={0.35} />
      </mesh>
      {/* Column & Enclosure */}
      <mesh position={[0, 2.6, 0]} castShadow>
        <boxGeometry args={[3.2, 1.8, 3.2]} />
        <meshStandardMaterial color={color} metalness={0.7} roughness={0.2} />
      </mesh>
      {/* Vertical Spindle Tool Head */}
      <mesh ref={toolRef} position={[0, 2.4, 0.4]}>
        <cylinderGeometry args={[0.15, 0.15, 0.8, 16]} />
        <meshStandardMaterial color="#e2e8f0" metalness={0.95} roughness={0.05} />
      </mesh>
      {/* Acrylic Front Window */}
      <mesh position={[0, 2.6, 1.61]}>
        <planeGeometry args={[2.2, 1.4]} />
        <meshPhysicalMaterial color="#38bdf8" transmission={0.65} opacity={0.85} transparent roughness={0.1} />
      </mesh>
    </group>
  )
}

// 3. Surface Grinder 3D Geometry
function SurfaceGrinderMesh({ color, isRunning }: { color: string; isRunning: boolean }) {
  const wheelRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    if (isRunning && wheelRef.current) {
      wheelRef.current.rotation.z += delta * 25
    }
  })

  return (
    <group>
      {/* Bed Base */}
      <mesh position={[0, 0.8, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.8, 1.6, 2.2]} />
        <meshStandardMaterial color="#1e293b" metalness={0.75} roughness={0.3} />
      </mesh>
      {/* Column Housing */}
      <mesh position={[1.0, 2.2, 0]} castShadow>
        <boxGeometry args={[1.4, 1.8, 1.8]} />
        <meshStandardMaterial color={color} metalness={0.65} roughness={0.25} />
      </mesh>
      {/* Grinding Wheel */}
      <mesh ref={wheelRef} position={[0.1, 2.0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.55, 0.55, 0.25, 24]} />
        <meshStandardMaterial color="#cbd5e1" metalness={0.4} roughness={0.8} />
      </mesh>
    </group>
  )
}

// 4. CMM Inspection Station 3D Geometry
function CMMMesh({ color }: { color: string }) {
  return (
    <group>
      {/* Black Granite Surface Table */}
      <mesh position={[0, 0.7, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.2, 1.4, 2.8]} />
        <meshStandardMaterial color="#020617" roughness={0.1} metalness={0.3} />
      </mesh>
      {/* Bridge Gantry Columns */}
      <mesh position={[-1.2, 2.3, 0]} castShadow>
        <boxGeometry args={[0.3, 1.8, 0.6]} />
        <meshStandardMaterial color={color} metalness={0.7} roughness={0.2} />
      </mesh>
      <mesh position={[1.2, 2.3, 0]} castShadow>
        <boxGeometry args={[0.3, 1.8, 0.6]} />
        <meshStandardMaterial color={color} metalness={0.7} roughness={0.2} />
      </mesh>
      {/* Top Crossbeam */}
      <mesh position={[0, 3.2, 0]} castShadow>
        <boxGeometry args={[2.7, 0.35, 0.6]} />
        <meshStandardMaterial color={color} metalness={0.7} roughness={0.2} />
      </mesh>
      {/* Vertical Probe Ram with Ruby Tip */}
      <mesh position={[0, 2.2, 0]}>
        <cylinderGeometry args={[0.06, 0.06, 1.4, 16]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.1} />
      </mesh>
      <mesh position={[0, 1.45, 0]}>
        <sphereGeometry args={[0.12, 16, 16]} />
        <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.8} />
      </mesh>
    </group>
  )
}

// Status Light Tower Beacon
function StatusLightBeacon({ status, color }: { status: string; color: string }) {
  const beaconRef = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    if (status === 'Fault' && beaconRef.current) {
      const pulse = (Math.sin(clock.getElapsedTime() * 8) + 1) / 2
      beaconRef.current.scale.set(1 + pulse * 0.3, 1 + pulse * 0.3, 1 + pulse * 0.3)
    }
  })

  return (
    <group position={[1.4, 3.2, -0.8]}>
      {/* Pole */}
      <mesh position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.04, 0.04, 0.8, 8]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      {/* Glowing Lamp */}
      <mesh ref={beaconRef} position={[0, 0.9, 0]}>
        <cylinderGeometry args={[0.12, 0.12, 0.3, 16]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color} 
          emissiveIntensity={status === 'Fault' ? 2.5 : 1.2} 
        />
      </mesh>
      <pointLight position={[0, 0.9, 0]} color={color} intensity={status === 'Fault' ? 3.0 : 1.0} distance={5} />
    </group>
  )
}

function MachineNode({ 
  machine, 
  telemetryPoint, 
  isSelected, 
  heatmapMode, 
  onClick 
}: { 
  machine: Machine
  telemetryPoint: any
  isSelected: boolean
  heatmapMode: HeatmapMode
  onClick: () => void 
}) {
  const [hovered, setHovered] = useState(false)
  const color = getMachineHeatmapColor(machine, telemetryPoint, heatmapMode)
  const isRunning = machine.status === 'Running'

  return (
    <group 
      position={[machine.pos_x, machine.pos_y, machine.pos_z]} 
      onClick={(e) => { e.stopPropagation(); onClick() }}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true) }}
      onPointerOut={() => setHovered(false)}
    >
      {/* 3D Geometry Based on Machine Type */}
      {machine.type === 'CNC Lathe' ? (
        <CNCLatheMesh color={color} isRunning={isRunning} />
      ) : machine.type === '5-Axis Mill' ? (
        <FiveAxisMillMesh color={color} isRunning={isRunning} />
      ) : machine.type === 'Surface Grinder' ? (
        <SurfaceGrinderMesh color={color} isRunning={isRunning} />
      ) : (
        <CMMMesh color={color} />
      )}

      {/* Industrial Status Light Tower */}
      <StatusLightBeacon status={machine.status} color={color} />

      {/* Selection Hologram Ring */}
      {isSelected && (
        <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[2.5, 2.8, 32]} />
          <meshBasicMaterial color="#38bdf8" side={THREE.DoubleSide} transparent opacity={0.9} />
        </mesh>
      )}

      {/* Machine Label Floating Above */}
      <Text 
        position={[0, 4.2, 0]} 
        fontSize={0.45} 
        color="#ffffff" 
        anchorX="center" 
        anchorY="middle"
        outlineWidth={0.04}
        outlineColor="#020617"
      >
        {machine.name}
      </Text>

      {/* Status Subtitle */}
      <Text 
        position={[0, 3.8, 0]} 
        fontSize={0.28} 
        color={color} 
        anchorX="center" 
        anchorY="middle"
      >
        {machine.status.toUpperCase()} ({machine.health_score}%)
      </Text>

      {/* Interactive Tooltip on Hover */}
      {hovered && (
        <Html position={[0, 4.8, 0]} center distanceFactor={25}>
          <div className="bg-slate-900/95 border border-cyan-500/50 backdrop-blur-md px-3 py-2 rounded-lg text-xs text-slate-200 shadow-2xl pointer-events-none min-w-[180px] z-50">
            <div className="font-bold text-white flex justify-between items-center mb-1 border-b border-slate-700 pb-1">
              <span>{machine.name}</span>
              <span className="text-cyan-400 font-mono">{machine.type}</span>
            </div>
            <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
              <div>Zone: <span className="text-slate-300 font-semibold">{machine.zone.split('—')[0]}</span></div>
              <div>Health: <span className="text-emerald-400 font-semibold">{machine.health_score}%</span></div>
              <div>Vib RMS: <span className="font-mono text-cyan-300">{telemetryPoint?.vibration_x?.toFixed(2) ?? '--'} mm/s</span></div>
              <div>Spindle: <span className="font-mono text-rose-300">{telemetryPoint?.temperature_spindle?.toFixed(1) ?? '--'}°C</span></div>
              <div>Risk: <span className="font-mono text-amber-400">{telemetryPoint?.risk_score ?? '--'}</span></div>
              <div>RUL: <span className="font-mono text-emerald-400">{telemetryPoint?.rul ? Math.round(telemetryPoint.rul) : '--'}h</span></div>
            </div>
          </div>
        </Html>
      )}
    </group>
  )
}

export function FactoryFloor() {
  const machines = useFactoryStore((state) => state.machines)
  const telemetryMap = useFactoryStore((state) => state.telemetry)
  const selectedId = useFactoryStore((state) => state.selectedMachineId)
  const setSelectedId = useFactoryStore((state) => state.setSelectedMachineId)
  const heatmapMode = useFactoryStore((state) => state.heatmapMode)
  const setHeatmapMode = useFactoryStore((state) => state.setHeatmapMode)
  const zoneFilter = useFactoryStore((state) => state.zoneFilter)
  const statusFilter = useFactoryStore((state) => state.statusFilter)

  // Filter machines based on selected filters
  const filteredMachines = useMemo(() => {
    return machines.filter((m) => {
      if (zoneFilter !== 'ALL' && m.zone !== zoneFilter) return false
      if (statusFilter !== 'ALL' && m.status !== statusFilter) return false
      return true
    })
  }, [machines, zoneFilter, statusFilter])

  return (
    <div className="w-full h-full bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800 relative">
      {/* 3D Canvas Viewport */}
      <Canvas shadows camera={{ position: [0, 55, 65], fov: 45 }}>
        <color attach="background" args={['#020617']} />
        
        {/* Dynamic Studio & Industrial Lighting */}
        <ambientLight intensity={0.65} />
        <directionalLight 
          position={[40, 60, 40]} 
          intensity={1.8} 
          castShadow 
          shadow-mapSize-width={2048} 
          shadow-mapSize-height={2048} 
        />
        <directionalLight position={[-40, 40, -40]} intensity={0.7} color="#38bdf8" />
        
        {/* Industrial Concrete Factory Floor */}
        <Plane args={[130, 130]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow onClick={() => setSelectedId(null)}>
          <meshStandardMaterial color="#090d16" roughness={0.8} metalness={0.25} />
        </Plane>

        {/* Safety Grid Markings */}
        <gridHelper args={[130, 26, '#334155', '#1e293b']} position={[0, 0.02, 0]} />

        {/* 3D Zone Title Plates on Shop Floor */}
        <Text position={[-25, 0.05, -42]} rotation={[-Math.PI / 2, 0, 0]} fontSize={2.2} color="#0284c7" fillOpacity={0.6}>
          CELL A — CNC TURNING
        </Text>
        <Text position={[25, 0.05, -42]} rotation={[-Math.PI / 2, 0, 0]} fontSize={2.2} color="#0284c7" fillOpacity={0.6}>
          CELL B — 5-AXIS MILLING
        </Text>
        <Text position={[-25, 0.05, 12]} rotation={[-Math.PI / 2, 0, 0]} fontSize={2.2} color="#0284c7" fillOpacity={0.6}>
          CELL C — PRECISION GRINDING
        </Text>
        <Text position={[25, 0.05, 12]} rotation={[-Math.PI / 2, 0, 0]} fontSize={2.2} color="#0284c7" fillOpacity={0.6}>
          CELL D — QA & CMM INSPECTION
        </Text>

        {/* Render Machines */}
        {filteredMachines.map((m) => {
          const tHistory = telemetryMap[m.id]
          const latestPoint = tHistory && tHistory.length > 0 ? tHistory[tHistory.length - 1] : null

          return (
            <MachineNode
              key={m.id}
              machine={m}
              telemetryPoint={latestPoint}
              isSelected={m.id === selectedId}
              heatmapMode={heatmapMode}
              onClick={() => setSelectedId(m.id)}
            />
          )
        })}

        <OrbitControls 
          maxPolarAngle={Math.PI / 2 - 0.05} 
          minDistance={10} 
          maxDistance={140} 
          enableDamping
          dampingFactor={0.05}
        />
      </Canvas>

      {/* Floating Heatmap & Camera Mode Overlay */}
      <div className="absolute top-3 right-3 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3 py-2 rounded-lg text-xs flex items-center gap-2 shadow-xl">
        <span className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">Heatmap:</span>
        {(['STATUS', 'HEALTH', 'RISK', 'TEMP', 'VIBRATION'] as HeatmapMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setHeatmapMode(mode)}
            className={`px-2 py-1 rounded transition-all font-medium text-[11px] ${
              heatmapMode === mode
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {mode}
          </button>
        ))}
      </div>

      {/* Legend Overlay */}
      <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 px-3 py-2 rounded-lg text-[11px] text-slate-300 flex items-center gap-4 shadow-xl">
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm" /> Running / Healthy</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm" /> Idle / Warning</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-sm animate-pulse" /> Critical / Fault</div>
        <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm" /> Maintenance</div>
      </div>
    </div>
  )
}
