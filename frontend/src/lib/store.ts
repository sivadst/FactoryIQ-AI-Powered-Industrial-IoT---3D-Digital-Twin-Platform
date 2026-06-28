import { create } from 'zustand'

export type Machine = {
  id: number
  name: string
  type: string
  status: 'Running' | 'Idle' | 'Fault' | 'Maintenance'
  pos_x: number
  pos_y: number
  pos_z: number
}

export type Telemetry = {
  machine_id: number
  vibration_x: number
  temperature_spindle: number
  cutting_force: number
  time: string
  rul?: number
  anomaly_score?: number
  fault_class?: number
}

interface FactoryStore {
  machines: Machine[]
  telemetry: Record<number, Telemetry[]>
  selectedMachineId: number | null
  setMachines: (machines: Machine[]) => void
  addTelemetryBatch: (batch: Telemetry[]) => void
  setSelectedMachineId: (id: number | null) => void
}

export const useFactoryStore = create<FactoryStore>((set) => ({
  machines: [],
  telemetry: {},
  selectedMachineId: null,
  
  setMachines: (machines) => set({ machines }),
  
  addTelemetryBatch: (batch) => set((state) => {
    const newTelemetry = { ...state.telemetry }
    batch.forEach(t => {
      if (!newTelemetry[t.machine_id]) {
        newTelemetry[t.machine_id] = []
      }
      newTelemetry[t.machine_id].push(t)
      // Keep last 30 readings
      if (newTelemetry[t.machine_id].length > 30) {
        newTelemetry[t.machine_id].shift()
      }
    })
    return { telemetry: newTelemetry }
  }),
  
  setSelectedMachineId: (id) => set({ selectedMachineId: id })
}))
