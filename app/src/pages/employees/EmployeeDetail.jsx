import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pencil, Plus, CheckCircle, Clock, Receipt, User, HelpCircle } from 'lucide-react'
import { getEmployee, getSalaryHistory, getEmployeePayrollHistory, runIndividualPayroll } from '../../api'
import { fmt, fmtDate, monthName } from '../../utils'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import { useToast } from '../../Toast'
import EmployeeModal from './EmployeeModal'
import SalaryRevisionModal from '../salary/SalaryRevisionModal'

export default function EmployeeDetail({ empId, onBack }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState('compensation')
  const [showEditModal, setShowEditModal] = useState(false)
  const [showRevisionModal, setShowRevisionModal] = useState(false)

  // Run Individual Payroll State
  const [runMonth, setRunMonth] = useState(new Date().getMonth() + 1)
  const [runYear, setRunYear] = useState(new Date().getFullYear())

  // Queries
  const { data: emp, isLoading: isEmpLoading } = useQuery({
    queryKey: ['employee', empId],
    queryFn: () => getEmployee(empId).then(r => r.data),
    enabled: !!empId,
  })

  const { data: revisions = [], isLoading: isRevisionsLoading } = useQuery({
    queryKey: ['salary-history', empId],
    queryFn: () => getSalaryHistory(empId).then(r => r.data),
    enabled: !!empId && activeTab === 'compensation',
  })

  const { data: payrollHistory = [], isLoading: isPayrollLoading, refetch: refetchPayroll } = useQuery({
    queryKey: ['employee-payroll-history', empId],
    queryFn: () => getEmployeePayrollHistory(empId).then(r => r.data),
    enabled: !!empId && activeTab === 'payroll',
  })

  // Individual Payroll Run Mutation
  const runPayrollMutation = useMutation({
    mutationFn: (payload) => runIndividualPayroll(empId, payload),
    onSuccess: () => {
      toast('Payroll generated successfully.', 'success')
      refetchPayroll()
      qc.invalidateQueries({ queryKey: ['employee-payroll-history', empId] })
    },
    onError: (err) => {
      toast(err?.response?.data?.detail || 'Failed to generate payroll.', 'error')
    },
  })

  if (isEmpLoading) {
    return (
      <div style={{ padding: 32 }}>
        <EmptyState loading />
      </div>
    )
  }

  if (!emp) {
    return (
      <div style={{ padding: 32 }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ marginBottom: 20 }}>
          <ArrowLeft size={16} style={{ marginRight: 8 }} /> Back to Employees
        </button>
        <EmptyState message="Employee not found." />
      </div>
    )
  }

  const salary = emp.current_salary

  const handleRunPayroll = (e) => {
    e.preventDefault()
    runPayrollMutation.mutate({
      payroll_month: parseInt(runMonth),
      payroll_year: parseInt(runYear),
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
      {/* Back & Actions Header */}
      <div className="page-header" style={{ borderBottom: 'none', paddingBottom: 8 }}>
        <div className="page-header-left">
          <button className="btn btn-ghost" onClick={onBack} style={{ paddingLeft: 0 }}>
            <ArrowLeft size={16} style={{ marginRight: 8 }} /> Back to Employees
          </button>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-secondary" onClick={() => setShowEditModal(true)}>
            <Pencil size={14} style={{ marginRight: 6 }} /> Edit Profile
          </button>
        </div>
      </div>

      {/* Top Section: Profile and Summary Card */}
      <div style={{ padding: '0 32px 24px' }}>
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 8,
          padding: '24px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 24,
        }}>
          {/* Avatar and Identity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'var(--accent-lo)',
              border: '2px solid var(--accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.25rem',
              fontWeight: 700,
              color: 'var(--accent)',
            }}>
              {emp.first_name[0]}{emp.last_name[0]}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
                  {emp.first_name} {emp.last_name}
                </h1>
                <StatusBadge status={emp.status} />
              </div>
              <div style={{ color: 'var(--text-3)', fontSize: '.9rem', marginTop: 4 }}>
                {emp.email} &middot; <span className="cell-mono" style={{ fontSize: '.8rem' }}>{emp.employee_code}</span>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div style={{ display: 'flex', gap: 40, flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Department</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: 4 }}>{emp.department_name || '—'}</div>
            </div>
            <div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Country / Currency</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: 4 }}>{emp.country} ({salary?.currency || '—'})</div>
            </div>
            <div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>Annual Base Salary</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--accent)', marginTop: 4 }}>
                {salary ? fmt(salary.annual_base_salary, salary.currency) : '—'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Tabs Container */}
      <div style={{ flex: 1, padding: '0 32px 32px' }}>
        {/* Tabs Headers */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 24 }}>
          <button
            style={{
              padding: '12px 24px',
              fontSize: '.9rem',
              fontWeight: 600,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'compensation' ? '2px solid var(--accent)' : '2px solid transparent',
              color: activeTab === 'compensation' ? 'var(--text-1)' : 'var(--text-3)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
            onClick={() => setActiveTab('compensation')}
          >
            <Clock size={16} /> Compensation & Revisions
          </button>
          <button
            style={{
              padding: '12px 24px',
              fontSize: '.9rem',
              fontWeight: 600,
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'payroll' ? '2px solid var(--accent)' : '2px solid transparent',
              color: activeTab === 'payroll' ? 'var(--text-1)' : 'var(--text-3)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
            onClick={() => setActiveTab('payroll')}
          >
            <Receipt size={16} /> Payroll History {payrollHistory.length > 0 && <span className="badge badge-blue" style={{ marginLeft: 4, padding: '1px 6px', fontSize: '.65rem' }}>{payrollHistory.length}</span>}
          </button>
        </div>

        {/* Tab content: Compensation & Revisions */}
        {activeTab === 'compensation' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 32, alignItems: 'start' }}>
            {/* Compensation breakdown summary */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: 24 }}>
              <h3 style={{ marginTop: 0, marginBottom: 20, fontSize: '.95rem', fontWeight: 700 }}>Salary Breakdown</h3>
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
                      <div key={b.label} style={{ marginBottom: 18 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.8rem', marginBottom: 6 }}>
                          <span style={{ color: 'var(--text-2)' }}>{b.label}</span>
                          <span style={{ fontFamily: 'var(--mono)', fontWeight: 600 }}>{fmt(b.value, salary.currency)}</span>
                        </div>
                        <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${b.pct}%`, background: b.color }} />
                        </div>
                      </div>
                    ))}
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border)', fontSize: '.88rem' }}>
                      <span style={{ color: 'var(--text-2)', fontWeight: 600 }}>Monthly Net Pay</span>
                      <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, color: 'var(--green)' }}>
                        {fmt(monthlyNet, salary.currency)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: '.8rem', color: 'var(--text-3)' }}>
                      <span>Joined Date</span>
                      <span>{fmtDate(emp.joining_date)}</span>
                    </div>
                    {emp.termination_date && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: '.8rem', color: 'var(--red)' }}>
                        <span>Termination Date</span>
                        <span>{fmtDate(emp.termination_date)}</span>
                      </div>
                    )}
                  </div>
                )
              })() : (
                <EmptyState message="No current compensation details available." />
              )}
            </div>

            {/* Salary Revision History */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, fontSize: '.95rem', fontWeight: 700 }}>Revision History (SCD Type 2)</h3>
                <button className="btn btn-primary btn-sm" onClick={() => setShowRevisionModal(true)}>
                  <Plus size={13} style={{ marginRight: 6 }} /> New Revision
                </button>
              </div>

              {isRevisionsLoading ? (
                <div style={{ padding: 48 }}><EmptyState loading /></div>
              ) : revisions.length === 0 ? (
                <div style={{ padding: 48 }}><EmptyState message="No revision records found." /></div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ margin: 0 }}>
                    <thead>
                      <tr>
                        <th>Rev #</th>
                        <th>Annual Base</th>
                        <th>Allowance</th>
                        <th>Deduction</th>
                        <th>Effective From</th>
                        <th>Effective To</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {revisions.map(rev => (
                        <tr key={rev.id}>
                          <td className="cell-mono" style={{ color: 'var(--text-3)' }}>#{rev.revision_number}</td>
                          <td className="cell-mono">{fmt(rev.annual_base_salary, rev.currency)}</td>
                          <td className="cell-mono" style={{ color: 'var(--green)' }}>{fmt(rev.monthly_allowance, rev.currency)}</td>
                          <td className="cell-mono" style={{ color: 'var(--red)' }}>{fmt(rev.monthly_deduction, rev.currency)}</td>
                          <td>{fmtDate(rev.effective_from)}</td>
                          <td style={{ color: 'var(--text-3)' }}>{rev.effective_to ? fmtDate(rev.effective_to) : '—'}</td>
                          <td>
                            {rev.is_current ? (
                              <span className="badge badge-green"><CheckCircle size={10} style={{ marginRight: 4 }} /> Active</span>
                            ) : (
                              <span className="badge badge-gray">Historical</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab content: Payroll History */}
        {activeTab === 'payroll' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 32, alignItems: 'start' }}>
            {/* History Table */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
              <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, fontSize: '.95rem', fontWeight: 700 }}>Processed Pay Slips</h3>
              </div>

              {isPayrollLoading ? (
                <div style={{ padding: 48 }}><EmptyState loading /></div>
              ) : payrollHistory.length === 0 ? (
                <div style={{ padding: 48 }}>
                  <EmptyState message="No processed payroll records found. Use the tool on the right to generate this employee's first pay slip." />
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ margin: 0 }}>
                    <thead>
                      <tr>
                        <th>Month / Year</th>
                        <th>Gross Pay</th>
                        <th>Deductions</th>
                        <th>Net Pay</th>
                        <th>Processed At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payrollHistory.map(rec => (
                        <tr key={rec.id}>
                          <td style={{ fontWeight: 600 }}>{monthName(rec.payroll_month)} {rec.payroll_year}</td>
                          <td className="cell-mono">{fmt(rec.gross_amount, rec.currency)}</td>
                          <td className="cell-mono" style={{ color: 'var(--red)' }}>{fmt(rec.deduction_amount, rec.currency)}</td>
                          <td className="cell-mono" style={{ color: 'var(--green)', fontWeight: 600 }}>{fmt(rec.net_amount, rec.currency)}</td>
                          <td style={{ fontSize: '.8rem', color: 'var(--text-3)' }}>{fmtDate(rec.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Run payroll helper tool */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: 24 }}>
              <h3 style={{ marginTop: 0, marginBottom: 12, fontSize: '.95rem', fontWeight: 700 }}>Run Individual Payroll</h3>
              <p style={{ fontSize: '.78rem', color: 'var(--text-2)', lineHeight: 1.5, marginBottom: 20 }}>
                Calculate and generate/update the payroll slip for this employee for a specific month. If no payroll run exists for the tenant, one will be created.
              </p>

              <form onSubmit={handleRunPayroll}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 20 }}>
                  <div className="form-group">
                    <label className="form-label">Month</label>
                    <select className="form-select" value={runMonth} onChange={e => setRunMonth(e.target.value)}>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
                        <option key={m} value={m}>{monthName(m)}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Year</label>
                    <input
                      required
                      type="number"
                      min="2000"
                      className="form-input"
                      value={runYear}
                      onChange={e => setRunYear(e.target.value)}
                    />
                  </div>
                </div>

                <div style={{ fontSize: '.78rem', color: 'var(--text-3)', marginBottom: 20, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <div>Joined: <strong style={{ color: 'var(--text-2)' }}>{fmtDate(emp.joining_date)}</strong></div>
                  {emp.termination_date && <div>Terminated: <strong style={{ color: 'var(--red)' }}>{fmtDate(emp.termination_date)}</strong></div>}
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  disabled={runPayrollMutation.isPending}
                >
                  {runPayrollMutation.isPending ? 'Calculating…' : 'Generate & Save Slip'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showEditModal && (
        <EmployeeModal
          employee={emp}
          onClose={() => {
            setShowEditModal(false)
            qc.invalidateQueries({ queryKey: ['employee', empId] })
          }}
        />
      )}

      {showRevisionModal && (
        <SalaryRevisionModal
          employeeId={emp.id}
          employeeName={`${emp.first_name} ${emp.last_name}`}
          employeeCountry={emp.country}
          onClose={() => setShowRevisionModal(false)}
          onSuccess={() => {
            setShowRevisionModal(false)
            qc.invalidateQueries({ queryKey: ['salary-history', empId] })
            qc.invalidateQueries({ queryKey: ['employee', empId] })
          }}
        />
      )}
    </div>
  )
}
