'use client'
import { useFactoryStore } from '@/lib/store'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function TelemetryPanel() {
    const selectedId = useFactoryStore((state) => state.selectedMachineId)
    const machines = useFactoryStore((state) => state.machines)
    const telemetryMap = useFactoryStore((state) => state.telemetry)

    if (!selectedId) {
        return (
            <Card className="w-full h-full bg-slate-900 border-slate-800 text-slate-400 flex items-center justify-center">
                <p>Select a machine on the 3D floor to view live telemetry.</p>
            </Card>
        )
    }

    const machine = machines.find(m => m.id === selectedId)
    const data = telemetryMap[selectedId] || []

    return (
        <Card className="w-full h-full bg-slate-900 border-slate-800 text-slate-100 flex flex-col">
            <CardHeader className="pb-2 border-b border-slate-800">
                <CardTitle className="flex justify-between items-center">
                    <span>{machine?.name} ({machine?.type})</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                        machine?.status === 'Running' ? 'bg-emerald-500/20 text-emerald-400' :
                        machine?.status === 'Fault' ? 'bg-red-500/20 text-red-400' :
                        machine?.status === 'Idle' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-blue-500/20 text-blue-400'
                    }`}>
                        {machine?.status}
                    </span>
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-4 overflow-y-auto space-y-4">
                
                <div className="h-48">
                    <h3 className="text-sm font-medium mb-2 text-slate-400">Vibration (X)</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="time" hide />
                            <YAxis stroke="#94a3b8" fontSize={12} domain={['auto', 'auto']} />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
                            <Line type="monotone" dataKey="vibration_x" stroke="#3b82f6" dot={false} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="h-48">
                    <h3 className="text-sm font-medium mb-2 text-slate-400">Spindle Temperature (°C)</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis dataKey="time" hide />
                            <YAxis stroke="#94a3b8" fontSize={12} domain={['auto', 'auto']} />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
                            <Line type="monotone" dataKey="temperature_spindle" stroke="#ef4444" dot={false} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                    <div className="bg-slate-800 p-3 rounded-lg">
                        <div className="text-xs text-slate-400">Cutting Force</div>
                        <div className="text-xl font-mono mt-1">
                            {data.length > 0 ? data[data.length - 1].cutting_force.toFixed(1) : '--'} N
                        </div>
                    </div>
                    <div className="bg-slate-800 p-3 rounded-lg">
                        <div className="text-xs text-slate-400">RUL Prediction</div>
                        <div className="text-xl font-mono mt-1 text-emerald-400">
                            {data.length > 0 && data[data.length - 1].rul !== undefined 
                                ? Math.round(data[data.length - 1].rul!) 
                                : '--'} hrs
                        </div>
                    </div>
                </div>

            </CardContent>
        </Card>
    )
}
