
import {
  Bell,
  ChevronDown,
  Search,
  Menu,
} from 'lucide-react'

interface TopbarProps {
  activePage: string
  onMenuClick: () => void
}

export default function Topbar({
  activePage,
  onMenuClick,
}: TopbarProps) {
  const pageTitle =
    activePage === 'Command Center'
      ? 'Wildfire Intelligence Overview'
      : activePage

  return (
    <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-pyra-border bg-pyra-bg/95 px-4 backdrop-blur-xl sm:px-7">

      {/* Page information */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="text-pyra-muted transition hover:text-white lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={22} />
        </button>

        <div>
          <p className="text-[10px] uppercase tracking-[2px] text-pyra-muted">
            PYRASIGHT / WORKSPACE
          </p>

          <h2 className="text-sm font-semibold text-white sm:text-base">
            {pageTitle}
          </h2>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 sm:gap-5">

        <div className="hidden items-center gap-2 rounded-full border border-pyra-border px-3 py-2 md:flex">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs text-pyra-muted">
            Workspace active
          </span>
        </div>

        <button
          aria-label="Search"
          className="text-pyra-muted transition hover:text-white"
        >
          <Search size={19} />
        </button>

        <button
          aria-label="Notifications"
          className="relative text-pyra-muted transition hover:text-white"
        >
          <Bell size={19} />

          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-orange-400" />
        </button>

        <div className="hidden h-8 w-8 items-center justify-center rounded-full border border-pyra-border bg-pyra-card text-xs font-semibold text-white sm:flex">
          PS
        </div>

        <ChevronDown
          size={14}
          className="hidden text-pyra-muted sm:block"
        />
      </div>
    </header>
  )
}
