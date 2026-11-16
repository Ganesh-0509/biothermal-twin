'use client'

export default function Dashboard() {
  return (
    <div className="min-h-screen p-6 bg-gray-50">
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">BioThermal Twin</h1>
        <p className="text-gray-600">Physics-Informed Heat Stress Early Warning System</p>
      </header>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Workers" value="100" color="bg-blue-50 text-blue-700 border-blue-200" />
        <StatCard label="High Risk" value="8" color="bg-red-50 text-red-700 border-red-200" />
        <StatCard label="Alerts Today" value="23" color="bg-orange-50 text-orange-700 border-orange-200" />
        <StatCard label="Avg PSI" value="4.2" color="bg-green-50 text-green-700 border-green-200" />
      </div>

      {/* Worker Grid */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Worker Status Grid</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(24)].map((_, i) => {
            const psi = Math.random() * 10
            let bgColor = 'bg-green-100 border-green-300'
            if (psi >= 7) bgColor = 'bg-red-100 border-red-300'
            else if (psi >= 5) bgColor = 'bg-yellow-100 border-yellow-300'

            return (
              <div key={i} className={`border-2 rounded p-3 ${bgColor} cursor-pointer hover:shadow-md transition`}>
                <p className="text-xs font-mono">W-{String(i + 1).padStart(5, '0')}</p>
                <p className="text-lg font-bold">PSI {psi.toFixed(1)}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">System Status</h2>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-gray-700">API Connection</span>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              Ready
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">PINN Model</span>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              MAE: 0.139°C
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Training Data</span>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              144,000 samples
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className={`rounded-lg border-2 p-4 ${color}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  )
}
