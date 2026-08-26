'use client'

import { useState } from 'react'
import { useFactoryStore, Alert } from '@/lib/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Bell, AlertTriangle, CheckCircle, ShieldAlert, Check, Clock } from 'lucide-react'

export function AlertsCenter() {
  const alerts = useFactoryStore((state) => state.alerts)
  const setAlerts = useFactoryStore((state) => state.setAlerts)
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL')
  const [filterStatus, setFilterStatus] = useState<string>('ALL')
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const handleAcknowledge = async (alertId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ acknowledged_by: 'Lead Operator' })
      })
      if (res.ok) {
        setActionMessage(`Alert #${alertId} acknowledged.`)
        // Refresh alerts
        const aRes = await fetch('http://localhost:8000/api/v1/alerts/')
        if (aRes.ok) setAlerts(await aRes.json())
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleResolve = async (alertId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/resolve`, {
        method: 'POST'
      })
      if (res.ok) {
        setActionMessage(`Alert #${alertId} resolved.`)
        // Refresh alerts
        const aRes = await fetch('http://localhost:8000/api/v1/alerts/')
        if (aRes.ok) setAlerts(await aRes.json())
      }
    } catch (err) {
      console.error(err)
    }
  }

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false
    if (filterStatus !== 'ALL' && a.status !== filterStatus) return false
    return true
  })

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-8">
      {/* Top Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Bell className="w-5 h-5 text-amber-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">Centralized Alert & Incident Center</h2>
        </div>

        <div className="flex items-center gap-3">
          {/* Severity Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-400">Severity:</span>
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                  filterSeverity === sev ? 'bg-blue-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs pl-3 border-l border-slate-800">
            <span className="text-slate-400">Status:</span>
            {['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-2 py-1 rounded text-xs font-medium transition-all ${
                  filterStatus === st ? 'bg-blue-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {actionMessage && (
        <div className="bg-blue-950/60 border border-blue-500/60 text-blue-200 px-4 py-2 rounded-lg text-xs flex justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-blue-400 hover:text-white">Dismiss</button>
        </div>
      )}

      {/* Alerts Table */}
      <Card className="bg-slate-900 border-slate-800 text-slate-100">
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 text-[11px] uppercase">
              <tr>
                <th className="p-3.5">Severity</th>
                <th className="p-3.5">Asset</th>
                <th className="p-3.5">Alarm Type</th>
                <th className="p-3.5">Description & Evidence</th>
                <th className="p-3.5">Time</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500 font-sans">
                    No matching alarms found for the selected filter.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="p-3.5">
                      <Badge className={
                        alert.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-800 animate-pulse' :
                        alert.severity === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border-amber-800' :
                        'bg-blue-500/20 text-blue-400 border-blue-800'
                      }>
                        {alert.severity}
                      </Badge>
                    </td>
                    <td className="p-3.5 font-bold text-white">
                      {alert.machine_name || `MCH-${String(alert.machine_id).padStart(3, '0')}`}
                    </td>
                    <td className="p-3.5 text-cyan-300">
                      {alert.type}
                    </td>
                    <td className="p-3.5 font-sans text-slate-300 max-w-md">
                      <div>{alert.description}</div>
                      {alert.evidence && (
                        <div className="text-[10px] text-slate-500 mt-0.5">{alert.evidence}</div>
                      )}
                    </td>
                    <td className="p-3.5 text-slate-400 font-sans text-[11px]">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        alert.status === 'ACTIVE' ? 'bg-red-950 text-red-400 border border-red-800' :
                        alert.status === 'ACKNOWLEDGED' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                        'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      }`}>
                        {alert.status}
                      </span>
                    </td>
                    <td className="p-3.5 text-right space-x-1.5 font-sans">
                      {alert.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          className="px-2 py-1 rounded bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 text-[11px] border border-amber-700/60"
                        >
                          Ack
                        </button>
                      )}
                      {alert.status !== 'RESOLVED' && (
                        <button
                          onClick={() => handleResolve(alert.id)}
                          className="px-2 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 text-[11px] border border-emerald-700/60"
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
