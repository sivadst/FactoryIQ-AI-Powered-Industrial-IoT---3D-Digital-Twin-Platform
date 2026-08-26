'use client'

import { useState } from 'react'
import { useFactoryStore, WorkOrder } from '@/lib/store'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Wrench, CheckCircle2, UserCheck, AlertCircle, Plus, Clock, FileText, Check 
} from 'lucide-react'

export function WorkOrdersPanel() {
  const workOrders = useFactoryStore((state) => state.workOrders)
  const setWorkOrders = useFactoryStore((state) => state.setWorkOrders)
  const machines = useFactoryStore((state) => state.machines)

  const [filterStatus, setFilterStatus] = useState('ALL')
  const [activeAssignModalId, setActiveAssignModalId] = useState<number | null>(null)
  const [assignedTechName, setAssignedTechName] = useState('Alex Rivera (Mechanical Lead)')
  const [activeCompleteModalId, setActiveCompleteModalId] = useState<number | null>(null)
  const [completionNotes, setCompletionNotes] = useState('Replaced spindle bearings, aligned axis, verified 0.35 mm/s vibration baseline.')
  const [partsUsed, setPartsUsed] = useState('Spindle Bearing Pack (SKF-7014)')
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const refreshWorkOrders = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/work-orders/')
      if (res.ok) setWorkOrders(await res.json())
    } catch (err) {
      console.error(err)
    }
  }

  const handleAssign = async (woId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/work-orders/${woId}/assign`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assigned_to: assignedTechName })
      })
      if (res.ok) {
        setActionMessage(`Work order #${woId} assigned to ${assignedTechName}.`)
        setActiveAssignModalId(null)
        await refreshWorkOrders()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleComplete = async (woId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/work-orders/${woId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          technician: assignedTechName,
          completion_notes: completionNotes,
          parts_used: partsUsed
        })
      })
      if (res.ok) {
        setActionMessage(`Work order #${woId} completed! Machine recovered to healthy state.`)
        setActiveCompleteModalId(null)
        await refreshWorkOrders()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const filteredWOs = workOrders.filter((w) => {
    if (filterStatus !== 'ALL' && w.status !== filterStatus) return false
    return true
  })

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-8">
      {/* Top Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Wrench className="w-5 h-5 text-blue-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">Predictive & Closed-Loop Work Orders Manager</h2>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-400">Filter:</span>
          {['ALL', 'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                filterStatus === st ? 'bg-blue-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {actionMessage && (
        <div className="bg-emerald-950/60 border border-emerald-500/60 text-emerald-200 px-4 py-2 rounded-lg text-xs flex justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-emerald-400 hover:text-white">Dismiss</button>
        </div>
      )}

      {/* Work Orders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredWOs.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-500 text-sm">
            No work orders matching the selected filter.
          </div>
        ) : (
          filteredWOs.map((wo) => {
            const machine = machines.find((m) => m.id === wo.machine_id)
            const isCompleted = wo.status === 'COMPLETED'

            return (
              <Card key={wo.id} className="bg-slate-900 border-slate-800 text-slate-100 flex flex-col justify-between hover:border-slate-700 transition-all">
                <CardHeader className="p-3.5 pb-2 border-b border-slate-800 flex flex-row items-start justify-between gap-2">
                  <div>
                    <div className="text-xs font-bold text-white font-mono">
                      {machine?.name || `MCH-${String(wo.machine_id).padStart(3, '0')}`} <span className="text-slate-500 font-sans font-normal">({wo.type})</span>
                    </div>
                    <CardTitle className="text-xs font-medium text-slate-300 mt-1 leading-snug">
                      {wo.title}
                    </CardTitle>
                  </div>
                  <Badge className={`text-[10px] uppercase font-mono ${
                    wo.priority === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-800' :
                    wo.priority === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border-orange-800' :
                    'bg-blue-500/20 text-blue-400 border-blue-800'
                  }`}>
                    {wo.priority}
                  </Badge>
                </CardHeader>

                <CardContent className="p-3.5 text-xs space-y-2.5 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    {/* Recommended Action */}
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800/80 text-[11px] text-slate-300">
                      <span className="text-slate-500 font-semibold block text-[10px] uppercase">Prescriptive Action:</span>
                      {wo.recommended_action || 'Inspect machine assembly and calibrate.'}
                    </div>

                    {/* Metadata Specs */}
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                      <div>Parts: <span className="text-slate-200 font-medium">{wo.parts_required || 'Standard kit'}</span></div>
                      <div>Duration: <span className="text-slate-200 font-mono font-medium">{wo.estimated_duration_hours}h</span></div>
                      <div>Assigned: <span className="text-cyan-300 font-medium">{wo.assigned_to || 'Unassigned'}</span></div>
                      <div>Status: <span className={`font-bold ${isCompleted ? 'text-emerald-400' : 'text-amber-400'}`}>{wo.status}</span></div>
                    </div>
                  </div>

                  {/* Actions Row */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    {!isCompleted ? (
                      <>
                        <button
                          onClick={() => setActiveAssignModalId(wo.id)}
                          className="flex-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium border border-slate-700 transition-all text-center"
                        >
                          Assign Tech
                        </button>
                        <button
                          onClick={() => setActiveCompleteModalId(wo.id)}
                          className="flex-1 px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition-all text-center shadow-sm"
                        >
                          Complete & Recover
                        </button>
                      </>
                    ) : (
                      <div className="w-full text-center text-emerald-400 text-[11px] font-semibold flex items-center justify-center gap-1.5 py-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Maintenance Verified & Recovered
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>

      {/* Assign Modal Dialog */}
      {activeAssignModalId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-md w-full text-slate-100 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-cyan-400" /> Assign Maintenance Specialist
            </h3>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Technician Name & Specialty:</label>
              <input
                type="text"
                value={assignedTechName}
                onChange={(e) => setAssignedTechName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setActiveAssignModalId(null)} className="px-3 py-1.5 text-xs text-slate-400 hover:text-white">Cancel</button>
              <button onClick={() => handleAssign(activeAssignModalId)} className="px-4 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold">Assign</button>
            </div>
          </div>
        </div>
      )}

      {/* Complete Maintenance & Machine Recovery Modal Dialog */}
      {activeCompleteModalId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 max-w-md w-full text-slate-100 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Complete Work Order & Recover Asset
            </h3>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Technician Notes:</label>
              <textarea
                value={completionNotes}
                onChange={(e) => setCompletionNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white outline-none focus:border-blue-500 h-20 resize-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Parts Replaced:</label>
              <input
                type="text"
                value={partsUsed}
                onChange={(e) => setPartsUsed(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-blue-500"
              />
            </div>
            <div className="text-[11px] text-emerald-400 bg-emerald-950/40 p-2 rounded-lg border border-emerald-800/60">
              ✓ Machine telemetry baseline will be stabilized and active alerts will be automatically resolved.
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setActiveCompleteModalId(null)} className="px-3 py-1.5 text-xs text-slate-400 hover:text-white">Cancel</button>
              <button onClick={() => handleComplete(activeCompleteModalId)} className="px-4 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold">Execute Recovery</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
