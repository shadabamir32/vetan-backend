import React, { useState } from 'react'
import { X } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { createSalaryRevision } from '../../api'
import { COUNTRY_CURRENCY } from '../../utils'
import { useToast } from '../../Toast'

export default function SalaryRevisionModal({ employeeId, employeeName, employeeCountry, onClose, onSuccess }) {
  const toast = useToast()
  const currency = COUNTRY_CURRENCY[employeeCountry] || 'USD'

  const [form, setForm] = useState({
    annual_base_salary: '',
    monthly_allowance: '0',
    monthly_deduction: '0',
    currency: currency,
    effective_from: '',
  })

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: (data) => createSalaryRevision(employeeId, data),
    onSuccess: () => {
      toast('Salary revision created.', 'success')
      onSuccess()
    },
    onError: (err) => {
      toast(err?.response?.data?.detail || 'Failed to create revision.', 'error')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    mutation.mutate({
      annual_base_salary: parseFloat(form.annual_base_salary),
      monthly_allowance: parseFloat(form.monthly_allowance) || 0,
      monthly_deduction: parseFloat(form.monthly_deduction) || 0,
      currency: form.currency,
      effective_from: form.effective_from,
    })
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()} style={{ zIndex: 120 }}>
      <div className="modal" style={{ maxWidth: 480 }}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '.95rem' }}>New Salary Revision</h2>
            <div style={{ fontSize: '.75rem', color: 'var(--text-3)', marginTop: 2 }}>{employeeName}</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Annual Base Salary *</label>
                <input required type="number" min="0" step="0.01" className="form-input" value={form.annual_base_salary} onChange={set('annual_base_salary')} placeholder="e.g. 105000" />
              </div>
              <div className="form-group">
                <label className="form-label">Currency</label>
                <input className="form-input" value={form.currency} readOnly style={{ opacity: 0.6 }} />
              </div>
              <div className="form-group">
                <label className="form-label">Monthly Allowance</label>
                <input type="number" min="0" step="0.01" className="form-input" value={form.monthly_allowance} onChange={set('monthly_allowance')} />
              </div>
              <div className="form-group">
                <label className="form-label">Monthly Deduction</label>
                <input type="number" min="0" step="0.01" className="form-input" value={form.monthly_deduction} onChange={set('monthly_deduction')} />
              </div>
              <div className="form-group span-2">
                <label className="form-label">Effective From *</label>
                <input required type="date" className="form-input" value={form.effective_from} onChange={set('effective_from')} />
                <div style={{ fontSize: '.72rem', color: 'var(--text-3)', marginTop: 4 }}>
                  Must be after the current revision's effective date
                </div>
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Creating…' : 'Create Revision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
