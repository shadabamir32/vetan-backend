import React, { useState, useEffect } from 'react'
import { Users, Receipt } from 'lucide-react'
import { ToastProvider } from './Toast'
import EmployeesPage from './pages/employees/EmployeesPage'
import EmployeeDetail from './pages/employees/EmployeeDetail'
import PayrollRunsPage from './pages/payroll/PayrollRunsPage'
import './App.css'

const TENANT_NAME = import.meta.env.VITE_TENANT_NAME || 'Vetan'

const NAV = [
  { id: 'employees', label: 'Employees', icon: Users },
  { id: 'payroll', label: 'Payroll', icon: Receipt },
]

export default function App() {
  const [route, setRoute] = useState(() => {
    const hash = window.location.hash
    if (hash.startsWith('#/employees/')) {
      const parts = hash.split('/')
      if (parts.length > 2 && parts[2]) {
        return { page: 'employees', selectedEmpId: parts[2] }
      }
    }
    if (hash === '#/payroll') {
      return { page: 'payroll', selectedEmpId: null }
    }
    return { page: 'employees', selectedEmpId: null }
  })

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash
      if (hash.startsWith('#/employees/')) {
        const parts = hash.split('/')
        if (parts.length > 2 && parts[2]) {
          setRoute({ page: 'employees', selectedEmpId: parts[2] })
          return
        }
      }
      if (hash === '#/payroll') {
        setRoute({ page: 'payroll', selectedEmpId: null })
        return
      }
      // Fallback
      setRoute({ page: 'employees', selectedEmpId: null })
    }

    if (!window.location.hash) {
      window.location.hash = '#/employees'
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleNavClick = (id) => {
    window.location.hash = id === 'employees' ? '#/employees' : '#/payroll'
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
          {/* Main employees list (preserved state) */}
          <div style={{ display: route.page === 'employees' && !route.selectedEmpId ? 'contents' : 'none' }}>
            <EmployeesPage onSelectEmployee={(id) => { window.location.hash = `#/employees/${id}` }} />
          </div>

          {/* Employee details (dynamically mounted) */}
          {route.page === 'employees' && route.selectedEmpId && (
            <EmployeeDetail
              empId={route.selectedEmpId}
              onBack={() => { window.location.hash = '#/employees' }}
            />
          )}

          {/* Payroll Runs list (preserved state) */}
          <div style={{ display: route.page === 'payroll' ? 'contents' : 'none' }}>
            <PayrollRunsPage />
          </div>
        </main>
      </div>
    </ToastProvider>
  )
}
