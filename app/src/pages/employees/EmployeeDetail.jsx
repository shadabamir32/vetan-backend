import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Pencil, Trash2, Clock } from 'lucide-react'
import { getEmployee, deleteEmployee } from '../../api'
import { fmt, fmtDate, statusLabel, statusBadge } from '../../utils'
import StatusBadge from '../../components/StatusBadge'
import { useToast } from '../../Toast'
import SalaryHistoryModal from '../salary/SalaryHistoryModal'

export default function EmployeeDetail({ empId, onClose, onEdit }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [showSalaryHistory, setShowSalaryHistory] = useState(false)

  const { data: emp, isLoading } = useQuery({
    queryKey: ['employee', empId],
    queryFn: () => getEmployee(empId).then(r => r.data),
    enabled: !!empId,
  })

  const del = useMutation({
    mutationFn: () => deleteEmployee(empId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees'] })
      toast('Employee removed.', 'success')
      onClose()
    },
    onError: () => toast('Delete failed.', 'error'),
  })

  if (!empId) return null

  const salary = emp?.current_salary

  return (
    <>
      <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
        <div className="modal" style={{ maxWidth: 560 }}>
          <div className="modal-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: 'var(--accent-lo)',
                border: '2px solid var(--accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '.7rem', fontWeight: 700, color: 'var(--accent)',
              }}>
                {emp ? emp.first_name[0] + emp.last_name[0] : ''}
              </div>
              <div>
                <h2 style={{ fontSize: '.95rem' }}>{emp ? `${emp.first_name} ${emp.last_name}` : 'Loading…'}</h2>
                {emp && <div style={{ fontSize: '.75rem', color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{emp.employee_code}</div>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {emp && (
                <>
                  <button className="btn btn-ghost btn-sm" title="Salary History" onClick={() => setShowSalaryHistory(true)}>
                    <Clock size={14} />
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={() => onEdit(emp)}><Pencil size={14} /></button>
                  <button className="btn btn-danger btn-sm" onClick={() => {
                    if (window.confirm(`Remove ${emp.first_name} ${emp.last_name}?`)) del.mutate()
                  }}><Trash2 size={14} /></button>
                </>
              )}
              <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
            </div>
          </div>

          <div className="modal-body">
            {isLoading && <div className="loading-box"><span className="spinner" /> Loading…</div>}
            {emp && (
              <>
                {/* Quick facts */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
                  <StatusBadge status={emp.status} />
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: '.78rem', color: 'var(--text-2)' }}>
                    {emp.email}
                  </span>
                </div>

                {/* Profile */}
                <div className="detail-section-title">Profile</div>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="di-label">Department</div>
                    <div className="di-value">{emp.department_name || '—'}</div>
                  </div>
                  <div className="detail-item">
                    <div className="di-label">Country</div>
                    <div className="di-value">{emp.country}</div>
                  </div>
                  <div className="detail-item">
                    <div className="di-label">Joining Date</div>
                    <div className="di-value">{fmtDate(emp.joining_date)}</div>
                  </div>
                  <div className="detail-item">
                    <div className="di-label">Termination Date</div>
                    <div className="di-value">{emp.termination_date ? fmtDate(emp.termination_date) : '—'}</div>
                  </div>
                </div>

                {/* Compensation */}
                <div className="detail-section-title">Current Compensation</div>
                {salary ? (() => {
                  const monthlyGross = parseFloat(salary.annual_base_salary) / 12 + parseFloat(salary.monthly_allowance)
                  const monthlyNet = monthlyGross - parseFloat(salary.monthly_deduction)
                  const bars = [
                    { label: 'Annual Base Salary', value: salary.annual_base_salary, color: 'var(--accent)', pct: 100 },
                    { label: 'Monthly Allowance', value: salary.monthly_allowance, color: 'var(--green)', pct: salary.monthly_allowance > 0 ? 60 : 0 },
                    { label: 'Monthly Deduction', value: salary.monthly_deduction, color: 'var(--red)', pct: salary.monthly_deduction > 0 ? 40 : 0 },
                  ]
                  return (
                    <div>
                      {bars.map(b => (
                        <div key={b.label} className="comp-bar-row">
                          <div className="label-row">
                            <span className="lbl">{b.label}</span>
                            <span className="val">{fmt(b.value, salary.currency)}</span>
                          </div>
                          <div className="bar-track">
                            <div className="bar-fill" style={{ width: `${b.pct}%`, background: b.color }} />
                          </div>
                        </div>
                      ))}
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)', fontSize: '.85rem' }}>
                        <span style={{ color: 'var(--text-2)' }}>Monthly Net</span>
                        <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, color: 'var(--green)' }}>
                          {fmt(monthlyNet, salary.currency)}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: '.82rem' }}>
                        <span style={{ color: 'var(--text-3)' }}>Currency</span>
                        <span style={{ fontFamily: 'var(--mono)', color: 'var(--text-2)' }}>{salary.currency}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: '.82rem' }}>
                        <span style={{ color: 'var(--text-3)' }}>Effective From</span>
                        <span style={{ color: 'var(--text-2)' }}>{fmtDate(salary.effective_from)}</span>
                      </div>
                      <div style={{ marginTop: 16 }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => setShowSalaryHistory(true)}>
                          <Clock size={13} /> View Salary History
                        </button>
                      </div>
                    </div>
                  )
                })() : (
                  <div style={{ color: 'var(--text-3)', fontSize: '.85rem' }}>No salary revision found.</div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {showSalaryHistory && emp && (
        <SalaryHistoryModal
          employeeId={emp.id}
          employeeName={`${emp.first_name} ${emp.last_name}`}
          employeeCountry={emp.country}
          onClose={() => setShowSalaryHistory(false)}
        />
      )}
    </>
  )
}
