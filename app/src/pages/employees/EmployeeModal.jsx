import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createEmployee, updateEmployee } from '../../api'
import { COUNTRIES, COUNTRY_CURRENCY, DEPARTMENTS } from '../../utils'
import { useToast } from '../../Toast'

const DEFAULTS = {
  first_name: '',
  last_name: '',
  email: '',
  country: '',
  department_id: '',
  joining_date: new Date().toISOString().slice(0, 10),
  status: 1,
  // Initial salary fields (only for create)
  annual_base_salary: '',
  monthly_allowance: '0',
  monthly_deduction: '0',
  currency: '',
}

export default function EmployeeModal({ employee, onClose }) {
  const toast = useToast()
  const qc = useQueryClient()
  const isEdit = !!employee

  const [form, setForm] = useState(DEFAULTS)

  useEffect(() => {
    if (employee) {
      setForm({
        first_name: employee.first_name,
        last_name: employee.last_name,
        email: employee.email,
        country: employee.country,
        department_id: employee.department_id || '',
        joining_date: employee.joining_date,
        status: employee.status,
        termination_date: employee.termination_date || '',
        // Not editable via this form
        annual_base_salary: '',
        monthly_allowance: '0',
        monthly_deduction: '0',
        currency: COUNTRY_CURRENCY[employee.country] || '',
      })
    }
  }, [employee])

  // Auto-set currency when country changes
  useEffect(() => {
    if (form.country && COUNTRY_CURRENCY[form.country]) {
      setForm(f => ({ ...f, currency: COUNTRY_CURRENCY[form.country] }))
    }
  }, [form.country])

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: isEdit
      ? (data) => updateEmployee(employee.id, data)
      : (data) => createEmployee(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees'] })
      if (isEdit) qc.invalidateQueries({ queryKey: ['employee', employee.id] })
      toast(isEdit ? 'Employee updated.' : 'Employee added.', 'success')
      onClose()
    },
    onError: (err) => {
      toast(err?.response?.data?.detail || 'Something went wrong.', 'error')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    if (isEdit) {
      // Only send profile fields for update
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        country: form.country,
        status: parseInt(form.status),
        joining_date: form.joining_date,
      }
      if (form.department_id) payload.department_id = form.department_id
      if (form.termination_date) payload.termination_date = form.termination_date
      mutation.mutate(payload)
    } else {
      // Create includes salary fields
      mutation.mutate({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        country: form.country,
        department_id: form.department_id || null,
        joining_date: form.joining_date,
        status: parseInt(form.status),
        annual_base_salary: parseFloat(form.annual_base_salary),
        monthly_allowance: parseFloat(form.monthly_allowance) || 0,
        monthly_deduction: parseFloat(form.monthly_deduction) || 0,
        currency: form.currency,
      })
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2>{isEdit ? `Edit — ${employee.employee_code}` : 'Add New Employee'}</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={16} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">

            {/* Personal Info */}
            <div className="section-divider">Personal Info</div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">First Name *</label>
                <input required className="form-input" value={form.first_name} onChange={set('first_name')} />
              </div>
              <div className="form-group">
                <label className="form-label">Last Name *</label>
                <input required className="form-input" value={form.last_name} onChange={set('last_name')} />
              </div>
              <div className="form-group span-2">
                <label className="form-label">Email *</label>
                <input required type="email" className="form-input" value={form.email} onChange={set('email')} />
              </div>
            </div>

            {/* Role & Location */}
            <div className="section-divider" style={{ margin: '20px 0 16px' }}>Role & Location</div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Country *</label>
                <select required className="form-select" value={form.country} onChange={set('country')}>
                  <option value="">Select country</option>
                  {COUNTRIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Department</label>
                <input className="form-input" value={form.department_id} onChange={set('department_id')} placeholder="Department UUID" />
              </div>
              <div className="form-group">
                <label className="form-label">Joining Date *</label>
                <input required type="date" className="form-input" value={form.joining_date} onChange={set('joining_date')} />
              </div>
              <div className="form-group">
                <label className="form-label">Status</label>
                <select className="form-select" value={form.status} onChange={set('status')}>
                  <option value={1}>Active</option>
                  <option value={0}>Inactive</option>
                </select>
              </div>
              {isEdit && (
                <div className="form-group span-2">
                  <label className="form-label">Termination Date</label>
                  <input type="date" className="form-input" value={form.termination_date || ''} onChange={set('termination_date')} />
                </div>
              )}
            </div>

            {/* Salary (Create only) */}
            {!isEdit && (
              <>
                <div className="section-divider" style={{ margin: '20px 0 16px' }}>Initial Compensation</div>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label">Annual Base Salary *</label>
                    <input required type="number" min="0" step="0.01" className="form-input" value={form.annual_base_salary} onChange={set('annual_base_salary')} placeholder="e.g. 95000" />
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
                </div>
              </>
            )}

          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
