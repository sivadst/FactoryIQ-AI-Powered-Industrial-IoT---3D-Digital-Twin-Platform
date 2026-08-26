'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useFactoryStore } from '@/lib/store'
import { CommandCenterTopBar } from '@/components/dashboard/CommandCenterTopBar'
import { FactoryFloor } from '@/components/dashboard/FactoryFloor'
import { TelemetryPanel } from '@/components/dashboard/TelemetryPanel'
import { MachineDetailView } from '@/components/dashboard/MachineDetailView'
import { AlertsCenter } from '@/components/dashboard/AlertsCenter'
import { WorkOrdersPanel } from '@/components/dashboard/WorkOrdersPanel'
import { OEEAnalyticsView } from '@/components/dashboard/OEEAnalyticsView'
import { MLAnalyticsView } from '@/components/dashboard/MLAnalyticsView'
import { DemoControlPanel } from '@/components/dashboard/DemoControlPanel'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Wrench, ArrowRight } from 'lucide-react'

export default function Home() {
  const router = useRouter()
  const setMachines = useFactoryStore((state) => state.setMachines)
  const addTelemetryBatch = useFactoryStore((state) => state.addTelemetryBatch)
  const setAlerts = useFactoryStore((state) => state.setAlerts)
  const setWorkOrders = useFactoryStore((state) => state.setWorkOrders)
  const setPlantOEE = useFactoryStore((state) => state.setPlantOEE)
  const setCurrentUser = useFactoryStore((state) => state.setCurrentUser)
  const activeTab = useFactoryStore((state) => state.activeTab)
  const setActiveTab = useFactoryStore((state) => state.setActiveTab)
  const workOrders = useFactoryStore((state) => state.workOrders)
  const machines = useFactoryStore((state) => state.machines)

  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userJson = localStorage.getItem('user')
    if (userJson) {
      try { setCurrentUser(JSON.parse(userJson)) } catch (e) {}
    }

    // 1. Fetch initial machine list
    fetch('http://localhost:8000/api/v1/machines/', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
      .then((res) => {
        if (res.status === 401) {
          localStorage.removeItem('token')
          router.push('/login')
          throw new Error('Unauthorized')
        }
        return res.json()
      })
      .then((data) => setMachines(data))
      .catch((err) => console.error('Failed to fetch machines', err))

    // 2. Fetch active alerts
    fetch('http://localhost:8000/api/v1/alerts/')
      .then((res) => res.json())
      .then((data) => setAlerts(data))
      .catch((err) => console.error('Failed to fetch alerts', err))

    // 3. Fetch active work orders
    fetch('http://localhost:8000/api/v1/work-orders/')
      .then((res) => res.json())
      .then((data) => setWorkOrders(data))
      .catch((err) => console.error('Failed to fetch work orders', err))

    // 4. Fetch initial OEE
    fetch('http://localhost:8000/api/v1/oee/plant')
      .then((res) => res.json())
      .then((data) => setPlantOEE(data))
      .catch((err) => console.error('Failed to fetch plant OEE', err))

    // 5. Connect WebSocket with auto-reconnect
    const connectWS = () => {
      const wsUrl = token
        ? `ws://localhost:8000/ws/telemetry?token=${token}`
        : 'ws://localhost:8000/ws/telemetry'
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'telemetry_batch') {
            addTelemetryBatch(message.data)
          }
        } catch (e) {
          console.error('WS parse error', e)
        }
      }

      ws.onclose = () => {
        setTimeout(connectWS, 3000)
      }

      wsRef.current = ws
    }

    connectWS()

    // Periodic polling for OEE, Alerts & Work Orders
    const pollInterval = setInterval(() => {
      fetch('http://localhost:8000/api/v1/alerts/')
        .then((res) => res.json())
        .then((data) => setAlerts(data))
        .catch(() => {})

      fetch('http://localhost:8000/api/v1/work-orders/')
        .then((res) => res.json())
        .then((data) => setWorkOrders(data))
        .catch(() => {})

      fetch('http://localhost:8000/api/v1/oee/plant')
        .then((res) => res.json())
        .then((data) => setPlantOEE(data))
        .catch(() => {})
    }, 5000)

    return () => {
      if (wsRef.current) wsRef.current.close()
      clearInterval(pollInterval)
    }
  }, [router, setMachines, addTelemetryBatch, setAlerts, setWorkOrders, setPlantOEE, setCurrentUser])

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Universal Command Center Header */}
      <CommandCenterTopBar />

      {/* Main Content Viewport */}
      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === 'COMMAND_CENTER' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-130px)]">
            {/* 3D Digital Twin — 3 Columns */}
            <div className="lg:col-span-3 h-full relative">
              <FactoryFloor />
            </div>

            {/* Right Sidebar — Real-Time Telemetry & Active Tickets */}
            <div className="h-full flex flex-col gap-4">
              <div className="flex-1 min-h-0">
                <TelemetryPanel />
              </div>
              
              {/* Quick Work Orders Sidebar Card */}
              <Card className="h-44 bg-slate-900 border-slate-800 text-slate-100 flex flex-col justify-between">
                <CardHeader className="py-2 px-3 border-b border-slate-800 flex flex-row items-center justify-between">
                  <CardTitle className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Wrench className="w-3.5 h-3.5 text-amber-400" /> Active Maintenance Tasks
                  </CardTitle>
                  <button
                    onClick={() => setActiveTab('WORK_ORDERS')}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                  >
                    View All <ArrowRight className="w-3 h-3" />
                  </button>
                </CardHeader>
                <CardContent className="p-2 overflow-y-auto space-y-1.5 flex-1">
                  {workOrders.filter((w) => w.status !== 'COMPLETED').slice(0, 3).map((wo) => {
                    const m = machines.find((mach) => mach.id === wo.machine_id)
                    return (
                      <div key={wo.id} className="bg-slate-950 p-2 rounded-lg border border-slate-800/80 text-[11px] flex justify-between items-center">
                        <div className="truncate max-w-[170px]">
                          <span className="font-bold text-white font-mono">{m?.name || `MCH-${wo.machine_id}`}</span>: {wo.title}
                        </div>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          wo.priority === 'CRITICAL' ? 'bg-red-950 text-red-400' : 'bg-amber-950 text-amber-400'
                        }`}>
                          {wo.priority}
                        </span>
                      </div>
                    )
                  })}
                  {workOrders.filter((w) => w.status !== 'COMPLETED').length === 0 && (
                    <div className="text-center text-slate-500 text-[11px] py-4">No active maintenance tickets.</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'MACHINE_DETAIL' && <MachineDetailView />}
        {activeTab === 'ALERTS' && <AlertsCenter />}
        {activeTab === 'WORK_ORDERS' && <WorkOrdersPanel />}
        {activeTab === 'OEE' && <OEEAnalyticsView />}
        {activeTab === 'ML_MODELS' && <MLAnalyticsView />}
        {activeTab === 'DEMO_CONTROLS' && <DemoControlPanel />}
      </div>
    </main>
  )
}
