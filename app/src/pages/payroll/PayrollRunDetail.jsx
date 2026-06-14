import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, Search } from 'lucide-react'
import { getPayrollRunDetails } from '../../api'
import { fmt, fmtDateTime, fmtDate, monthName, COUNTRIES } from '../../utils'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'

const PAGE_SIZE = 20

export default function PayrollRunDetail({ runId, onClose }) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [country, setCountry] = useState('')

  // Build query params
  const params = { page, limit: PAGE_SIZE }
  if (search) params.search = search
  if (country) params.country = country

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['payroll-run-detail', runId, params],
    queryFn: () => getPayrollRunDetails(runId, params).then(r => r.data),
    enabled: !!runId,
    placeholderData: (prev) => prev,
  })

  if (!runId) return null

  const totalPages = data?.pages ?? 1
  const filteredCount = data?.filtered_count ?? 0

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 960, maxHeight: '92vh' }}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '.95rem' }}>
              {data ? `${monthName(data.payroll_month)} ${data.payroll_year} Payroll` : 'Loading…'}
            </h2>
            {data && (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 4 }}>
                <StatusBadge status={data.status} type="payroll" />
                <span style={{ fontSize: '.75rem', color: 'var(--text-3)' }}>{fmtDateTime(data.run_at)}</span>
              </div>
            )}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="modal-body" style={{ padding: 0 }}>
          {isLoading && !data ? (
            <EmptyState loading />
          ) : data ? (
            <>
              {/* Message */}
              {data.message && (
                <div style={{ padding: '12px 24px', fontSize: '.82rem', color: 'var(--text-2)', borderBottom: '1px solid var(--border)', background: 'var(--bg-input)' }}>
                  {data.message}
                </div>
              )}

              {/* Summary cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 0, borderBottom: '1px solid var(--border)' }}>
                {[
                  { label: 'Total Gross', value: fmt(data.total_gross, 'USD'), color: 'var(--text-1)' },
                  { label: 'Total Deductions', value: fmt(data.total_deduction, 'USD'), color: 'var(--red)' },
                  { label: 'Total Net', value: fmt(data.total_net, 'USD'), color: 'var(--green)' },
                  { label: 'Employees', value: data.employee_count?.toLocaleString(), color: 'var(--accent)' },
                ].map((card, i) => (
                  <div key={card.label} style={{
                    padding: '16px 20px',
                    borderRight: i < 3 ? '1px solid var(--border)' : 'none',
                  }}>
                    <div style={{ fontSize: '.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em', color: 'var(--text-3)', marginBottom: 6 }}>{card.label}</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--mono)', color: card.color }}>{card.value}</div>
                  </div>
                ))}
              </div>

              {/* Filters */}
              <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
                <div className="filter-bar" style={{ marginBottom: 0 }}>
                  <div className="search-wrap">
                    <Search size={14} className="search-icon" />
                    <input className="form-input" placeholder="Search name, email, code…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
                  </div>
                  <select className="form-select" style={{ width: 'auto', minWidth: 150 }} value={country} onChange={e => { setCountry(e.target.value); setPage(1) }}>
                    <option value="">All countries</option>
                    {COUNTRIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                  {(search || country) && (
                    <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setCountry(''); setPage(1) }}>Clear</button>
                  )}
                  {isFetching && <span className="spinner" style={{ marginLeft: 8 }} />}
                </div>
              </div>

              {/* Records table */}
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Name</th>
                      <th>Department</th>
                      <th>Country</th>
                      <th>Gross</th>
                      <th>Deduction</th>
                      <th>Net</th>
                      <th>Currency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.records?.length === 0 && (
                      <tr><td colSpan={8}>
                        <EmptyState message="No records match your filters." />
                      </td></tr>
                    )}
                    {data.records?.map(rec => (
                      <tr key={rec.id} style={{ cursor: 'default' }}>
                        <td className="cell-mono" style={{ color: 'var(--text-3)' }}>{rec.employee_code}</td>
                        <td style={{ fontWeight: 600 }}>{rec.first_name} {rec.last_name}</td>
                        <td>{rec.department_name || '—'}</td>
                        <td>{rec.country}</td>
                        <td className="cell-mono">{fmt(rec.gross_amount, rec.currency)}</td>
                        <td className="cell-mono" style={{ color: 'var(--red)' }}>{fmt(rec.deduction_amount, rec.currency)}</td>
                        <td className="cell-mono" style={{ color: 'var(--green)', fontWeight: 600 }}>{fmt(rec.net_amount, rec.currency)}</td>
                        <td className="cell-mono">{rec.currency}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <Pagination
                  page={page}
                  totalPages={totalPages}
                  total={filteredCount}
                  limit={PAGE_SIZE}
                  onPageChange={setPage}
                />
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
