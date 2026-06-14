import React, { useState } from 'react'
import { Users, Receipt } from 'lucide-react'
import { ToastProvider } from './Toast'
import EmployeesPage from './pages/employees/EmployeesPage'
import PayrollRunsPage from './pages/payroll/PayrollRunsPage'
import './App.css'

const TENANT_NAME = import.meta.env.VITE_TENANT_NAME || 'Vetan'

const NAV = [
  { id: 'employees', label: 'Employees', icon: Users },
  { id: 'payroll', label: 'Payroll', icon: Receipt },
]

export default function App() {
  const [page, setPage] = useState('employees')

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
                  className={`nav-item${page === item.id ? ' active' : ''}`}
                  onClick={() => setPage(item.id)}
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
          {page === 'employees' && <EmployeesPage />}
          {page === 'payroll' && <PayrollRunsPage />}
        </main>
      </div>
    </ToastProvider>
  )
}
