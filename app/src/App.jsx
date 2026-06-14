import React, { useState, useEffect } from 'react'
import { Users, Receipt, LayoutDashboard } from 'lucide-react'
import { ToastProvider } from './Toast'
import EmployeesPage from './pages/employees/EmployeesPage'
import EmployeeDetail from './pages/employees/EmployeeDetail'
import PayrollRunsPage from './pages/payroll/PayrollRunsPage'
import PayrollRunDetail from './pages/payroll/PayrollRunDetail'
import DashboardPage from './pages/dashboard/DashboardPage'
import './App.css'

const TENANT_NAME = import.meta.env.VITE_TENANT_NAME || 'Vetan'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'employees', label: 'Employees', icon: Users },
  { id: 'payroll', label: 'Payroll', icon: Receipt },
]

export default function App() {
  const [route, setRoute] = useState(() => {
    const hash = window.location.hash
    const [path, queryStr] = hash.split('?')
    const params = new URLSearchParams(queryStr || '')
    const back = params.get('back')

    if (path.startsWith('#/employees/')) {
      const parts = path.split('/')
      if (parts.length > 2 && parts[2]) {
        return { page: 'employees', selectedEmpId: parts[2], selectedRunId: null, backRoute: back }
      }
    }
    if (path.startsWith('#/payroll/')) {
      const parts = path.split('/')
      if (parts.length > 2 && parts[2]) {
        return { page: 'payroll', selectedEmpId: null, selectedRunId: parts[2], backRoute: back }
      }
    }
    if (path === '#/payroll') {
      return { page: 'payroll', selectedEmpId: null, selectedRunId: null, backRoute: back }
    }
    if (path === '#/employees') {
      return { page: 'employees', selectedEmpId: null, selectedRunId: null, backRoute: back }
    }
    return { page: 'dashboard', selectedEmpId: null, selectedRunId: null, backRoute: null }
  })

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash
      const [path, queryStr] = hash.split('?')
      const params = new URLSearchParams(queryStr || '')
      const back = params.get('back')

      if (path.startsWith('#/employees/')) {
        const parts = path.split('/')
        if (parts.length > 2 && parts[2]) {
          setRoute({ page: 'employees', selectedEmpId: parts[2], selectedRunId: null, backRoute: back })
          return
        }
      }
      if (path.startsWith('#/payroll/')) {
        const parts = path.split('/')
        if (parts.length > 2 && parts[2]) {
          setRoute({ page: 'payroll', selectedEmpId: null, selectedRunId: parts[2], backRoute: back })
          return
        }
      }
      if (path === '#/payroll') {
        setRoute({ page: 'payroll', selectedEmpId: null, selectedRunId: null, backRoute: back })
        return
      }
      if (path === '#/employees') {
        setRoute({ page: 'employees', selectedEmpId: null, selectedRunId: null, backRoute: back })
        return
      }
      // Fallback
      setRoute({ page: 'dashboard', selectedEmpId: null, selectedRunId: null, backRoute: null })
    }

    if (!window.location.hash) {
      window.location.hash = '#/'
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleNavClick = (id) => {
    if (id === 'employees') {
      window.location.hash = '#/employees'
    } else if (id === 'payroll') {
      window.location.hash = '#/payroll'
    } else {
      window.location.hash = '#/'
    }
  }

  return (
    <ToastProvider>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="sidebar-logo">
            <div className="wordmark">{TENANT_NAME}<span>HR</span></div>
            <div className="org-tag">{TENANT_NAME} · Salary & Payroll</div>
          </div>
          <nav className="sidebar-nav">
            <div className="nav-label">Workspace</div>
            {NAV.map(item => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  className={`nav-item${route.page === item.id ? ' active' : ''}`}
                  onClick={() => handleNavClick(item.id)}
                >
                  <Icon size={17} className="icon" />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
          <div className="sidebar-footer">v1.0 · {TENANT_NAME}</div>
        </aside>
        <main className="main-content">
          {/* Main dashboard list (preserved state) */}
          <div style={{ display: route.page === 'dashboard' ? 'contents' : 'none' }}>
            <DashboardPage />
          </div>

          {/* Main employees list (preserved state) */}
          <div style={{ display: route.page === 'employees' && !route.selectedEmpId ? 'contents' : 'none' }}>
            <EmployeesPage onSelectEmployee={(id) => { window.location.hash = `#/employees/${id}` }} />
          </div>

          {/* Employee details (dynamically mounted) */}
          {route.page === 'employees' && route.selectedEmpId && (
            <EmployeeDetail
              empId={route.selectedEmpId}
              onBack={() => {
                if (route.backRoute) {
                  window.location.hash = `#/${route.backRoute}`
                } else {
                  window.location.hash = '#/employees'
                }
              }}
              backLabel={route.backRoute === 'dashboard' ? 'Back to Dashboard' : route.backRoute?.startsWith('payroll/') ? 'Back to Payroll Details' : 'Back to Employees'}
            />
          )}

          {/* Main payroll runs list (preserved state) */}
          <div style={{ display: route.page === 'payroll' && !route.selectedRunId ? 'contents' : 'none' }}>
            <PayrollRunsPage onSelectRun={(id) => { window.location.hash = `#/payroll/${id}` }} />
          </div>

          {/* Payroll Run Detail (dynamically mounted) */}
          {route.page === 'payroll' && route.selectedRunId && (
            <PayrollRunDetail
              runId={route.selectedRunId}
              onBack={() => { window.location.hash = '#/payroll' }}
            />
          )}
        </main>
      </div>
    </ToastProvider>
  )
}
