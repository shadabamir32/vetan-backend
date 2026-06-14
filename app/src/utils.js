// ─── Currency formatting ──────────────────────────────────────────────────────

export function fmt(n, currency = 'USD', decimals = 0) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: decimals,
    minimumFractionDigits: decimals,
  }).format(n)
}

export function fmtNum(n) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-US').format(n)
}

export function fmtM(n) {
  if (n == null) return '—'
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n}`
}


// ─── Status helpers ───────────────────────────────────────────────────────────

export const STATUS_MAP = { 1: 'Active', 0: 'Inactive' }
export const statusLabel = (code) => STATUS_MAP[code] ?? 'Unknown'
export const statusBadge = (code) => code === 1 ? 'badge-green' : 'badge-red'

export const PAYROLL_STATUS_MAP = {
  0: 'Pending',
  1: 'In Progress',
  2: 'Processed',
  4: 'Failed',
}
export const payrollStatusLabel = (code) => PAYROLL_STATUS_MAP[code] ?? 'Unknown'
export const payrollStatusBadge = (code) => {
  switch (code) {
    case 0: return 'badge-amber'
    case 1: return 'badge-blue'
    case 2: return 'badge-green'
    case 4: return 'badge-red'
    default: return 'badge-gray'
  }
}


// ─── Date helpers ─────────────────────────────────────────────────────────────

const MONTHS = [
  '', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
export const monthName = (num) => MONTHS[num] ?? ''
export const monthOptions = MONTHS.slice(1).map((name, i) => ({ value: i + 1, label: name }))

export function fmtDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export function fmtDateTime(dtStr) {
  if (!dtStr) return '—'
  return new Date(dtStr).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}


// ─── Master data (mirrors backend constants) ─────────────────────────────────

export const COUNTRY_CURRENCY = {
  'United States': 'USD',
  'United Kingdom': 'GBP',
  'Germany': 'EUR',
  'India': 'INR',
  'Canada': 'CAD',
  'Australia': 'AUD',
  'France': 'EUR',
  'Netherlands': 'EUR',
  'Singapore': 'SGD',
  'Brazil': 'BRL',
  'Mexico': 'MXN',
  'Poland': 'PLN',
  'Spain': 'EUR',
  'Sweden': 'SEK',
  'Japan': 'JPY',
}

export const COUNTRIES = Object.keys(COUNTRY_CURRENCY)
export const CURRENCIES = [...new Set(Object.values(COUNTRY_CURRENCY))]

// Hardcoded departments — same as seeded data in backend
export const DEPARTMENTS = [
  'Engineering',
  'Product',
  'Design',
  'Marketing',
  'Sales',
  'Finance',
  'Human Resources',
  'Legal',
  'Operations',
  'Customer Support',
]
