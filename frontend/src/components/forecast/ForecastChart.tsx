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
import type { ForecastPoint, RiskLevel } from '../../types/api'
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
    hour: p.lead_time_hours === 0 ? 'Now' : `+${p.lead_time_hours}h`,
    Thunderstorm: Number((p.thunderstorm_probability * 100).toFixed(1)),
    Hail: Number((p.hail_probability * 100).toFixed(1)),
    Cloudburst: Number((p.cloudburst_probability * 100).toFixed(1)),
  }))

  const riskMeta = getRiskMeta(overallRisk)

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[11px] text-slate-500">
          0–6 hour probabilistic nowcast
        </p>
        <span
          className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${riskMeta.borderClass} ${riskMeta.bgClass} ${riskMeta.textClass}`}
        >
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
              stroke="#475569"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              stroke="#475569"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
            />
            <Tooltip
              formatter={(value) => [`${value}%`]}
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                color: '#e2e8f0',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#94a3b8', fontSize: '11px' }}
            />
            <Legend
              wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
              iconType="circle"
              iconSize={8}
            />
            <Line
              type="monotone"
              dataKey="Thunderstorm"
              stroke="#38bdf8"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#38bdf8' }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Hail"
              stroke="#fbbf24"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#fbbf24' }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="Cloudburst"
              stroke="#a78bfa"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#a78bfa' }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
