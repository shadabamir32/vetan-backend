import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Eye } from 'lucide-react'
import { getPayrollRuns } from '../../api'
import { fmtDateTime, monthName, monthOptions, payrollStatusLabel } from '../../utils'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import RunPayrollModal from './RunPayrollModal'
import PayrollRunDetail from './PayrollRunDetail'

const PAGE_SIZE = 20

export default function PayrollRunsPage() {
  const [page, setPage] = useState(1)
  const [month, setMonth] = useState('')
  const [year, setYear] = useState('')
  const [status, setStatus] = useState('')
  const [showRunModal, setShowRunModal] = useState(false)
  const [detailRunId, setDetailRunId] = useState(null)

  // Build query params
  const params = { page, limit: PAGE_SIZE }
  if (month) params.payroll_month = parseInt(month)
  if (year) params.payroll_year = parseInt(year)
  if (status !== '') params.status = parseInt(status)

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['payroll-runs', params],
    queryFn: () => getPayrollRuns(params).then(r => r.data),
    placeholderData: (prev) => prev,
  })

  const total = data?.total ?? 0
  const totalPages = data?.pages ?? 1

  // Generate year options (last 5 years + next year)
  const currentYear = new Date().getFullYear()
  const yearOptions = []
  for (let y = currentYear + 1; y >= currentYear - 5; y--) yearOptions.push(y)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Payroll Runs</h1>
          <p>{total.toLocaleString()} runs{isFetching ? ' · syncing…' : ''}</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowRunModal(true)}>
            <Plus size={15} /> Run Payroll
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="page-body" style={{ paddingBottom: 0, flex: 'none' }}>
        <div className="filter-bar">
          <select className="form-select" style={{ width: 'auto', minWidth: 140 }} value={month} onChange={e => { setMonth(e.target.value); setPage(1) }}>
            <option value="">All months</option>
            {monthOptions.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>

          <select className="form-select" style={{ width: 'auto', minWidth: 110 }} value={year} onChange={e => { setYear(e.target.value); setPage(1) }}>
            <option value="">All years</option>
            {yearOptions.map(y => <option key={y} value={y}>{y}</option>)}
          </select>

          <select className="form-select" style={{ width: 'auto', minWidth: 140 }} value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
            <option value="">All statuses</option>
            <option value="0">Pending</option>
            <option value="1">In Progress</option>
            <option value="2">Processed</option>
            <option value="4">Failed</option>
          </select>

          {(month || year || status !== '') && (
            <button className="btn btn-ghost btn-sm" onClick={() => {
              setMonth(''); setYear(''); setStatus(''); setPage(1)
            }}>Clear filters</button>
          )}
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 32px 32px' }}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Period</th>
                <th>Status</th>
                <th>Run At</th>
                <th>Message</th>
                <th style={{ width: 80 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={5}>
                  <EmptyState loading />
                </td></tr>
              )}
              {!isLoading && data?.data?.length === 0 && (
                <tr><td colSpan={5}>
                  <EmptyState message="No payroll runs found." />
                </td></tr>
              )}
              {data?.data?.map(run => (
                <tr key={run.id} onClick={() => setDetailRunId(run.id)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontWeight: 600 }}>
                    {monthName(run.payroll_month)} {run.payroll_year}
                  </td>
                  <td><StatusBadge status={run.status} type="payroll" /></td>
                  <td style={{ color: 'var(--text-2)', fontSize: '.82rem' }}>{fmtDateTime(run.run_at)}</td>
                  <td style={{ color: 'var(--text-3)', fontSize: '.82rem', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {run.message || '—'}
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); setDetailRunId(run.id) }}>
                      <Eye size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <Pagination
            page={page}
            totalPages={totalPages}
            total={total}
            limit={PAGE_SIZE}
            onPageChange={setPage}
          />
        </div>
      </div>

      {/* Modals */}
      {showRunModal && (
        <RunPayrollModal onClose={() => setShowRunModal(false)} />
      )}

      {detailRunId && (
        <PayrollRunDetail
          runId={detailRunId}
          onClose={() => setDetailRunId(null)}
        />
      )}
    </div>
  )
}
