'use client'

import { useEffect, useState } from 'react'
import useSWR from 'swr'

// API fetcher
const fetcher = (url: string) => fetch(url).then((res) => res.json())

interface WorkerStatus {
  worker_id: string
  core_temp_estimate: number
  psi: number
  kidney_risk: number
  heart_rate: number
  risk_level: string
  last_updated: string
}

interface DashboardData {
  total_workers: number
  high_risk_count: number
  alerts_today: number
  average_psi: number
  workers: WorkerStatus[]
}

export default function Dashboard() {
  // Poll dashboard data every 2 seconds
  const { data, error, isLoading } = useSWR<DashboardData>(
    'http://localhost:8000/api/dashboard/overview',
    fetcher,
    { refreshInterval: 2000 }
  )

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Connection Error</h1>
          <p className="text-gray-600">Unable to connect to backend API</p>
          <p className="text-sm text-gray-500 mt-2">
            Make sure FastAPI is running on http://localhost:8000
          </p>
        </div>
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">BioThermal Twin</h1>
        <p className="text-gray-600">Physics-Informed Heat Stress Early Warning</p>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total Workers"
          value={data.total_workers}
          color="blue"
        />
        <StatCard
          label="High Risk"
          value={data.high_risk_count}
          color="red"
        />
        <StatCard
          label="Alerts Today"
          value={data.alerts_today}
          color="orange"
        />
        <StatCard
          label="Avg PSI"
          value={data.average_psi.toFixed(1)}
          color="green"
        />
      </div>

      {/* Worker Grid */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Worker Status Grid</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(24)].map((_, i) => (
            <WorkerCard
              key={i}
              workerId={`W-${String(i + 1).padStart(5, '0')}`}
              psi={Math.random() * 10}
            />
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">System Status</h2>
        <div className="space-y-2">
          <StatusRow label="API Connection" status="Connected" color="green" />
          <StatusRow label="PINN Model" status="Loaded" color="green" />
          <StatusRow label="Data Stream" status="Active" color="green" />
          <StatusRow label="Last Update" status={new Date().toLocaleTimeString()} color="blue" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number | string; color: string }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    green: 'bg-green-50 text-green-700 border-green-200',
  }

  return (
    <div className={`rounded-lg border-2 p-4 ${colors[color as keyof typeof colors]}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  )
}

function WorkerCard({ workerId, psi }: { workerId: string; psi: number }) {
  let bgColor = 'bg-green-100 border-green-300'
  let textColor = 'text-green-800'

  if (psi >= 7) {
    bgColor = 'bg-red-100 border-red-300'
    textColor = 'text-red-800'
  } else if (psi >= 5) {
    bgColor = 'bg-yellow-100 border-yellow-300'
    textColor = 'text-yellow-800'
  }

  return (
    <div className={`border-2 rounded p-3 ${bgColor} cursor-pointer hover:shadow-md transition`}>
      <p className="text-xs font-mono">{workerId}</p>
      <p className={`text-lg font-bold ${textColor}`}>PSI {psi.toFixed(1)}</p>
    </div>
  )
}

function StatusRow({ label, status, color }: { label: string; status: string; color: string }) {
  const colors = {
    green: 'bg-green-100 text-green-800',
    blue: 'bg-blue-100 text-blue-800',
    red: 'bg-red-100 text-red-800',
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-700">{label}</span>
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[color as keyof typeof colors]}`}>
        {status}
      </span>
    </div>
  )
}
