import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pencil, Plus, CheckCircle, Clock, Receipt, User, HelpCircle } from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { getEmployee, getSalaryHistory, getEmployeePayrollHistory, runIndividualPayroll } from '../../api'
import { fmt, fmtDate, monthName } from '../../utils'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import { useToast } from '../../Toast'
import EmployeeModal from './EmployeeModal'
import SalaryRevisionModal from '../salary/SalaryRevisionModal'

export default function EmployeeDetail({ empId, onBack, backLabel = 'Back to Employees' }) {
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

  // Enabled up front to show in top banner summary
  const { data: revisions = [], isLoading: isRevisionsLoading } = useQuery({
    queryKey: ['salary-history', empId],
    queryFn: () => getSalaryHistory(empId).then(r => r.data),
    enabled: !!empId,
  })

  // Enabled up front to calculate Last Paid and Paid YTD
  const { data: payrollHistory = [], isLoading: isPayrollLoading, refetch: refetchPayroll } = useQuery({
    queryKey: ['employee-payroll-history', empId],
    queryFn: () => getEmployeePayrollHistory(empId).then(r => r.data),
    enabled: !!empId,
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
          <ArrowLeft size={16} style={{ marginRight: 8 }} /> {backLabel}
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

  // 1. Dynamic Tenure Calculation
  const tenureText = (() => {
    if (!emp.joining_date) return '—'
    const start = new Date(emp.joining_date)
    const end = emp.termination_date ? new Date(emp.termination_date) : new Date()
    let years = end.getFullYear() - start.getFullYear()
    let months = end.getMonth() - start.getMonth()
    if (months < 0) {
      years--
      months += 12
    }
    const parts = []
    if (years > 0) parts.push(`${years} yr${years > 1 ? 's' : ''}`)
    if (months > 0 || parts.length === 0) parts.push(`${months} mo${months > 1 ? 's' : ''}`)
    return parts.join(' ')
  })()

  // 2. Last Paid pay slip details
  const sortedPayroll = [...payrollHistory].sort(
    (a, b) => (b.payroll_year * 12 + b.payroll_month) - (a.payroll_year * 12 + a.payroll_month)
  )
  const lastPaidRecord = sortedPayroll[0]
  const lastPaidText = lastPaidRecord
    ? `${fmt(lastPaidRecord.net_amount, lastPaidRecord.currency)} (${monthName(lastPaidRecord.payroll_month).slice(0, 3)} ${lastPaidRecord.payroll_year})`
    : 'Never paid'

  // 3. Year-to-Date (YTD) sum paid
  const currentYear = new Date().getFullYear()
  const displayCurrency = salary?.currency || 'USD'
  const ytdPaid = payrollHistory
    .filter(p => p.payroll_year === currentYear)
    .reduce((sum, p) => sum + parseFloat(p.net_amount), 0)
  const ytdText = payrollHistory.length > 0 ? fmt(ytdPaid, displayCurrency) : '—'

  // 4. Raise / Growth calculations for salary revisions (SCD Type 2)
  const sortedRevisions = [...revisions].sort((a, b) => a.revision_number - b.revision_number)
  const revisionsWithRaise = sortedRevisions.map((rev, index) => {
    let raisePercent = null
    let raiseAmount = null
    if (index > 0) {
      const prevRev = sortedRevisions[index - 1]
      const prevSalary = parseFloat(prevRev.annual_base_salary)
      const currSalary = parseFloat(rev.annual_base_salary)
      raiseAmount = currSalary - prevSalary
      if (prevSalary > 0) {
        raisePercent = (raiseAmount / prevSalary) * 100
      }
    }
    return { ...rev, raisePercent, raiseAmount }
  })
  const displayRevisions = [...revisionsWithRaise].reverse()

  // 5. Chart Data Preparation
  const chartData = sortedRevisions.map(r => {
    const base = parseFloat(r.annual_base_salary)
    const allowance = parseFloat(r.monthly_allowance) * 12 // Annualized allowance
    return {
      date: new Date(r.effective_from).toLocaleDateString(undefined, { month: 'short', year: 'numeric' }),
      'Base Salary': base,
      'Total Package': base + allowance,
    }
  })

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-hi)',
          padding: '10px 14px',
          borderRadius: 6,
          fontSize: '.8rem',
          boxShadow: 'var(--shadow-lg)'
        }}>
          <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text-1)' }}>{label}</div>
          {payload.map(p => (
            <div key={p.name} style={{ display: 'flex', gap: 12, justifyContent: 'space-between', color: p.color, marginTop: 4 }}>
              <span style={{ fontWeight: 500 }}>{p.name}:</span>
              <span style={{ fontFamily: 'var(--mono)', fontWeight: 600 }}>{fmt(p.value, displayCurrency)}</span>
            </div>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
      {/* Back & Actions Header */}
      <div className="page-header" style={{ borderBottom: 'none', paddingBottom: 8 }}>
        <div className="page-header-left">
          <button className="btn btn-ghost" onClick={onBack} style={{ paddingLeft: 0 }}>
            <ArrowLeft size={16} style={{ marginRight: 8 }} /> {backLabel}
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
        <div className="profile-card">
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
          <div className="profile-metrics">
            <div style={{ minWidth: 120 }}>
              <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Department</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 4, color: 'var(--text-1)' }}>{emp.department_name || '—'}</div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 2 }}>{emp.country}</div>
            </div>
            <div style={{ minWidth: 120 }}>
              <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Tenure</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 4, color: 'var(--text-1)' }}>{tenureText}</div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 2 }}>Joined {fmtDate(emp.joining_date)}</div>
            </div>
            <div style={{ minWidth: 140 }}>
              <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Last Paid</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 4, color: 'var(--text-1)', fontFamily: 'var(--mono)' }}>{lastPaidText}</div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 2 }}>Direct Deposit</div>
            </div>
            <div style={{ minWidth: 120 }}>
              <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Paid YTD ({currentYear})</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: 4, color: 'var(--text-1)', fontFamily: 'var(--mono)' }}>{ytdText}</div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 2 }}>Net Salary Sum</div>
            </div>
            <div style={{ minWidth: 150 }}>
              <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Annual Base Salary</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--accent)', marginTop: 4 }}>
                {salary ? fmt(salary.annual_base_salary, salary.currency) : '—'}
              </div>
              <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 2 }}>Current Active Package</div>
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            <div className="comp-grid">
              {/* Compensation breakdown summary */}
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: 24 }}>
                <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: '.95rem', fontWeight: 700 }}>Salary Breakdown</h3>
                {salary ? (() => {
                  const monthlyBase = parseFloat(salary.annual_base_salary) / 12
                  const monthlyAllowance = parseFloat(salary.monthly_allowance)
                  const monthlyDeduction = parseFloat(salary.monthly_deduction)
                  const monthlyGross = monthlyBase + monthlyAllowance
                  const monthlyNet = monthlyGross - monthlyDeduction

                  const netPct = (monthlyNet / monthlyGross) * 100
                  const deductionPct = (monthlyDeduction / monthlyGross) * 100

                  return (
                    <div>
                      {/* Big direct deposit summary */}
                      <div style={{ marginBottom: 20 }}>
                        <div style={{ fontSize: '.68rem', color: 'var(--text-3)', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.08em' }}>Monthly Take-home Pay</div>
                        <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--green)', fontFamily: 'var(--mono)', marginTop: 4 }}>
                          {fmt(monthlyNet, salary.currency)}
                        </div>
                        <div style={{ fontSize: '.75rem', color: 'var(--text-2)', marginTop: 4 }}>
                          Gross: {fmt(monthlyGross, salary.currency)} &middot; Deductions: {fmt(monthlyDeduction, salary.currency)}
                        </div>
                      </div>

                      {/* Cohesive segmented visual bar */}
                      <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', margin: '20px 0', background: 'var(--border)' }}>
                        <div style={{ width: `${netPct}%`, background: 'var(--green)' }} title={`Net Take-home: ${netPct.toFixed(1)}%`} />
                        <div style={{ width: `${deductionPct}%`, background: 'var(--red)' }} title={`Deductions: ${deductionPct.toFixed(1)}%`} />
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 20 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' }}>
                          <span style={{ color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)' }} /> Monthly Base
                          </span>
                          <span style={{ fontFamily: 'var(--mono)', fontWeight: 600 }}>{fmt(monthlyBase, salary.currency)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' }}>
                          <span style={{ color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} /> Monthly Allowance
                          </span>
                          <span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--green)' }}>+{fmt(monthlyAllowance, salary.currency)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.82rem' }}>
                          <span style={{ color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--red)' }} /> Monthly Deduction
                          </span>
                          <span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--red)' }}>-{fmt(monthlyDeduction, salary.currency)}</span>
                        </div>
                      </div>

                      <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.78rem', color: 'var(--text-3)' }}>
                          <span>Joined Date</span>
                          <span>{fmtDate(emp.joining_date)}</span>
                        </div>
                        {emp.termination_date && (
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.78rem', color: 'var(--red)' }}>
                            <span>Termination Date</span>
                            <span>{fmtDate(emp.termination_date)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })() : (
                  <EmptyState message="No current compensation details available." />
                )}
              </div>

              {/* Salary Growth Chart Card */}
              <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                padding: 24,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 320
              }}>
                <h3 style={{ marginTop: 0, marginBottom: 20, fontSize: '.95rem', fontWeight: 700 }}>Compensation Progression</h3>
                {chartData.length > 0 ? (
                  <div style={{ flex: 1, minHeight: 220, width: '100%' }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorBase" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="colorPackage" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--green)" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="var(--green)" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                        <XAxis dataKey="date" stroke="var(--text-3)" fontSize={11} tickLine={false} />
                        <YAxis
                          stroke="var(--text-3)"
                          fontSize={11}
                          tickLine={false}
                          axisLine={false}
                          width={45}
                          tickFormatter={(v) => {
                            const val = parseFloat(v);
                            if (val >= 1.0e9) return `$${(val / 1.0e9).toFixed(1).replace(/\.0$/, '')}B`;
                            if (val >= 1.0e6) return `$${(val / 1.0e6).toFixed(1).replace(/\.0$/, '')}M`;
                            if (val >= 1.0e3) return `$${(val / 1.0e3).toFixed(1).replace(/\.0$/, '')}K`;
                            return `$${val}`;
                          }}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area type="monotone" name="Total Package" dataKey="Total Package" stroke="var(--green)" fillOpacity={1} fill="url(#colorPackage)" strokeWidth={2} />
                        <Area type="monotone" name="Base Salary" dataKey="Base Salary" stroke="var(--accent)" fillOpacity={1} fill="url(#colorBase)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <EmptyState message="No progression data available." />
                )}
              </div>
            </div>

            {/* Salary Revision History Table */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, fontSize: '.95rem', fontWeight: 700 }}>Revision History</h3>
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
                        <th>Raise Growth</th>
                        <th>Effective From</th>
                        <th>Effective To</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displayRevisions.map(rev => {
                        let raiseBadge = null
                        if (rev.raisePercent !== null) {
                          const isPositive = rev.raisePercent >= 0
                          const color = isPositive ? 'var(--green)' : 'var(--red)'
                          const sign = isPositive ? '+' : ''
                          raiseBadge = (
                            <span style={{ color, fontWeight: 600, fontSize: '.78rem' }}>
                              {sign}{rev.raisePercent.toFixed(1)}%
                            </span>
                          )
                        } else {
                          raiseBadge = <span style={{ color: 'var(--text-3)', fontSize: '.78rem' }}>Hire Rate</span>
                        }
                        return (
                          <tr key={rev.id}>
                            <td className="cell-mono" style={{ color: 'var(--text-3)' }}>#{rev.revision_number}</td>
                            <td className="cell-mono">{fmt(rev.annual_base_salary, rev.currency)}</td>
                            <td className="cell-mono" style={{ color: 'var(--green)' }}>{fmt(rev.monthly_allowance, rev.currency)}</td>
                            <td className="cell-mono" style={{ color: 'var(--red)' }}>{fmt(rev.monthly_deduction, rev.currency)}</td>
                            <td>{raiseBadge}</td>
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
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab content: Payroll History */}
        {activeTab === 'payroll' && (
          <div className="payroll-grid">
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
