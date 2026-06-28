'use client'
import { useEffect, useRef } from 'react'
import { FactoryFloor } from '@/components/dashboard/FactoryFloor'
import { TelemetryPanel } from '@/components/dashboard/TelemetryPanel'
import { WorkOrdersPanel } from '@/components/dashboard/WorkOrdersPanel'
import { useRouter } from 'next/navigation'
import { useFactoryStore } from '@/lib/store'
import { Activity, Settings, AlertTriangle, ShieldCheck, LogOut } from 'lucide-react'

export default function Home() {
    const router = useRouter()
    const setMachines = useFactoryStore(state => state.setMachines)
    const addTelemetryBatch = useFactoryStore(state => state.addTelemetryBatch)
    const machines = useFactoryStore(state => state.machines)
    const wsRef = useRef<WebSocket | null>(null)

    useEffect(() => {
        const token = localStorage.getItem('token')
        if (!token) {
            router.push('/login')
            return
        }

        // Fetch initial machines
        fetch('http://localhost:8000/api/v1/machines/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(res => {
                if (res.status === 401) {
                    localStorage.removeItem('token')
                    router.push('/login')
                    throw new Error('Unauthorized')
                }
                return res.json()
            })
            .then(data => setMachines(data))
            .catch(err => console.error("Failed to fetch machines", err))

        // Connect WebSocket for telemetry
        const ws = new WebSocket('ws://localhost:8000/ws/telemetry')
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data)
            if (message.type === 'telemetry_batch') {
                addTelemetryBatch(message.data)
                
                // Optionally update machine status randomly or based on real data
                // In a full implementation, the backend would broadcast machine status changes.
            }
        }
        wsRef.current = ws

        return () => {
            ws.close()
        }
    }, [setMachines, addTelemetryBatch])

    const stats = {
        total: machines.length,
        running: machines.filter(m => m.status === 'Running').length,
        fault: machines.filter(m => m.status === 'Fault').length,
        maintenance: machines.filter(m => m.status === 'Maintenance').length,
    }

    return (
        <main className="min-h-screen bg-slate-950 text-slate-200 flex flex-col p-4 font-sans">
            <header className="flex justify-between items-center mb-4">
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                        <Activity className="text-blue-500" /> FactoryIQ
                    </h1>
                    <p className="text-sm text-slate-400">Industrial AI Predictive Maintenance & OEE Command Center</p>
                </div>
                
                <div className="flex gap-4">
                    <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
                        <ShieldCheck className="text-emerald-500 w-5 h-5" />
                        <div>
                            <div className="text-xs text-slate-400">Running</div>
                            <div className="font-bold">{stats.running}</div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
                        <AlertTriangle className="text-red-500 w-5 h-5" />
                        <div>
                            <div className="text-xs text-slate-400">Faults</div>
                            <div className="font-bold">{stats.fault}</div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800">
                        <Settings className="text-blue-500 w-5 h-5" />
                        <div>
                            <div className="text-xs text-slate-400">Maintenance</div>
                            <div className="font-bold">{stats.maintenance}</div>
                        </div>
                    </div>
                    <button 
                        onClick={() => {
                            localStorage.removeItem('token')
                            router.push('/login')
                        }}
                        className="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-lg border border-slate-800 hover:bg-slate-800 transition-colors"
                    >
                        <LogOut className="text-slate-400 w-5 h-5" />
                    </button>
                </div>
            </header>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 overflow-hidden h-[calc(100vh-100px)]">
                {/* 3D Digital Twin - Takes up 3 columns */}
                <div className="lg:col-span-3 h-full relative flex flex-col">
                    <div className="flex-1 min-h-0">
                        <FactoryFloor />
                    </div>
                    
                    {/* Simplified layout for other dashboards, keeping focus on the 3D twin and telemetry */}
                    <div className="h-48 mt-4 grid grid-cols-3 gap-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center items-center">
                            <h3 className="text-sm font-semibold text-slate-400 mb-2">OEE Availability</h3>
                            <div className="text-3xl font-bold text-emerald-400">92.4%</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center items-center">
                            <h3 className="text-sm font-semibold text-slate-400 mb-2">OEE Performance</h3>
                            <div className="text-3xl font-bold text-blue-400">88.1%</div>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center items-center">
                            <h3 className="text-sm font-semibold text-slate-400 mb-2">OEE Quality</h3>
                            <div className="text-3xl font-bold text-indigo-400">99.2%</div>
                        </div>
                    </div>
                    
                    {/* Floating Overlay Stats */}
                    <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md p-3 rounded-lg border border-slate-700 pointer-events-none">
                        <h3 className="text-sm font-semibold text-slate-300 mb-1">Global OEE</h3>
                        <div className="text-2xl font-bold text-white">68.4%</div>
                        <div className="text-xs text-emerald-400">↑ 1.2% from last shift</div>
                    </div>
                </div>

                {/* Right Sidebar - Analytics/Telemetry */}
                <div className="h-full flex flex-col gap-4">
                    <div className="flex-1 min-h-0">
                        <TelemetryPanel />
                    </div>
                    <div className="flex-1 min-h-0">
                        <WorkOrdersPanel />
                    </div>
                </div>
            </div>
        </main>
    )
}
