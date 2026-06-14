import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'X-API-Key': import.meta.env.VITE_API_KEY || '',
  },
})

// ─── Employee endpoints ───────────────────────────────────────────────────────
export const getEmployees = (params) => api.get('/employees', { params })
export const getEmployee = (id) => api.get(`/employees/${id}`)
export const createEmployee = (data) => api.post('/employees', data)
export const updateEmployee = (id, data) => api.put(`/employees/${id}`, data)
// Note: DELETE endpoint not yet implemented on backend — will return 405
export const deleteEmployee = (id) => api.delete(`/employees/${id}`)

// ─── Salary endpoints ─────────────────────────────────────────────────────────
export const getSalaryHistory = (empId) => api.get(`/employees/${empId}/salary-revisions`)
export const getCurrentSalary = (empId) => api.get(`/employees/${empId}/current-salary`)
export const createSalaryRevision = (empId, data) => api.post(`/employees/${empId}/salary-revisions`, data)

// ─── Payroll endpoints ────────────────────────────────────────────────────────
export const getPayrollRuns = (params) => api.get('/payroll/runs', { params })
export const getPayrollRunDetails = (id, params) => api.get(`/payroll/runs/${id}`, { params })
export const runPayroll = (data) => api.post('/payroll/run', data)

export default api
