'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, ShieldCheck, Lock, User, KeyRound } from 'lucide-react'

const DEMO_ACCOUNTS = [
  { username: 'admin', label: 'Chief Operations Director', role: 'ADMIN' },
  { username: 'plant_mgr', label: 'Plant Operations Manager', role: 'PLANT_MANAGER' },
  { username: 'maint_mgr', label: 'Maintenance Superintendent', role: 'MAINTENANCE_MANAGER' },
  { username: 'engineer', label: 'Lead Reliability Engineer', role: 'ENGINEER' },
  { username: 'operator', label: 'Senior Cell Operator', role: 'OPERATOR' },
  { username: 'viewer', label: 'Audit & Analytics Viewer', role: 'VIEWER' },
]

export default function LoginPage() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('factory123!')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const res = await fetch('http://localhost:8000/api/v1/auth/login/access-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || 'Invalid username or password')
      }

      const data = await res.json()
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify({
        username: data.username,
        role: data.role,
        full_name: data.full_name
      }))

      router.push('/')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const selectPreset = (u: string) => {
    setUsername(u)
    setPassword('factory123!')
  }

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 selection:bg-blue-600 selection:text-white">
      {/* Platform Branding Header */}
      <div className="mb-6 flex flex-col items-center text-center">
        <div className="bg-blue-600/20 border border-blue-500/40 p-3.5 rounded-2xl text-blue-400 mb-3 shadow-xl">
          <Activity className="w-10 h-10 animate-pulse" />
        </div>
        <h1 className="text-3xl font-bold text-white tracking-tight">FactoryIQ</h1>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Industrial AI Predictive Maintenance & 3D Digital Twin Command Center
        </p>
      </div>
      
      <Card className="w-full max-w-md bg-slate-900 border-slate-800 text-slate-100 shadow-2xl">
        <CardHeader className="pb-3 border-b border-slate-800">
          <CardTitle className="text-base font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-400" /> Enterprise Sign In
          </CardTitle>
          <p className="text-xs text-slate-400">Authenticate to access plant telemetry and operational controls.</p>
        </CardHeader>
        <CardContent className="pt-4">
          <form onSubmit={handleLogin} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" /> Username
              </label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 outline-none focus:border-blue-500 font-mono transition-colors" 
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-slate-400" /> Password
              </label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-100 outline-none focus:border-blue-500 font-mono transition-colors" 
              />
            </div>
            
            {error && (
              <div className="text-red-400 bg-red-950/40 border border-red-900/60 text-xs p-2.5 rounded-lg">
                {error}
              </div>
            )}
            
            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md py-2.5"
            >
              {loading ? 'Authenticating...' : 'Sign In to Command Center'}
            </Button>
          </form>

          {/* Quick RBAC Role Presets */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            <div className="text-[11px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
              Quick Role Switcher (Default: <code className="text-cyan-400">factory123!</code>)
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.username}
                  type="button"
                  onClick={() => selectPreset(acc.username)}
                  className={`p-2 rounded-lg text-left border text-[11px] transition-all ${
                    username === acc.username
                      ? 'bg-blue-950/60 border-blue-500/60 text-white'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="font-semibold text-slate-200 truncate">{acc.username}</div>
                  <div className="text-[10px] text-cyan-400 font-mono">{acc.role}</div>
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
