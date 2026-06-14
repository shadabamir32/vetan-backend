import React from 'react'
import { statusLabel, statusBadge, payrollStatusLabel, payrollStatusBadge } from '../utils'

export default function StatusBadge({ status, type = 'employee' }) {
  const label = type === 'payroll' ? payrollStatusLabel(status) : statusLabel(status)
  const cls = type === 'payroll' ? payrollStatusBadge(status) : statusBadge(status)

  return <span className={`badge ${cls}`}>{label}</span>
}
