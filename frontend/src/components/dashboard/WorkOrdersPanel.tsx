'use client'
import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useFactoryStore } from '@/lib/store'

type WorkOrder = {
    id: number;
    machine_id: number;
    created_at: string;
    scheduled_date: string;
    type: string;
    priority: string;
    status: string;
    description: string;
}

export function WorkOrdersPanel() {
    const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
    const machines = useFactoryStore(state => state.machines)

    useEffect(() => {
        const fetchWOs = async () => {
            const token = localStorage.getItem('token')
            if (!token) return
            try {
                const res = await fetch('http://localhost:8000/api/v1/work-orders/', {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
                if (res.ok) {
                    setWorkOrders(await res.json())
                }
            } catch (err) {
                console.error("Failed to fetch work orders", err)
            }
        }
        fetchWOs()
        const interval = setInterval(fetchWOs, 30000)
        return () => clearInterval(interval)
    }, [])

    return (
        <Card className="w-full h-full bg-slate-900 border-slate-800 text-slate-100 flex flex-col">
            <CardHeader className="pb-2 border-b border-slate-800">
                <CardTitle>Work Orders</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0 overflow-y-auto">
                <div className="divide-y divide-slate-800">
                    {workOrders.length === 0 ? (
                        <div className="p-4 text-center text-slate-500">No active work orders.</div>
                    ) : (
                        workOrders.map(wo => {
                            const machine = machines.find(m => m.id === wo.machine_id)
                            return (
                                <div key={wo.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="font-medium text-slate-200">
                                            {machine?.name || `Machine #${wo.machine_id}`}
                                        </div>
                                        <Badge variant={wo.priority === 'Critical' ? 'destructive' : 'default'} className={
                                            wo.priority === 'High' ? 'bg-orange-500 hover:bg-orange-600 text-white' : ''
                                        }>
                                            {wo.priority}
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-slate-400">{wo.description}</p>
                                    <div className="flex justify-between items-center mt-3 text-xs text-slate-500">
                                        <span>Type: {wo.type}</span>
                                        <span>Scheduled: {new Date(wo.scheduled_date).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            )
                        })
                    )}
                </div>
            </CardContent>
        </Card>
    )
}
