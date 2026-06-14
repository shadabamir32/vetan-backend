import React, { useState } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { runPayroll } from '../../api'
import { monthOptions } from '../../utils'
import { useToast } from '../../Toast'

export default function RunPayrollModal({ onClose }) {
  const toast = useToast()
  const qc = useQueryClient()
  const currentDate = new Date()

  const [form, setForm] = useState({
    payroll_month: currentDate.getMonth() + 1,
    payroll_year: currentDate.getFullYear(),
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: (data) => runPayroll(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['payroll-runs'] })
      toast('Payroll queued for processing.', 'success')
      onClose()
    },
    onError: (err) => {
      toast(err?.response?.data?.detail || 'Failed to queue payroll.', 'error')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate({
      payroll_month: parseInt(form.payroll_month),
      payroll_year: parseInt(form.payroll_year),
    })
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth: 420 }}>
        <div className="modal-header">
          <h2 style={{ fontSize: '.95rem' }}>Run Payroll</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <p style={{ fontSize: '.82rem', color: 'var(--text-2)', marginBottom: 20 }}>
              Select the month and year to process payroll for all eligible employees.
            </p>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Month *</label>
                <select required className="form-select" value={form.payroll_month} onChange={set('payroll_month')}>
                  {monthOptions.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Year *</label>
                <input required type="number" min="2000" className="form-input" value={form.payroll_year} onChange={set('payroll_year')} />
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Queuing…' : 'Run Payroll'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
