
import {
  Activity,
  Bell,
  BrainCircuit,
  FileBarChart,
  Flame,
  Globe2,
  History,
  LayoutDashboard,
  Map,
  Settings,
  ShieldAlert,
} from 'lucide-react'

interface SidebarProps {
  activePage: string
  onNavigate: (page: string) => void
  onClose?: () => void
}

const navigation = [
  {
    section: 'OVERVIEW',
    items: [
      { label: 'Command Center', icon: LayoutDashboard },
    ],
  },
  {
    section: 'MONITORING',
    items: [
      { label: 'Global Fire Map', icon: Globe2 },
    ],
  },
  {
    section: 'INTELLIGENCE',
    items: [
      { label: 'AI Risk Prediction', icon: BrainCircuit },
      { label: 'Hazard Forecast', icon: ShieldAlert },
    ],
  },
  {
    section: 'ANALYTICS',
    items: [
      { label: 'Fire History', icon: History },
      { label: 'Incident Explorer', icon: Map },
      { label: 'Model Intelligence', icon: Activity },
    ],
  },
  {
    section: 'MANAGEMENT',
    items: [
      { label: 'Reports & Alerts', icon: FileBarChart },
      { label: 'Settings & Sources', icon: Settings },
    ],
  },
]

export default function Sidebar({
  activePage,
  onNavigate,
  onClose,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-pyra-border bg-pyra-surface">
      <div className="flex h-[76px] items-center gap-3 border-b border-pyra-border px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10 text-orange-400">
          <Flame size={23} />
        </div>

        <div>
          <h1 className="text-lg font-bold tracking-wide text-white">
            PyraSight
          </h1>
          <p className="text-[10px] font-medium uppercase tracking-[2px] text-pyra-muted">
            Wildfire Intelligence
          </p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-6">
        {navigation.map(group => (
          <div key={group.section} className="mb-7">
            <p className="mb-3 px-3 text-[10px] font-semibold tracking-[2px] text-pyra-muted">
              {group.section}
            </p>

            <div className="space-y-1">
              {group.items.map(item => {
                const Icon = item.icon
                const active = activePage === item.label

                return (
                  <button
                    key={item.label}
                    onClick={() => {
                      onNavigate(item.label)
                      onClose?.()
                    }}
                    className={`flex w-full items-center gap-3 rounded-lg border px-3 py-3 text-left text-sm transition-all ${
                      active
                        ? 'border-orange-500/20 bg-orange-500/10 font-medium text-orange-400'
                        : 'border-transparent text-pyra-muted hover:bg-pyra-hover hover:text-white'
                    }`}
                  >
                    <Icon size={18} />
                    <span>{item.label}</span>

                    {active && (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-orange-400" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-pyra-border p-4">
        <div className="rounded-xl border border-pyra-border bg-pyra-card p-3">
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-medium text-white">
              Workspace active
            </span>
          </div>

          <p className="text-[11px] leading-relaxed text-pyra-muted">
            Wildfire monitoring and intelligence platform
          </p>
        </div>
      </div>
    </aside>
  )
}
