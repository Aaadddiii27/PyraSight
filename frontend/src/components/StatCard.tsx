
import type { LucideIcon } from 'lucide-react'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  description: string
  icon: LucideIcon
  trend?: number
  trendLabel?: string
  accent?: 'orange' | 'green' | 'blue' | 'purple'
}

const accentStyles = {
  orange: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  blue: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
}

export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendLabel = 'vs previous period',
  accent = 'orange',
}: StatCardProps) {
  const trendPositive = trend !== undefined && trend > 0
  const trendNegative = trend !== undefined && trend < 0

  return (
    <div className="group rounded-xl border border-pyra-border bg-pyra-surface p-5 transition-all duration-200 hover:border-white/15 hover:bg-pyra-card">

      <div className="mb-5 flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-pyra-muted">
            {title}
          </p>

          <h3 className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            {value}
          </h3>
        </div>

        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl border ${accentStyles[accent]}`}
        >
          <Icon size={21} />
        </div>
      </div>

      <div className="flex min-h-5 flex-wrap items-center gap-2">
        {trend !== undefined && (
          <span
            className={`inline-flex items-center gap-1 text-xs font-semibold ${
              trendPositive
                ? 'text-emerald-400'
                : trendNegative
                  ? 'text-red-400'
                  : 'text-pyra-muted'
            }`}
          >
            {trendPositive ? (
              <ArrowUpRight size={14} />
            ) : trendNegative ? (
              <ArrowDownRight size={14} />
            ) : (
              <Minus size={14} />
            )}
            {Math.abs(trend)}%
          </span>
        )}

        <span className="text-xs text-pyra-muted">
          {description}
        </span>
      </div>

      {trend !== undefined && (
        <p className="mt-2 text-[10px] text-pyra-muted">
          {trendLabel}
        </p>
      )}
    </div>
  )
}
