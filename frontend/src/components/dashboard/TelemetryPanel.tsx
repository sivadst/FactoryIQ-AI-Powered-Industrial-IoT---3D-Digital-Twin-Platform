'use client'

import { useFactoryStore } from '@/lib/store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip 
} from 'recharts'
import { Activity, ShieldCheck, AlertTriangle, Gauge, Thermometer, ArrowRight } from 'lucide-react'

export function TelemetryPanel() {
  const selectedId = useFactoryStore((state) => state.selectedMachineId)
  const setSelectedId = useFactoryStore((state) => state.setSelectedMachineId)
  const machines = useFactoryStore((state) => state.machines)
  const telemetryMap = useFactoryStore((state) => state.telemetry)
  const setActiveTab = useFactoryStore((state) => state.setActiveTab)

  const activeId = selectedId || (machines.length > 0 ? machines[0].id : null)
  const machine = machines.find((m) => m.id === activeId)
  const data = activeId ? telemetryMap[activeId] || [] : []
  const latest = data.length > 0 ? data[data.length - 1] : null

  if (!machine) {
    return (
      <Card className="w-full h-full bg-slate-900 border-slate-800 text-slate-400 flex items-center justify-center p-6 text-center text-xs">
        <p>Select any machine on the 3D factory floor to inspect real-time AI telemetry.</p>
      </Card>
    )
  }

  return (
    <Card className="w-full h-full bg-slate-900 border-slate-800 text-slate-100 flex flex-col justify-between overflow-hidden shadow-xl">
      <CardHeader className="py-2.5 px-3.5 border-b border-slate-800 flex flex-row items-center justify-between">
        <div>
          <div className="text-xs font-bold text-white font-mono flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            {machine.name} <span className="text-slate-400 font-sans font-normal">({machine.type})</span>
          </div>
          <div className="text-[10px] text-slate-500">{machine.zone}</div>
        </div>
        <Badge className={`text-[10px] font-mono ${
          machine.status === 'Running' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-800' :
          machine.status === 'Fault' ? 'bg-red-500/20 text-red-400 border-red-800' :
          'bg-amber-500/20 text-amber-400 border-amber-800'
        }`}>
          {machine.status} ({machine.health_score}%)
        </Badge>
      </CardHeader>

      <CardContent className="p-3 text-xs space-y-3 flex-1 flex flex-col justify-between overflow-y-auto">
        {/* Real-time Diagnostics Grid */}
        <div className="grid grid-cols-2 gap-2">
          {/* Anomaly Score */}
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-400 flex items-center gap-1">
              <Activity className="w-3 h-3 text-cyan-400" /> Anomaly
            </div>
            <div className="text-sm font-bold font-mono text-cyan-300 mt-0.5">
              {latest?.anomaly_score !== undefined ? `${(latest.anomaly_score * 100).toFixed(1)}%` : '--'}
            </div>
            <div className="text-[9px] text-cyan-400">{latest?.anomaly_status || 'NORMAL'}</div>
          </div>

          {/* RUL Prediction */}
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-400 flex items-center gap-1">
              <Gauge className="w-3 h-3 text-emerald-400" /> Estimated RUL
            </div>
            <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
              {latest?.rul !== undefined ? `${latest.rul.toFixed(0)} hrs` : '--'}
            </div>
            <div className="text-[9px] text-slate-500">[{latest?.rul_ci_lower?.toFixed(0) || '--'} - {latest?.rul_ci_upper?.toFixed(0) || '--'}h]</div>
          </div>

          {/* Predicted Failure */}
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800 col-span-2">
            <div className="text-[10px] text-slate-400 flex items-center justify-between">
              <span className="flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-amber-400" /> Fault Classification</span>
              <span className="text-[10px] text-amber-400 font-mono">Conf: {latest?.confidence ? `${(latest.confidence * 100).toFixed(0)}%` : '--'}</span>
            </div>
            <div className="text-xs font-bold font-mono text-amber-300 mt-0.5 truncate">
              {latest?.predicted_failure?.replace('_', ' ') || 'NONE (HEALTHY)'}
            </div>
          </div>
        </div>

        {/* Live Sparkline Charts */}
        <div className="space-y-2">
          {/* Vibration Waveform */}
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
            <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
              <span>Vibration RMS (mm/s)</span>
              <span className="text-cyan-300 font-mono">{latest?.vibration_x?.toFixed(2) ?? '--'} mm/s</span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                  <YAxis hide domain={['auto', 'auto']} />
                  <Line type="monotone" dataKey="vibration_x" stroke="#38bdf8" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Temperature Waveform */}
          <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
            <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
              <span>Spindle Temp (°C)</span>
              <span className="text-rose-300 font-mono">{latest?.temperature_spindle?.toFixed(1) ?? '--'}°C</span>
            </div>
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                  <YAxis hide domain={['auto', 'auto']} />
                  <Line type="monotone" dataKey="temperature_spindle" stroke="#f43f5e" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Deep Dive Action Link */}
        <button
          onClick={() => {
            setSelectedId(machine.id)
            setActiveTab('MACHINE_DETAIL')
          }}
          className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 text-xs font-semibold border border-blue-700/60 transition-all"
        >
          <span>Open Full Machine Deep-Dive & XAI</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </CardContent>
    </Card>
  )
}
