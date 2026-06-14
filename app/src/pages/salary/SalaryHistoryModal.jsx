import React, { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { X, Plus, CheckCircle } from 'lucide-react'
import { getSalaryHistory } from '../../api'
import { fmt, fmtDate } from '../../utils'
import SalaryRevisionModal from './SalaryRevisionModal'

export default function SalaryHistoryModal({ employeeId, employeeName, employeeCountry, onClose }) {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)

  const { data: revisions = [], isLoading } = useQuery({
    queryKey: ['salary-history', employeeId],
    queryFn: () => getSalaryHistory(employeeId).then(r => r.data),
    enabled: !!employeeId,
  })

  return (
    <>
      <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()} style={{ zIndex: 110 }}>
        <div className="modal" style={{ maxWidth: 720 }}>
          <div className="modal-header">
            <div>
              <h2 style={{ fontSize: '.95rem' }}>Salary History</h2>
              <div style={{ fontSize: '.75rem', color: 'var(--text-3)', marginTop: 2 }}>{employeeName}</div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)}>
                <Plus size={13} /> New Revision
              </button>
              <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
            </div>
          </div>

          <div className="modal-body" style={{ padding: 0 }}>
            {isLoading ? (
              <div className="loading-box"><span className="spinner" /> Loading…</div>
            ) : revisions.length === 0 ? (
              <div className="empty-state" style={{ padding: 40 }}>No salary revisions found.</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Rev #</th>
                      <th>Annual Base</th>
                      <th>Allowance</th>
                      <th>Deduction</th>
                      <th>Currency</th>
                      <th>Effective From</th>
                      <th>Effective To</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {revisions.map(rev => (
                      <tr key={rev.id} style={{ cursor: 'default' }}>
                        <td className="cell-mono" style={{ color: 'var(--text-3)' }}>#{rev.revision_number}</td>
                        <td className="cell-mono">{fmt(rev.annual_base_salary, rev.currency)}</td>
                        <td className="cell-mono" style={{ color: 'var(--green)' }}>{fmt(rev.monthly_allowance, rev.currency)}</td>
                        <td className="cell-mono" style={{ color: 'var(--red)' }}>{fmt(rev.monthly_deduction, rev.currency)}</td>
                        <td className="cell-mono">{rev.currency}</td>
                        <td style={{ fontSize: '.82rem' }}>{fmtDate(rev.effective_from)}</td>
                        <td style={{ fontSize: '.82rem', color: 'var(--text-3)' }}>{rev.effective_to ? fmtDate(rev.effective_to) : '—'}</td>
                        <td>
                          {rev.is_current ? (
                            <span className="badge badge-green"><CheckCircle size={11} style={{ marginRight: 4 }} /> Current</span>
                          ) : (
                            <span className="badge badge-gray">Past</span>
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
      </div>

      {showCreate && (
        <SalaryRevisionModal
          employeeId={employeeId}
          employeeName={employeeName}
          employeeCountry={employeeCountry}
          onClose={() => setShowCreate(false)}
          onSuccess={() => {
            setShowCreate(false)
            qc.invalidateQueries({ queryKey: ['salary-history', employeeId] })
            qc.invalidateQueries({ queryKey: ['employee', employeeId] })
          }}
        />
      )}
    </>
  )
}
