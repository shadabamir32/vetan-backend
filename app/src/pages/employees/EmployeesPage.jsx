import React, { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Plus, ChevronUp, ChevronDown, ChevronsUpDown, RotateCw } from 'lucide-react'
import { getEmployees, getDepartments, getCountries } from '../../api'
import { fmt, fmtDate, statusLabel, statusBadge } from '../../utils'
import Pagination from '../../components/Pagination'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import EmployeeModal from './EmployeeModal'
import EmployeeDetail from './EmployeeDetail'

const PAGE_SIZE = 20

function SortIcon({ col, current, dir }) {
  if (col !== current) return <ChevronsUpDown size={12} style={{ opacity: .3 }} />
  return dir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
}

export default function EmployeesPage({ onSelectEmployee }) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [country, setCountry] = useState('')
  const [status, setStatus] = useState('1')
  const [departmentId, setDepartmentId] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editEmp, setEditEmp] = useState(null)

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
  if (status !== '') params.status = parseInt(status)
  if (departmentId) params.department_id = departmentId

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['employees', params],
    queryFn: () => getEmployees(params).then(r => r.data),
    placeholderData: (prev) => prev,
  })

  const handleSearch = (e) => { setSearch(e.target.value); setPage(1) }

  const openEdit = (emp) => { setEditEmp(emp); setShowModal(true) }

  const total = data?.total ?? 0
  const totalPages = data?.pages ?? 1

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Employees</h1>
          <p>{total.toLocaleString()} records{isFetching ? ' · syncing…' : ''}</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => { setEditEmp(null); setShowModal(true) }}>
            <Plus size={15} /> Add Employee
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="page-body" style={{ paddingBottom: 0, flex: 'none' }}>
        <div className="filter-bar">
          <div className="search-wrap">
            <Search size={14} className="search-icon" />
            <input className="form-input" placeholder="Search name, email, code…" value={search} onChange={handleSearch} />
          </div>

          <select className="form-select" style={{ width: 'auto', minWidth: 150 }} value={country} onChange={e => { setCountry(e.target.value); setPage(1) }}>
            <option value="">All countries</option>
            {countriesData.map(c => <option key={c.country} value={c.country}>{c.country}</option>)}
          </select>

          <select className="form-select" style={{ width: 'auto', minWidth: 160 }} value={departmentId} onChange={e => { setDepartmentId(e.target.value); setPage(1) }}>
            <option value="">All departments</option>
            {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>

          <select className="form-select" style={{ width: 'auto', minWidth: 130 }} value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
            <option value="">All statuses</option>
            <option value="1">Active</option>
            <option value="0">Inactive</option>
          </select>

          {(search || country || status !== '' || departmentId) && (
            <button className="btn btn-ghost btn-sm" onClick={() => {
              setSearch(''); setCountry(''); setStatus(''); setDepartmentId(''); setPage(1)
            }}>Clear filters</button>
          )}

          <button
            className="btn btn-secondary btn-sm"
            onClick={() => refetch()}
            disabled={isFetching}
            title="Refresh data"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}
          >
            <RotateCw size={13} className={isFetching ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 32px 32px' }}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Email</th>
                <th>Department</th>
                <th>Country</th>
                <th>Annual Base Salary</th>
                <th>Status</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={8}>
                  <EmptyState loading />
                </td></tr>
              )}
              {!isLoading && data?.data?.length === 0 && (
                <tr><td colSpan={8}>
                  <EmptyState message="No employees match your filters." />
                </td></tr>
              )}
              {data?.data?.map(emp => {
                const salary = emp.current_salary
                return (
                  <tr key={emp.id} onClick={() => onSelectEmployee(emp.id)}>
                    <td className="cell-mono" style={{ color: 'var(--text-3)' }}>{emp.employee_code}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{emp.first_name} {emp.last_name}</div>
                    </td>
                    <td style={{ color: 'var(--text-2)', fontSize: '.82rem' }}>{emp.email}</td>
                    <td>{emp.department_name || '—'}</td>
                    <td>{emp.country}</td>
                    <td className="cell-mono">
                      {salary ? fmt(salary.annual_base_salary, salary.currency) : '—'}
                    </td>
                    <td><StatusBadge status={emp.status} /></td>
                    <td style={{ color: 'var(--text-2)', fontSize: '.82rem' }}>{fmtDate(emp.joining_date)}</td>
                  </tr>
                )
              })}
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
      {showModal && (
        <EmployeeModal
          employee={editEmp}
          onClose={() => { setShowModal(false); setEditEmp(null) }}
        />
      )}
    </div>
  )
}
