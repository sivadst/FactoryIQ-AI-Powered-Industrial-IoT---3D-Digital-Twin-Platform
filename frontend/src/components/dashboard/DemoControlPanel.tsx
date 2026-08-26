'use client'

import { useState } from 'react'
import { useFactoryStore } from '@/lib/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Sliders, Flame, RefreshCw, CheckCircle2, Play, AlertTriangle, Cpu, Activity } from 'lucide-react'

export function DemoControlPanel() {
  const machines = useFactoryStore((state) => state.machines)
  const setSelectedMachineId = useFactoryStore((state) => state.setSelectedMachineId)
  const setActiveTab = useFactoryStore((state) => state.setActiveTab)
  
  const [selectedMachineId, setLocalSelectedMachineId] = useState<number>(machines[0]?.id || 1)
  const [selectedMode, setSelectedMode] = useState<string>('BEARING_FAILURE')
  const [severity, setSeverity] = useState<number>(85)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const failureScenarios = [
    {
      id: 'BEARING_FAILURE',
      name: 'Bearing Race Spalling & Fatigue',
      desc: 'Spikes vibration RMS (0.35 -> 2.8 mm/s), bearing temperature (+35°C), acoustic noise.',
      targetAsset: 'CNC Lathe / Mill'
    },
    {
      id: 'MOTOR_OVERHEATING',
      name: 'Motor Stator Thermal Overload',
      desc: 'Elevates stator temperatures (+30°C) and draws heavy 3-phase current (+16A).',
      targetAsset: '5-Axis Milling Spindle'
    },
    {
      id: 'TOOL_WEAR',
      name: 'Cutting Flank Tool Degradation',
      desc: 'Increases dynamic cutting force (185N -> 450N), high-frequency Z-chatter, scrap rate spikes.',
      targetAsset: 'CNC Turning / Milling'
    },
    {
      id: 'LUBRICATION_FAILURE',
      name: 'Hydrodynamic Oil Starvation',
      desc: 'Rapid spindle thermal surge (+45°C), torque resistance drag, and friction spike.',
      targetAsset: 'All Machine Assets'
    },
    {
      id: 'SPINDLE_WEAR',
      name: 'Spindle Journal Runout & Eccentricity',
      desc: 'Causes radial rotational vibration unbalance and RPM speed hunting.',
      targetAsset: 'High-Speed Spindle'
    },
    {
      id: 'ELECTRICAL_FAULT',
      name: 'VFD 3-Phase Current Imbalance',
      desc: 'Diverges phase currents L1, L2, L3, creating severe phase harmonics.',
      targetAsset: 'Main Drive Inverter'
    },
    {
      id: 'COOLANT_FAILURE',
      name: 'Coolant Pump Pressure Collapse',
      desc: 'Drops delivery pressure (50 -> 2 psi) and surges coolant/workpiece temperatures.',
      targetAsset: 'Through-Spindle Pump'
    },
    {
      id: 'VIBRATION_ANOMALY',
      name: 'Bed Anchor Bolt Resonance',
      desc: 'Broadband mechanical vibration resonance across primary axis.',
      targetAsset: 'Cast Iron Base Mount'
    }
  ]

  const handleInject = async (modeId: string) => {
    setIsLoading(true)
    setStatusMessage(null)
    try {
      const res = await fetch(`http://localhost:8000/api/v1/machines/${selectedMachineId}/inject-failure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ failure_mode: modeId, severity: severity / 100 })
      })
      if (res.ok) {
        setStatusMessage(`Injected ${modeId.replace('_', ' ')} on Machine #${selectedMachineId} at ${severity}% severity. AI anomaly detection and work order pipeline triggered.`)
        setSelectedMachineId(selectedMachineId)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecoverAll = async () => {
    setIsLoading(true)
    try {
      for (const m of machines) {
        if (m.status === 'Fault' || m.degradation_state !== 'HEALTHY') {
          await fetch(`http://localhost:8000/api/v1/machines/${m.id}/recover`, { method: 'POST' })
        }
      }
      setStatusMessage('All 24 machines across all factory cells reset to healthy baseline.')
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-8">
      {/* Header Bar */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sliders className="w-5 h-5 text-red-400" />
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">Interactive Failure Injection & Live Demo Control</h2>
            <p className="text-xs text-slate-400">Trigger real-time physics-grounded degradation scenarios to test the closed-loop AI system</p>
          </div>
        </div>

        <button
          onClick={handleRecoverAll}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset All Assets to Healthy
        </button>
      </div>

      {statusMessage && (
        <div className="bg-blue-950/70 border border-blue-500/60 text-blue-200 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            <span>{statusMessage}</span>
          </div>
          <button
            onClick={() => setActiveTab('MACHINE_DETAIL')}
            className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[11px] font-semibold"
          >
            View Machine Detail →
          </button>
        </div>
      )}

      {/* Target Asset & Severity Controls */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold uppercase">Target Asset:</label>
          <select
            value={selectedMachineId}
            onChange={(e) => setLocalSelectedMachineId(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-2 font-mono outline-none"
          >
            {machines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} — {m.type} ({m.zone.split('—')[0]})
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-semibold uppercase">Fault Severity: <span className="text-red-400 font-mono">{severity}%</span></label>
          <input
            type="range"
            min={50}
            max={100}
            value={severity}
            onChange={(e) => setSeverity(Number(e.target.value))}
            className="w-40 accent-red-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {failureScenarios.map((sc) => (
          <Card key={sc.id} className="bg-slate-900 border-slate-800 text-slate-100 flex flex-col justify-between hover:border-slate-700 transition-all">
            <CardHeader className="p-3.5 pb-2 border-b border-slate-800 flex flex-row items-center justify-between">
              <CardTitle className="text-xs font-bold text-white flex items-center gap-1.5">
                <Flame className="w-3.5 h-3.5 text-red-400" />
                {sc.name}
              </CardTitle>
            </CardHeader>

            <CardContent className="p-3.5 text-xs space-y-3 flex-1 flex flex-col justify-between">
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {sc.desc}
              </p>

              <div>
                <div className="text-[10px] text-slate-500 mb-2">Target Subsystem: <span className="text-slate-300 font-mono">{sc.targetAsset}</span></div>
                <button
                  onClick={() => handleInject(sc.id)}
                  disabled={isLoading}
                  className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/40 text-red-300 text-xs font-semibold border border-red-700/60 transition-all"
                >
                  <Play className="w-3 h-3 text-red-400" />
                  Inject into Machine
                </button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
