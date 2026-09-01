import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import type {
  ForecastPoint,
  RiskLevel,
} from '../../types/api'
import { getRiskMeta } from '../../lib/riskLevels'

interface ForecastChartProps {
  points: ForecastPoint[]
  overallRisk: RiskLevel
}

export default function ForecastChart({
  points,
  overallRisk,
}: ForecastChartProps) {
  const data = points.map((p) => ({
    hour: `${p.lead_time_hours}h`,
    Thunderstorm: Number((p.thunderstorm_probability * 100).toFixed(1)),
    Hail: Number((p.hail_probability * 100).toFixed(1)),
    Cloudburst: Number((p.cloudburst_probability * 100).toFixed(1)),
  }))

  const riskMeta = getRiskMeta(overallRisk)

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-slate-500">
          0–6 hour probabilistic nowcast
        </p>
        <span className={`text-xs font-semibold ${riskMeta.textClass}`}>
          Overall: {riskMeta.label}
        </span>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="hour"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
            />
            <Tooltip
              formatter={(value) => `${value}%`}
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#e2e8f0',
              }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
            <Line
              type="monotone"
              dataKey="Thunderstorm"
              stroke="#38bdf8"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Hail"
              stroke="#fbbf24"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Cloudburst"
              stroke="#a78bfa"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
