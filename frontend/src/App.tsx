
import { useState } from 'react'
import { Command, X } from 'lucide-react'
import PredictionLab from './pages/PredictionLab'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import CommandCenter from './pages/CommandCenter'
import GlobalFireMap from './pages/GlobalFireMap'
import MesogeosForecast from './pages/MesogeosForecast'
import FireHistory from './pages/FireHistory'
import IncidentExplorer from './pages/IncidentExplorer'
import ModelIntelligence from './pages/ModelIntelligence'
import ReportsAlerts from './pages/ReportsAlerts'
import SettingsDataSources from './pages/SettingsDataSources'
function App() {
  const [activePage, setActivePage] = useState('Command Center')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const renderPage = () => {
    switch (activePage) {
      case 'Command Center':
        return <CommandCenter />

      case 'Global Fire Map':
        return <GlobalFireMap />
      case 'AI Risk Prediction':
        return <PredictionLab />
      case 'Hazard Forecast':
        return <MesogeosForecast />
      case 'Fire History':
        return <FireHistory />
      case 'Incident Explorer':
        return <IncidentExplorer />
      case 'Model Intelligence':
        return <ModelIntelligence />

      case 'Reports & Alerts':
        return <ReportsAlerts />

      case 'Settings & Sources':
        return <SettingsDataSources />

      default:
        return (
          <div className="rounded-xl border border-pyra-border bg-pyra-surface p-8 text-center">
            <h2 className="text-lg font-semibold text-white">
              Page not found
            </h2>
            <p className="mt-2 text-sm text-pyra-muted">
              Select a valid section from the navigation sidebar.
            </p>
          </div>
        )
    }
  }

  return (
    <div className="min-h-screen bg-pyra-bg text-pyra-text">
      <div className="flex min-h-screen">

        {/* Sidebar */}
        <div
          className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 lg:static lg:translate-x-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <Sidebar
            activePage={activePage}
            onNavigate={setActivePage}
            onClose={() => setSidebarOpen(false)}
          />
        </div>

        {/* Mobile overlay */}
        {sidebarOpen && (
          <button
            aria-label="Close navigation"
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          >
            <X className="sr-only" />
          </button>
        )}

        {/* Main application */}
        <main className="min-w-0 flex-1">

          <Topbar
            activePage={activePage}
            onMenuClick={() => setSidebarOpen(true)}
          />

          <section className="p-5 sm:p-7">

            {/* Breadcrumb */}
            <div className="mb-3 flex items-center gap-2 text-xs text-pyra-muted">
              <Command size={14} />
              <span>Intelligence Workspace</span>
              <span>/</span>
              <span className="text-orange-400">
                {activePage}
              </span>
            </div>

            {/* Page heading */}
            <div className="mb-7">
              <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {activePage === 'Command Center'
                  ? 'Wildfire Intelligence Overview'
                  : activePage}
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-pyra-muted">
                Monitor satellite observations, analyze wildfire
                risk, and explore environmental intelligence.
              </p>
            </div>

            {/* Active page */}
            {renderPage()}

            {/* Footer */}
            <footer className="mt-8 border-t border-pyra-border pt-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-[10px] text-pyra-muted">
                  PyraSight · Wildfire Intelligence Platform
                </p>

                <p className="text-[10px] text-pyra-muted">
                  Satellite observations are not necessarily confirmed wildfires.
                </p>
              </div>
            </footer>

          </section>
        </main>
      </div>
    </div>
  )
}

export default App
