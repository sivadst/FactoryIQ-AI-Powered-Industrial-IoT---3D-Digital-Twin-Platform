'use client'

import { useState } from 'react'
import { useFactoryStore } from '@/lib/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend 
} from 'recharts'
import { 
  Activity, AlertTriangle, ShieldCheck, Thermometer, Zap, Gauge, 
  HelpCircle, Wrench, CheckCircle2, RefreshCw, Flame, Cpu 
} from 'lucide-react'

export function MachineDetailView() {
  const machines = useFactoryStore((state) => state.machines)
  const telemetryMap = useFactoryStore((state) => state.telemetry)
  const selectedId = useFactoryStore((state) => state.selectedMachineId)
  const setSelectedId = useFactoryStore((state) => state.setSelectedMachineId)
  const setWorkOrders = useFactoryStore((state) => state.setWorkOrders)
  
  const [selectedFailure, setSelectedFailure] = useState('BEARING_FAILURE')
  const [isActionLoading, setIsActionLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const activeMachineId = selectedId || (machines.length > 0 ? machines[0].id : null)
  const machine = machines.find((m) => m.id === activeMachineId)
  const history = activeMachineId ? telemetryMap[activeMachineId] || [] : []
  const latest = history.length > 0 ? history[history.length - 1] : null

  const handleInjectFailure = async () => {
    if (!machine) return
    setIsActionLoading(true)
    setActionMessage(null)
    try {
      const res = await fetch(`http://localhost:8000/api/v1/machines/${machine.id}/inject-failure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ failure_mode: selectedFailure, severity: 0.85 })
      })
      if (res.ok) {
        setActionMessage(`Successfully injected ${selectedFailure.replace('_', ' ')}! Observe real-time anomaly escalation.`)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleManualRecovery = async () => {
    if (!machine) return
    setIsActionLoading(true)
    setActionMessage(null)
    try {
      const res = await fetch(`http://localhost:8000/api/v1/machines/${machine.id}/recover`, {
        method: 'POST'
      })
      if (res.ok) {
        setActionMessage(`Machine ${machine.name} has been recovered to optimal healthy baseline.`)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleCreateWorkOrder = async () => {
    if (!machine) return
    setIsActionLoading(true)
    try {
      const res = await fetch(`http://localhost:8000/api/v1/work-orders/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine_id: machine.id,
          title: `Intervention: ${machine.name} (${latest?.predicted_failure || 'Mechanical Inspection'})`,
          type: 'PREDICTIVE',
          priority: latest?.risk_level === 'CRITICAL' ? 'CRITICAL' : 'HIGH',
          recommended_action: latest?.rca?.recommended_action || 'Inspect spindle assembly and lubrication.',
          estimated_duration_hours: 2.5
        })
      })
      if (res.ok) {
        setActionMessage(`Work order created for ${machine.name}.`)
        // Refresh work orders
        const woRes = await fetch('http://localhost:8000/api/v1/work-orders/')
        if (woRes.ok) setWorkOrders(await woRes.json())
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsActionLoading(false)
    }
  }

  if (!machine) {
    return (
      <div className="p-8 text-center text-slate-500">
        No machine selected. Please choose a machine from the selector.
      </div>
    )
  }

  const riskColor = 
    latest?.risk_level === 'CRITICAL' ? 'text-red-400 bg-red-950/40 border-red-800' :
    latest?.risk_level === 'HIGH' ? 'text-orange-400 bg-orange-950/40 border-orange-800' :
    latest?.risk_level === 'MEDIUM' ? 'text-amber-400 bg-amber-950/40 border-amber-800' :
    'text-emerald-400 bg-emerald-950/40 border-emerald-800'

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-8">
      {/* Machine Selector Bar */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label className="text-xs font-semibold text-slate-400 uppercase">Select Machine:</label>
          <select
            value={machine.id}
            onChange={(e) => setSelectedId(Number(e.target.value))}
            className="bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-1.5 font-mono focus:border-blue-500 outline-none"
          >
            {machines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} — {m.type} ({m.zone.split('—')[0]})
              </option>
            ))}
          </select>
        </div>

        {/* Machine Status & Degradation Badges */}
        <div className="flex items-center gap-2">
          <Badge className="bg-slate-800 text-slate-200 border-slate-700 font-mono">
            {machine.zone}
          </Badge>
          <Badge className={`font-mono ${
            machine.status === 'Running' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-800' :
            machine.status === 'Fault' ? 'bg-red-500/20 text-red-400 border-red-800' :
            'bg-amber-500/20 text-amber-400 border-amber-800'
          }`}>
            {machine.status.toUpperCase()}
          </Badge>
          <Badge className="bg-cyan-950 text-cyan-400 border-cyan-800 font-mono">
            STATE: {machine.degradation_state}
          </Badge>
        </div>
      </div>

      {/* Action Notification Alert */}
      {actionMessage && (
        <div className="bg-blue-950/60 border border-blue-500/60 text-blue-200 px-4 py-2.5 rounded-xl text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-blue-400 hover:text-white text-xs">Dismiss</button>
        </div>
      )}

      {/* KPI Diagnosis Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Health Score */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Health Score
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {machine.health_score}%
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Physical condition index</div>
        </div>

        {/* Anomaly Score */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
            <Activity className="w-3.5 h-3.5 text-cyan-400" /> Anomaly Score
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-300">
            {latest?.anomaly_score !== undefined ? (latest.anomaly_score * 100).toFixed(1) : '--'}%
          </div>
          <div className="text-[10px] text-cyan-400 font-semibold mt-0.5">
            Status: {latest?.anomaly_status || 'NORMAL'}
          </div>
        </div>

        {/* Predicted Failure Mode */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Predicted Fault
          </div>
          <div className="text-sm font-bold font-mono text-amber-300 truncate mt-1">
            {latest?.predicted_failure?.replace('_', ' ') || 'NONE (HEALTHY)'}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Conf: {latest?.confidence ? `${(latest.confidence * 100).toFixed(0)}%` : '--'}
          </div>
        </div>

        {/* Remaining Useful Life (RUL) */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
            <Gauge className="w-3.5 h-3.5 text-emerald-400" /> Estimated RUL
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {latest?.rul !== undefined ? `${latest.rul.toFixed(1)}h` : '--'}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            90% CI: [{latest?.rul_ci_lower?.toFixed(0) || '--'} - {latest?.rul_ci_upper?.toFixed(0) || '--'}h]
          </div>
        </div>

        {/* Industrial Risk Score */}
        <div className={`p-3 rounded-xl border ${riskColor}`}>
          <div className="text-[11px] flex items-center gap-1.5 mb-1">
            <Flame className="w-3.5 h-3.5" /> Risk Score
          </div>
          <div className="text-2xl font-bold font-mono">
            {latest?.risk_score !== undefined ? latest.risk_score : '--'} / 100
          </div>
          <div className="text-[10px] font-bold mt-0.5 uppercase tracking-wider">
            {latest?.risk_level || 'LOW'} RISK
          </div>
        </div>

        {/* Operating Hours */}
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mb-1">
            <Cpu className="w-3.5 h-3.5 text-slate-400" /> Operating Age
          </div>
          <div className="text-2xl font-bold font-mono text-slate-200">
            {machine.operating_hours ? Math.round(machine.operating_hours) : 1200}h
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Cycle: {machine.ideal_cycle_time_sec}s</div>
        </div>
      </div>

      {/* Multi-Channel Waveform Time-Series Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 1. Vibration Waveforms (X, Y, Z) */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" /> 3-Axis Vibration Analysis (mm/s RMS)
            </CardTitle>
            <span className="text-[11px] text-slate-500 font-mono">Live 1Hz Stream</span>
          </CardHeader>
          <CardContent className="p-3 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                <Line type="monotone" dataKey="vibration_x" name="Vib X" stroke="#38bdf8" dot={false} strokeWidth={1.8} isAnimationActive={false} />
                <Line type="monotone" dataKey="vibration_y" name="Vib Y" stroke="#818cf8" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="monotone" dataKey="vibration_z" name="Vib Z" stroke="#a78bfa" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 2. Spindle & Coolant Temperatures */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-rose-400" /> Thermal Dynamics (°C)
            </CardTitle>
            <span className="text-[11px] text-slate-500 font-mono">Spindle vs Coolant</span>
          </CardHeader>
          <CardContent className="p-3 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                <Line type="monotone" dataKey="temperature_spindle" name="Spindle Temp" stroke="#f43f5e" dot={false} strokeWidth={2.0} isAnimationActive={false} />
                <Line type="monotone" dataKey="temperature_coolant" name="Coolant Temp" stroke="#06b6d4" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 3. 3-Phase Motor Current */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> 3-Phase Electrical Current Draw (Amperes)
            </CardTitle>
            <span className="text-[11px] text-slate-500 font-mono">L1 / L2 / L3 Balance</span>
          </CardHeader>
          <CardContent className="p-3 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" hide />
                <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                <Line type="monotone" dataKey="current_l1" name="Phase L1" stroke="#f59e0b" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="monotone" dataKey="current_l2" name="Phase L2" stroke="#fbbf24" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                <Line type="monotone" dataKey="current_l3" name="Phase L3" stroke="#d97706" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 4. Speed & Cutting Dynamics */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Gauge className="w-4 h-4 text-emerald-400" /> Spindle Speed & Dynamic Cutting Force (N)
            </CardTitle>
            <span className="text-[11px] text-slate-500 font-mono">Mechanical Load</span>
          </CardHeader>
          <CardContent className="p-3 h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" hide />
                <YAxis yAxisId="left" stroke="#10b981" fontSize={11} domain={['auto', 'auto']} />
                <YAxis yAxisId="right" orientation="right" stroke="#f97316" fontSize={11} domain={['auto', 'auto']} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                <Line yAxisId="left" type="monotone" dataKey="rpm_spindle" name="Spindle RPM" stroke="#10b981" dot={false} strokeWidth={1.8} isAnimationActive={false} />
                <Line yAxisId="right" type="monotone" dataKey="cutting_force" name="Cutting Force (N)" stroke="#f97316" dot={false} strokeWidth={1.8} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Explainable AI (XAI) & Root Cause Analysis (RCA) Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Explainable AI (XAI) Top Drivers */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" /> Explainable AI (XAI): Top Anomaly Drivers
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {latest?.top_drivers && latest.top_drivers.length > 0 ? (
              latest.top_drivers.map((d, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 font-medium">{d.feature}</span>
                    <span className={`font-mono font-bold ${
                      d.contribution > 25 ? 'text-red-400' : d.contribution > 15 ? 'text-amber-400' : 'text-slate-400'
                    }`}>
                      +{d.contribution}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full ${
                        d.contribution > 25 ? 'bg-gradient-to-r from-amber-500 to-red-500' : 'bg-gradient-to-r from-blue-500 to-cyan-400'
                      }`}
                      style={{ width: `${Math.min(100, d.contribution * 2.5)}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs">
                Process within standard 6-sigma limits. No anomalous drivers detected.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Root Cause Analysis (RCA) & Prescriptive Action */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="py-2.5 px-4 border-b border-slate-800">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-amber-400" /> Root Cause Analysis & Prescriptive Action
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {latest?.rca ? (
              <div className="space-y-2 text-xs">
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Suspected Root Cause:</div>
                  <div className="text-rose-300 font-semibold mt-0.5">{latest.rca.root_cause}</div>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Affected Subsystem:</div>
                  <div className="text-cyan-300 font-semibold mt-0.5">{latest.rca.affected_subsystem}</div>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">Diagnostic Evidence:</div>
                  <div className="text-slate-300 mt-0.5 leading-relaxed">{latest.rca.evidence}</div>
                </div>

                <div className="bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-800/80">
                  <div className="text-emerald-400 text-[10px] uppercase font-bold">Prescriptive Maintenance Action:</div>
                  <div className="text-emerald-200 mt-0.5 leading-relaxed">{latest.rca.recommended_action}</div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs">
                All subsystems nominal. No corrective action required.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Closed-Loop Operational Controls & Fault Injection */}
      <Card className="bg-slate-900 border-slate-800 text-slate-100">
        <CardHeader className="py-2.5 px-4 border-b border-slate-800">
          <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-blue-400" /> Closed-Loop Asset Control & Testing Panel
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          {/* Work Order Trigger */}
          <button
            onClick={handleCreateWorkOrder}
            disabled={isActionLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all"
          >
            <Wrench className="w-4 h-4" /> Create Work Order
          </button>

          {/* Fault Injection Sub-form */}
          <div className="flex items-center gap-2">
            <select
              value={selectedFailure}
              onChange={(e) => setSelectedFailure(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none font-mono"
            >
              <option value="BEARING_FAILURE">Bearing Degradation (Vibration + Temp)</option>
              <option value="MOTOR_OVERHEATING">Motor Overheating (Stator Temp + Current)</option>
              <option value="TOOL_WEAR">Tool Wear (Cutting Force + Micro-chatter)</option>
              <option value="LUBRICATION_FAILURE">Lubrication Starvation (Rapid Friction Heat)</option>
              <option value="SPINDLE_WEAR">Spindle Wear (Radial Runout + Jitter)</option>
              <option value="ELECTRICAL_FAULT">Electrical Fault (3-Phase Imbalance)</option>
              <option value="COOLANT_FAILURE">Coolant Failure (Pressure Drop + Heat)</option>
              <option value="VIBRATION_ANOMALY">Vibration Resonance (Bed Bolt Loosening)</option>
            </select>
            <button
              onClick={handleInjectFailure}
              disabled={isActionLoading}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <Flame className="w-4 h-4" /> Inject Fault
            </button>
          </div>

          {/* Recovery Button */}
          <button
            onClick={handleManualRecovery}
            disabled={isActionLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Execute Repair & Recover
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
