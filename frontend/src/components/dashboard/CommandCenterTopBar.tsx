'use client'

import { useFactoryStore, ActiveTab } from '@/lib/store'
import { 
  Activity, ShieldCheck, AlertTriangle, Wrench, BarChart3, 
  BrainCircuit, Sliders, LogOut, Layers, Bell, CheckCircle2, Factory
} from 'lucide-react'
import { useRouter } from 'next/navigation'

export function CommandCenterTopBar() {
  const router = useRouter()
  const machines = useFactoryStore((state) => state.machines)
  const alerts = useFactoryStore((state) => state.alerts)
  const workOrders = useFactoryStore((state) => state.workOrders)
  const plantOEE = useFactoryStore((state) => state.plantOEE)
  const activeTab = useFactoryStore((state) => state.activeTab)
  const setActiveTab = useFactoryStore((state) => state.setActiveTab)
  const currentUser = useFactoryStore((state) => state.currentUser)

  const runningCount = machines.filter((m) => m.status === 'Running').length
  const faultCount = machines.filter((m) => m.status === 'Fault' || m.degradation_state === 'CRITICAL').length
  const activeAlertsCount = alerts.filter((a) => a.status === 'ACTIVE').length
  const activeWorkOrdersCount = workOrders.filter((w) => w.status === 'OPEN' || w.status === 'ASSIGNED' || w.status === 'IN_PROGRESS').length

  const globalOEEFormatted = plantOEE ? `${(plantOEE.global_oee * 100).toFixed(1)}%` : '80.2%'

  const tabs: { id: ActiveTab; label: string; icon: any }[] = [
    { id: 'COMMAND_CENTER', label: 'Command Center', icon: Factory },
    { id: 'MACHINE_DETAIL', label: 'Machine Deep-Dive', icon: Activity },
    { id: 'ALERTS', label: `Alerts (${activeAlertsCount})`, icon: Bell },
    { id: 'WORK_ORDERS', label: `Work Orders (${activeWorkOrdersCount})`, icon: Wrench },
    { id: 'OEE', label: 'OEE Analytics', icon: BarChart3 },
    { id: 'ML_MODELS', label: 'AI Model Center', icon: BrainCircuit },
    { id: 'DEMO_CONTROLS', label: 'Demo / Fault Injection', icon: Sliders },
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex flex-col gap-2.5 shadow-md">
      {/* Top Row: Title, KPI Badges, User Profile */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600/20 border border-blue-500/40 p-2 rounded-xl text-blue-400 shadow-inner">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              FactoryIQ <span className="text-[11px] font-normal px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">ENTERPRISE 10/10</span>
            </h1>
            <p className="text-xs text-slate-400">Industrial AI Predictive Maintenance & 3D Digital Twin Command Center</p>
          </div>
        </div>

        {/* Global KPI Chips */}
        <div className="flex items-center gap-3">
          {/* Total Machines */}
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <Layers className="w-4 h-4 text-slate-400" />
            <div>
              <div className="text-[10px] text-slate-400 leading-none">Total Assets</div>
              <div className="text-sm font-bold text-white font-mono">{machines.length}</div>
            </div>
          </div>

          {/* Running */}
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-[10px] text-slate-400 leading-none">Online</div>
              <div className="text-sm font-bold text-emerald-400 font-mono">{runningCount}</div>
            </div>
          </div>

          {/* Critical Faults */}
          <div className={`bg-slate-950 border px-3 py-1.5 rounded-lg flex items-center gap-2 ${
            faultCount > 0 ? 'border-red-500/50 bg-red-950/20' : 'border-slate-800'
          }`}>
            <AlertTriangle className={`w-4 h-4 ${faultCount > 0 ? 'text-red-400 animate-bounce' : 'text-slate-500'}`} />
            <div>
              <div className="text-[10px] text-slate-400 leading-none">Critical / Faults</div>
              <div className={`text-sm font-bold font-mono ${faultCount > 0 ? 'text-red-400' : 'text-slate-300'}`}>{faultCount}</div>
            </div>
          </div>

          {/* Plant OEE */}
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <div>
              <div className="text-[10px] text-slate-400 leading-none">Plant OEE</div>
              <div className="text-sm font-bold text-blue-400 font-mono">{globalOEEFormatted}</div>
            </div>
          </div>

          {/* Active Work Orders */}
          <div className="bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <Wrench className="w-4 h-4 text-amber-400" />
            <div>
              <div className="text-[10px] text-slate-400 leading-none">Work Orders</div>
              <div className="text-sm font-bold text-amber-400 font-mono">{activeWorkOrdersCount}</div>
            </div>
          </div>

          {/* User Profile & Logout */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-white">{currentUser?.username || 'admin'}</div>
              <div className="text-[10px] text-cyan-400 font-mono uppercase">{currentUser?.role || 'ADMIN'}</div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-2 rounded-lg bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1.5 border-t border-slate-800/80 pt-2 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'bg-slate-950/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-slate-800/60'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              {tab.label}
            </button>
          )
        })}
      </nav>
    </header>
  )
}
