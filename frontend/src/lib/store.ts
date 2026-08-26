import { create } from 'zustand'

export type Machine = {
  id: number
  name: string
  type: string
  zone: string
  status: 'Running' | 'Idle' | 'Fault' | 'Maintenance'
  criticality: string
  pos_x: number
  pos_y: number
  pos_z: number
  health_score: number
  degradation_state: string
  active_failure_mode: string
  operating_hours: number
  ideal_cycle_time_sec: number
}

export type TopDriver = {
  feature: string
  contribution: number
  status: string
}

export type RCAReport = {
  predicted_failure_mode: string
  root_cause: string
  affected_subsystem: string
  severity: string
  evidence: string
  recommended_action: string
  urgency_hours?: number
}

export type Telemetry = {
  machine_id: number
  name?: string
  machine_type?: string
  zone?: string
  status?: string
  degradation_state?: string
  active_failure_mode?: string
  health_score?: number
  wear_factor?: number
  operating_hours?: number
  time: string
  
  // 12 Sensor Channels
  vibration_x: number
  vibration_y: number
  vibration_z: number
  temperature_spindle: number
  temperature_coolant: number
  current_l1: number
  current_l2: number
  current_l3: number
  pressure_coolant: number
  pressure_air: number
  rpm_spindle: number
  cutting_force: number

  // AI / ML Inferences
  anomaly_score?: number
  anomaly_status?: string
  predicted_failure?: string
  failure_probability?: number
  confidence?: number
  rul?: number
  rul_ci_lower?: number
  rul_ci_upper?: number
  risk_score?: number
  risk_level?: string
  top_drivers?: TopDriver[]
  rca?: RCAReport
}

export type Alert = {
  id: number
  machine_id: number
  machine_name?: string
  timestamp: string
  severity: 'INFO' | 'WARNING' | 'CRITICAL'
  type: string
  description: string
  evidence?: string
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED'
  acknowledged_by?: string
  resolved_at?: string
}

export type WorkOrder = {
  id: number
  machine_id: number
  machine_name?: string
  title: string
  failure_mode: string
  type: string
  priority: string
  status: string
  risk_score: number
  predicted_failure?: string
  recommended_action?: string
  created_at: string
  scheduled_date?: string
  assigned_to?: string
  resolved_at?: string
  estimated_duration_hours: number
  parts_required?: string
  completion_notes?: string
}

export type PlantOEE = {
  global_oee: number
  availability: number
  performance: number
  quality: number
  total_production_parts: number
  good_parts: number
  rejected_parts: number
  running_machines: number
  faulted_machines: number
  maintenance_machines: number
  downtime_pareto: Record<string, number>
}

export type UserProfile = {
  username: string
  role: string
  full_name?: string
}

export type HeatmapMode = 'STATUS' | 'HEALTH' | 'RISK' | 'OEE' | 'TEMP' | 'VIBRATION'
export type ActiveTab = 'COMMAND_CENTER' | 'DIGITAL_TWIN' | 'MACHINE_DETAIL' | 'ALERTS' | 'OEE' | 'WORK_ORDERS' | 'ML_MODELS' | 'DEMO_CONTROLS'

interface FactoryStore {
  machines: Machine[]
  telemetry: Record<number, Telemetry[]>
  alerts: Alert[]
  workOrders: WorkOrder[]
  plantOEE: PlantOEE | null
  mlMetrics: any | null
  selectedMachineId: number | null
  heatmapMode: HeatmapMode
  activeTab: ActiveTab
  zoneFilter: string
  statusFilter: string
  currentUser: UserProfile | null
  
  setMachines: (machines: Machine[]) => void
  addTelemetryBatch: (batch: Telemetry[]) => void
  setAlerts: (alerts: Alert[]) => void
  setWorkOrders: (workOrders: WorkOrder[]) => void
  setPlantOEE: (plantOEE: PlantOEE) => void
  setMlMetrics: (metrics: any) => void
  setSelectedMachineId: (id: number | null) => void
  setHeatmapMode: (mode: HeatmapMode) => void
  setActiveTab: (tab: ActiveTab) => void
  setZoneFilter: (zone: string) => void
  setStatusFilter: (status: string) => void
  setCurrentUser: (user: UserProfile | null) => void
}

export const useFactoryStore = create<FactoryStore>((set) => ({
  machines: [],
  telemetry: {},
  alerts: [],
  workOrders: [],
  plantOEE: null,
  mlMetrics: null,
  selectedMachineId: null,
  heatmapMode: 'STATUS',
  activeTab: 'COMMAND_CENTER',
  zoneFilter: 'ALL',
  statusFilter: 'ALL',
  currentUser: null,

  setMachines: (machines) => set({ machines }),

  addTelemetryBatch: (batch) => set((state) => {
    const newTelemetry = { ...state.telemetry }
    const updatedMachines = [...state.machines]

    batch.forEach((t) => {
      if (!newTelemetry[t.machine_id]) {
        newTelemetry[t.machine_id] = []
      }
      newTelemetry[t.machine_id].push(t)
      // Keep last 45 readings for smooth chart animation
      if (newTelemetry[t.machine_id].length > 45) {
        newTelemetry[t.machine_id].shift()
      }

      // Sync live machine state with telemetry
      const mIdx = updatedMachines.findIndex((m) => m.id === t.machine_id)
      if (mIdx !== -1) {
        if (t.status) updatedMachines[mIdx].status = t.status as any
        if (t.health_score !== undefined) updatedMachines[mIdx].health_score = t.health_score
        if (t.degradation_state) updatedMachines[mIdx].degradation_state = t.degradation_state
        if (t.active_failure_mode) updatedMachines[mIdx].active_failure_mode = t.active_failure_mode
      }
    })

    return { telemetry: newTelemetry, machines: updatedMachines }
  }),

  setAlerts: (alerts) => set({ alerts }),
  setWorkOrders: (workOrders) => set({ workOrders }),
  setPlantOEE: (plantOEE) => set({ plantOEE }),
  setMlMetrics: (mlMetrics) => set({ mlMetrics }),
  setSelectedMachineId: (id) => set({ selectedMachineId: id }),
  setHeatmapMode: (heatmapMode) => set({ heatmapMode }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setZoneFilter: (zoneFilter) => set({ zoneFilter }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  setCurrentUser: (currentUser) => set({ currentUser }),
}))
