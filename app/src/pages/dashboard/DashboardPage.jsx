import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, CartesianGrid
} from 'recharts'
import { LayoutDashboard, Users, TrendingUp, DollarSign, ArrowUpRight, ArrowDownRight, AlertTriangle, Clock } from 'lucide-react'
import {
  getAnalyticsStats,
  getAnalyticsDepartments,
  getAnalyticsCountries,
  getAnalyticsDistribution,
  getAnalyticsExtremeSalaries,
  getAnalyticsSalaryAudit
} from '../../api'
import { fmt, fmtM, fmtNum, DEPT_COLORS } from '../../utils'

const TIP_STYLE = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: 8,
  fontSize: 12,
  color: 'var(--text-1)',
}

const TIP_ITEM_STYLE = {
  color: 'var(--text-1)',
}

const TIP_LABEL_STYLE = {
  color: 'var(--text-2)',
}

function StatCard({ label, value, sub, variant, icon: Icon }) {
  return (
    <div className={`stat-card${variant ? ` ${variant}` : ''}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="sc-label">{label}</div>
          <div className="sc-value">{value}</div>
          {sub && <div className="sc-sub">{sub}</div>}
        </div>
        {Icon && (
          <div style={{
            background: 'var(--bg-input)',
            padding: 8,
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)',
            color: variant === 'green' ? 'var(--green)' : variant === 'amber' ? 'var(--amber)' : 'var(--accent)'
          }}>
            <Icon size={18} />
          </div>
        )}
      </div>
    </div>
  )
}

export default function DashboardPage({ isActive }) {
  // Queries run sequentially (each waits for the previous to succeed) to avoid
  // simultaneous SQLite connections which cause lock contention in Docker/WSL2.
  // Sequential: ~150ms × 6 ≈ 900ms total vs ~6s when all fire at once.

  const { data: stats, isLoading: sl, isSuccess: statsOk } = useQuery({
    queryKey: ['analytics-stats'],
    queryFn: () => getAnalyticsStats().then(r => r.data),
    enabled: !!isActive
  })

  const { data: depts = [], isLoading: dl, isSuccess: deptsOk } = useQuery({
    queryKey: ['analytics-depts'],
    queryFn: () => getAnalyticsDepartments().then(r => r.data),
    enabled: !!isActive && statsOk
  })

  const { data: countries = [], isLoading: cl, isSuccess: countriesOk } = useQuery({
    queryKey: ['analytics-countries'],
    queryFn: () => getAnalyticsCountries().then(r => r.data),
    enabled: !!isActive && deptsOk
  })

  const { data: distribution = [], isLoading: dil, isSuccess: distOk } = useQuery({
    queryKey: ['analytics-distribution'],
    queryFn: () => getAnalyticsDistribution().then(r => r.data),
    enabled: !!isActive && countriesOk
  })

  const { data: extremes, isLoading: el, isSuccess: extremesOk } = useQuery({
    queryKey: ['analytics-extremes'],
    queryFn: () => getAnalyticsExtremeSalaries().then(r => r.data),
    enabled: !!isActive && distOk
  })

  const { data: audit, isLoading: al } = useQuery({
    queryKey: ['analytics-audit'],
    queryFn: () => getAnalyticsSalaryAudit().then(r => r.data),
    enabled: !!isActive && extremesOk
  })

  const loading = sl || dl || cl || dil || el || al

  const handleRowClick = (empId) => {
    window.location.hash = `#/employees/${empId}?back=dashboard`
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1>Dashboard</h1>
          <p>Real-time salary intelligence and workforce aggregates</p>
        </div>
      </div>

      <div className="page-body">
        {loading ? (
          <div className="loading-box"><span className="spinner" />Loading dashboard analytics…</div>
        ) : (
          <>
            {/* KPI Summary Row */}
            <div className="stat-grid">
              <StatCard
                label="Total Headcount"
                value={fmtNum(stats?.total_employees)}
                sub={`${fmtNum(stats?.active_employees)} Active`}
                icon={Users}
              />
              <StatCard
                label="Avg Base Salary (USD)"
                value={fmt(stats?.avg_base_salary)}
                sub={`Median: ${fmt(stats?.median_base_salary)}`}
                variant="green"
                icon={TrendingUp}
              />
              <StatCard
                label="Total Annual Payroll"
                value={fmtM(stats?.total_base_salary)}
                sub="USD Equivalent"
                icon={DollarSign}
              />
              <StatCard
                label="Salary Range"
                value={`${fmtM(stats?.min_base_salary)} – ${fmtM(stats?.max_base_salary)}`}
                sub="min → max base USD"
                variant="amber"
                icon={LayoutDashboard}
              />
            </div>

            {/* Charts Row 1 */}
            <div className="charts-grid">
              <div className="chart-card">
                <h3>Average Salary by Department</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={depts.slice(0, 10)} layout="vertical" margin={{ left: 8, right: 24, top: 0, bottom: 0 }}>
                    <XAxis type="number" tickFormatter={v => `$${(v / 1000).toFixed(0)}K`} tick={{ fill: 'var(--text-3)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="department" width={110} tick={{ fill: 'var(--text-2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={TIP_STYLE} itemStyle={TIP_ITEM_STYLE} labelStyle={TIP_LABEL_STYLE} formatter={(v) => [fmt(v), 'Avg Salary']} />
                    <Bar dataKey="avg_salary" radius={[0, 4, 4, 0]}>
                      {depts.slice(0, 10).map((_, i) => (
                        <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-card">
                <h3>Headcount by Department</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={depts.slice(0, 10)}
                      dataKey="employee_count"
                      nameKey="department"
                      cx="50%" cy="45%" outerRadius={80}
                      stroke="none"
                    >
                      {depts.slice(0, 10).map((_, i) => (
                        <Cell key={i} fill={DEPT_COLORS[i % DEPT_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={TIP_STYLE} itemStyle={TIP_ITEM_STYLE} labelStyle={TIP_LABEL_STYLE} formatter={(v, n) => [fmtNum(v), n]} />
                    <Legend
                      formatter={(v) => <span style={{ fontSize: 11, color: 'var(--text-2)' }}>{v}</span>}
                      iconSize={10}
                      layout="horizontal"
                      align="center"
                      verticalAlign="bottom"
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Charts Row 2 */}
            <div className="charts-grid">
              <div className="chart-card">
                <h3>Salary Distribution Bands</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={distribution} margin={{ left: 8, right: 8, top: 10, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="band" tick={{ fill: 'var(--text-2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis type="number" tick={{ fill: 'var(--text-3)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={TIP_STYLE} itemStyle={TIP_ITEM_STYLE} labelStyle={TIP_LABEL_STYLE} formatter={(v) => [fmtNum(v), 'Employees']} />
                    <Bar dataKey="employee_count" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-card">
                <h3>Headcount by Country</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={countries.slice(0, 10)} layout="vertical" margin={{ left: 8, right: 24, top: 0, bottom: 0 }}>
                    <XAxis type="number" tick={{ fill: 'var(--text-3)', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <YAxis type="category" dataKey="country" width={110} tick={{ fill: 'var(--text-2)', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={TIP_STYLE} itemStyle={TIP_ITEM_STYLE} labelStyle={TIP_LABEL_STYLE} formatter={(v) => [fmtNum(v), 'Employees']} />
                    <Bar dataKey="employee_count" radius={[0, 4, 4, 0]}>
                      {countries.slice(0, 10).map((_, i) => (
                        <Cell key={i} fill={DEPT_COLORS[(i + 3) % DEPT_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* High/Low Lists Row */}
            <div className="dashboard-tables-grid">
              <div className="chart-card" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <ArrowUpRight size={16} className="text-green" style={{ color: 'var(--green)' }} />
                  <h3 style={{ marginBottom: 0 }}>Highest Paid Employees</h3>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Country</th>
                        <th style={{ textAlign: 'right' }}>Annual Salary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {extremes?.highest_paid?.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-3)' }}>No data available</td>
                        </tr>
                      ) : (
                        extremes?.highest_paid?.map((emp) => (
                          <tr key={emp.id} onClick={() => handleRowClick(emp.id)}>
                            <td className="cell-mono">{emp.employee_code}</td>
                            <td>{emp.first_name} {emp.last_name}</td>
                            <td>{emp.department_name}</td>
                            <td>{emp.country}</td>
                            <td className="cell-mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                              {fmt(emp.salary, emp.currency)}
                              {emp.currency !== 'USD' && (
                                <span style={{ fontSize: '0.72rem', color: 'var(--text-3)', display: 'block' }}>
                                  ({fmt(emp.salary_usd, 'USD')} USD)
                                </span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="chart-card" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                  <ArrowDownRight size={16} className="text-red" style={{ color: 'var(--red)' }} />
                  <h3 style={{ marginBottom: 0 }}>Lowest Paid Employees</h3>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Country</th>
                        <th style={{ textAlign: 'right' }}>Annual Salary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {extremes?.lowest_paid?.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-3)' }}>No data available</td>
                        </tr>
                      ) : (
                        extremes?.lowest_paid?.map((emp) => (
                          <tr key={emp.id} onClick={() => handleRowClick(emp.id)}>
                            <td className="cell-mono">{emp.employee_code}</td>
                            <td>{emp.first_name} {emp.last_name}</td>
                            <td>{emp.department_name}</td>
                            <td>{emp.country}</td>
                            <td className="cell-mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                              {fmt(emp.salary, emp.currency)}
                              {emp.currency !== 'USD' && (
                                <span style={{ fontSize: '0.72rem', color: 'var(--text-3)', display: 'block' }}>
                                  ({fmt(emp.salary_usd, 'USD')} USD)
                                </span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* HR Salary Action Center Grid */}
            <div className="section-divider" style={{ marginTop: 32, marginBottom: 16 }}>HR Salary Action Center</div>
            <div className="dashboard-tables-grid" style={{ marginBottom: 0 }}>
              {/* Pay Equity Audit */}
              <div className="chart-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <AlertTriangle size={16} style={{ color: 'var(--amber)' }} />
                  <h3 style={{ marginBottom: 0 }}>Salary Below Department Average</h3>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-2)', marginBottom: 14 }}>
                  Active employees earning less than 85% of their department's average base salary.
                </p>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th style={{ textAlign: 'right' }}>Annual Salary</th>
                        <th style={{ textAlign: 'center' }}>% of Dept Avg</th>
                      </tr>
                    </thead>
                    <tbody>
                      {!audit?.underpaid_employees || audit.underpaid_employees.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', padding: '24px 12px', color: 'var(--green)' }}>
                            <span style={{ fontWeight: 600, display: 'block', marginBottom: 4 }}>✓ Pay Equity Maintained</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-3)' }}>
                              No active employees are paid below 85% of their department's average.
                            </span>
                          </td>
                        </tr>
                      ) : (
                        audit.underpaid_employees.slice(0, 5).map((emp) => (
                          <tr key={emp.id} onClick={() => handleRowClick(emp.id)}>
                            <td className="cell-mono">{emp.employee_code}</td>
                            <td>{emp.first_name} {emp.last_name}</td>
                            <td>{emp.department_name}</td>
                            <td className="cell-mono" style={{ textAlign: 'right', fontWeight: 600 }}>
                              {fmt(emp.salary, emp.currency)}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <span className="badge badge-amber">
                                {Math.round(emp.compa_ratio * 100)}% of Avg
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Overdue Salary Reviews */}
              <div className="chart-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <Clock size={16} style={{ color: 'var(--accent)' }} />
                  <h3 style={{ marginBottom: 0 }}>Overdue Salary Reviews</h3>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-2)', marginBottom: 14 }}>
                  Active employees with no compensation changes in the last 365 days.
                </p>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Last Revision</th>
                        <th style={{ textAlign: 'right' }}>Days Elapsed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {!audit?.overdue_reviews || audit.overdue_reviews.length === 0 ? (
                        <tr>
                          <td colSpan={5} style={{ textAlign: 'center', padding: '24px 12px', color: 'var(--green)' }}>
                            <span style={{ fontWeight: 600, display: 'block', marginBottom: 4 }}>✓ Reviews Up to Date</span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-3)' }}>
                              All active employees have had a salary revision within the past year.
                            </span>
                          </td>
                        </tr>
                      ) : (
                        audit.overdue_reviews.slice(0, 5).map((emp) => (
                          <tr key={emp.id} onClick={() => handleRowClick(emp.id)}>
                            <td className="cell-mono">{emp.employee_code}</td>
                            <td>{emp.first_name} {emp.last_name}</td>
                            <td>{emp.department_name}</td>
                            <td>{emp.last_revision_date ? new Date(emp.last_revision_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}</td>
                            <td className="cell-mono" style={{ textAlign: 'right' }}>
                              <span className="badge badge-red" style={{ fontWeight: 600 }}>
                                {emp.days_since_revision} Days
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
