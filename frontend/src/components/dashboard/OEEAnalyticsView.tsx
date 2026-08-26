'use client'

import { useFactoryStore } from '@/lib/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell 
} from 'recharts'
import { BarChart3, CheckCircle, Clock, Zap, AlertTriangle, ShieldCheck } from 'lucide-react'

export function OEEAnalyticsView() {
  const plantOEE = useFactoryStore((state) => state.plantOEE)
  const machines = useFactoryStore((state) => state.machines)

  const globalOEE = plantOEE?.global_oee ?? 0.812
  const availability = plantOEE?.availability ?? 0.945
  const performance = plantOEE?.performance ?? 0.884
  const quality = plantOEE?.quality ?? 0.972

  // Transform Downtime Pareto into chart-friendly array
  const paretoData = plantOEE?.downtime_pareto 
    ? Object.entries(plantOEE.downtime_pareto).map(([name, minutes]) => ({
        reason: name.replace('_', ' '),
        minutes: Math.round(minutes * 10) / 10
      })).sort((a, b) => b.minutes - a.minutes)
    : [
        { reason: 'BREAKDOWN', minutes: 24.5 },
        { reason: 'CHANGEOVER', minutes: 18.0 },
        { reason: 'MATERIAL SHORTAGE', minutes: 12.5 },
        { reason: 'PLANNED MAINT', minutes: 8.0 },
        { reason: 'OPERATOR DELAY', minutes: 5.2 }
      ]

  const PARETO_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#8b5cf6']

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-8">
      {/* Top Header */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">Overall Equipment Effectiveness (OEE) Analytics</h2>
        </div>
        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-800 font-mono">
          WORLD-CLASS BENCHMARK: 85.0%
        </Badge>
      </div>

      {/* 4 Primary OEE Component Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Global OEE */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-400" />
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-xs font-semibold text-slate-400 flex items-center justify-between">
              <span>Plant Global OEE</span>
              <BarChart3 className="w-4 h-4 text-cyan-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-bold font-mono text-cyan-300">
              {(globalOEE * 100).toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Availability × Performance × Quality
            </div>
          </CardContent>
        </Card>

        {/* Availability */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-400" />
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-xs font-semibold text-slate-400 flex items-center justify-between">
              <span>Availability</span>
              <Clock className="w-4 h-4 text-emerald-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-bold font-mono text-emerald-400">
              {(availability * 100).toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Operating Time / Planned Shift Time
            </div>
          </CardContent>
        </Card>

        {/* Performance */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-400" />
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-xs font-semibold text-slate-400 flex items-center justify-between">
              <span>Performance</span>
              <Zap className="w-4 h-4 text-blue-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-bold font-mono text-blue-400">
              {(performance * 100).toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              (Ideal Cycle × Parts) / Operating Time
            </div>
          </CardContent>
        </Card>

        {/* Quality */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-pink-400" />
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-xs font-semibold text-slate-400 flex items-center justify-between">
              <span>Quality Rate</span>
              <CheckCircle className="w-4 h-4 text-purple-400" />
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-bold font-mono text-purple-400">
              {(quality * 100).toFixed(1)}%
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Good Parts / Total Parts Produced
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Downtime Pareto & Production Statistics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Downtime Pareto Breakdown */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="p-4 pb-2 border-b border-slate-800">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" /> Downtime Pareto Distribution (Minutes)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={paretoData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="reason" type="category" stroke="#94a3b8" fontSize={10} width={130} />
                <Tooltip contentStyle={{ backgroundColor: '#090d16', borderColor: '#334155', fontSize: '11px' }} />
                <Bar dataKey="minutes" name="Downtime (mins)" radius={[0, 4, 4, 0]}>
                  {paretoData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PARETO_COLORS[index % PARETO_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Machine OEE Leaderboard */}
        <Card className="bg-slate-900 border-slate-800 text-slate-100">
          <CardHeader className="p-4 pb-2 border-b border-slate-800">
            <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Machine Operational Efficiency Leaderboard
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0 max-h-64 overflow-y-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950/80 text-slate-400 text-[10px] uppercase border-b border-slate-800 sticky top-0">
                <tr>
                  <th className="p-2.5">Asset</th>
                  <th className="p-2.5">Zone</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5 font-mono">Health</th>
                  <th className="p-2.5 text-right font-mono">Cycle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {machines.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-2.5 font-bold text-white">{m.name}</td>
                    <td className="p-2.5 text-slate-400 font-sans">{m.zone.split('—')[0]}</td>
                    <td className="p-2.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        m.status === 'Running' ? 'text-emerald-400 bg-emerald-950' :
                        m.status === 'Fault' ? 'text-red-400 bg-red-950' : 'text-amber-400 bg-amber-950'
                      }`}>
                        {m.status}
                      </span>
                    </td>
                    <td className="p-2.5 text-slate-200">{m.health_score}%</td>
                    <td className="p-2.5 text-right text-slate-400">{m.ideal_cycle_time_sec}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
