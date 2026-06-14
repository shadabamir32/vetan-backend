import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Search, Download, RotateCw } from 'lucide-react'
import { getPayrollRunDetails, getDepartments, getCountries, runPayroll } from '../../api'
import { fmt, fmtDateTime, fmtDate, monthName } from '../../utils'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import { useToast } from '../../Toast'

const PAGE_SIZE = 20
const EXPORT_BATCH_SIZE = 500

export default function PayrollRunDetail({ runId, onBack }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [country, setCountry] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  // Fetch master data for filtering
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => getDepartments().then(r => r.data),
  })
  const { data: countriesData = [] } = useQuery({
    queryKey: ['countries'],
    queryFn: () => getCountries().then(r => r.data),
  })

  // Build query params
  const params = { page, limit: PAGE_SIZE }
  if (search) params.search = search
  if (country) params.country = country
  if (departmentId) params.department_id = departmentId

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['payroll-run-detail', runId, params],
    queryFn: () => getPayrollRunDetails(runId, params).then(r => r.data),
    enabled: !!runId,
    placeholderData: (prev) => prev,
  })

  // Re-run payroll mutation
  const runMutation = useMutation({
    mutationFn: () => runPayroll({ payroll_month: data.payroll_month, payroll_year: data.payroll_year }),
    onSuccess: () => {
      toast('Payroll re-run initiated successfully.', 'success')
      refetch()
      qc.invalidateQueries({ queryKey: ['payroll-runs'] })
      qc.invalidateQueries({ queryKey: ['all-runs-status'] })
    },
    onError: (err) => {
      toast(err?.response?.data?.detail || 'Failed to re-run payroll.', 'error')
    }
  })

  // Client-side CSV Exporter fetching all filtered rows
  const handleExportCSV = async () => {
    if (!data) return
    try {
      setIsExporting(true)
      const records = []
      const totalCount = data.filtered_count || 0
      const totalPages = Math.ceil(totalCount / EXPORT_BATCH_SIZE)
      for (let exportPage = 1; exportPage <= totalPages; exportPage += 1) {
        const exportParams = {
          page: exportPage,
          limit: EXPORT_BATCH_SIZE,
        }
        if (search) exportParams.search = search
        if (country) exportParams.country = country
        if (departmentId) exportParams.department_id = departmentId

        const response = await getPayrollRunDetails(runId, exportParams)
        records.push(...(response.data?.records || []))
      }

      if (records.length === 0) {
        toast('No records to export.', 'error')
        return
      }

      const headers = ['Employee Code', 'First Name', 'Last Name', 'Department', 'Country', 'Gross Amount', 'Deduction Amount', 'Net Amount', 'Currency']
      const csvRows = [headers.join(',')]

      records.forEach(rec => {
        const row = [
          rec.employee_code,
          rec.first_name,
          rec.last_name,
          rec.department_name || '',
          rec.country,
          rec.gross_amount,
          rec.deduction_amount,
          rec.net_amount,
          rec.currency
        ].map(field => `"${String(field || '').replace(/"/g, '""')}"`)
        csvRows.push(row.join(','))
      })

      const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.setAttribute('href', url)
      link.setAttribute('download', `payroll_register_${data.payroll_month}_${data.payroll_year}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast('CSV exported successfully.', 'success')
    } catch (err) {
      toast('Failed to export CSV.', 'error')
    } finally {
      setIsExporting(false)
    }
  }

  if (!runId) return null

  const totalPages = data?.pages ?? 1
  const filteredCount = data?.filtered_count ?? 0

  // Calculate visual spend percentages
  const showSpendRatio = data && parseFloat(data.total_gross) > 0
  const netPct = showSpendRatio ? (parseFloat(data.total_net) / parseFloat(data.total_gross)) * 100 : 0
  const deductionPct = showSpendRatio ? (parseFloat(data.total_deduction) / parseFloat(data.total_gross)) * 100 : 0

  // Check if run is eligible for re-run (status 2 or 4)
  const isEligibleToReRun = data && (data.status === 2 || data.status === 4)

  if (isLoading && !data) {
    return (
      <div style={{ padding: 32 }}>
        <EmptyState loading />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
      {/* Back & Actions Header */}
      <div className="page-header" style={{ borderBottom: 'none', paddingBottom: 8 }}>
        <div className="page-header-left">
          <button className="btn btn-ghost" onClick={onBack} style={{ paddingLeft: 0 }}>
            <ArrowLeft size={16} style={{ marginRight: 8 }} /> Back to Payroll
          </button>
        </div>
        <div className="page-header-actions">
          {isEligibleToReRun && (
            <button
              className="btn btn-secondary"
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCw size={13} className={runMutation.isPending ? 'spin' : ''} />
              <span>{runMutation.isPending ? 'Re-queueing…' : 'Re-run Payroll'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Title section */}
      {data && (
        <div style={{ padding: '0 32px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
              {monthName(data.payroll_month)} {data.payroll_year} Payroll
            </h1>
            <StatusBadge status={data.status} type="payroll" />
            <span style={{ fontSize: '.85rem', color: 'var(--text-3)' }}>Run at {fmtDateTime(data.run_at)}</span>
          </div>
          {data.message && (
            <p style={{ margin: '8px 0 0', fontSize: '.82rem', color: 'var(--text-2)' }}>{data.message}</p>
          )}
        </div>
      )}

      {data ? (
        <>
          {/* Summary cards */}
          <div style={{ padding: '0 32px 24px' }}>
            <div className="stat-grid" style={{ marginBottom: 24 }}>
              {[
                { label: 'Total Gross (USD)', value: fmt(data.total_gross, 'USD'), color: 'var(--text-1)' },
                { label: 'Total Deductions (USD)', value: fmt(data.total_deduction, 'USD'), color: 'var(--red)' },
                { label: 'Total Net Outflow (USD)', value: fmt(data.total_net, 'USD'), color: 'var(--green)' },
                { label: 'Employee Count', value: data.employee_count?.toLocaleString(), color: 'var(--accent)' },
              ].map((card) => (
                <div className="stat-card" key={card.label}>
                  <div className="sc-label">{card.label}</div>
                  <div className="sc-value" style={{ color: card.color }}>{card.value}</div>
                  <div className="sc-sub">Run-wide aggregate</div>
                </div>
              ))}
            </div>

            {/* Cohesive Visual Spend Ratio Bar */}
            {showSpendRatio && (
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.74rem', color: 'var(--text-2)', marginBottom: 8 }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} />
                    Net Take-home: {netPct.toFixed(1)}%
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--red)' }} />
                    Deductions: {deductionPct.toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden', background: 'var(--border)' }}>
                  <div style={{ width: `${netPct}%`, background: 'var(--green)' }} title={`Net Salary Outflow: ${netPct.toFixed(1)}%`} />
                  <div style={{ width: `${deductionPct}%`, background: 'var(--red)' }} title={`Deductions: ${deductionPct.toFixed(1)}%`} />
                </div>
              </div>
            )}
          </div>

          {/* Filters Bar */}
          <div style={{ padding: '0 32px 16px' }}>
            <div className="filter-bar" style={{ marginBottom: 0 }}>
              <div className="search-wrap">
                <Search size={14} className="search-icon" />
                <input className="form-input" placeholder="Search name, email, code…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
              </div>
              <select className="form-select" style={{ width: 'auto', minWidth: 150 }} value={country} onChange={e => { setCountry(e.target.value); setPage(1) }}>
                <option value="">All countries</option>
                {countriesData.map(c => <option key={c.country} value={c.country}>{c.country}</option>)}
              </select>
              <select className="form-select" style={{ width: 'auto', minWidth: 160 }} value={departmentId} onChange={e => { setDepartmentId(e.target.value); setPage(1) }}>
                <option value="">All departments</option>
                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
              {(search || country || departmentId) && (
                <button className="btn btn-ghost btn-sm" onClick={() => { setSearch(''); setCountry(''); setDepartmentId(''); setPage(1) }}>Clear filters</button>
              )}
              {isFetching && <span className="spinner" style={{ marginLeft: 8 }} />}

              {/* Export Register Button */}
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleExportCSV}
                disabled={isExporting || filteredCount === 0}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}
              >
                <Download size={13} />
                <span>{isExporting ? 'Exporting…' : 'Export Register'}</span>
              </button>
            </div>
          </div>

          {/* Records Table */}
          <div style={{ padding: '0 32px 32px' }}>
            <div className="table-wrap">
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
                    <tr
                      key={rec.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => { window.location.hash = `#/employees/${rec.employee_id}?back=payroll/${runId}` }}
                    >
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
          </div>
        </>
      ) : null}
    </div>
  )
}
