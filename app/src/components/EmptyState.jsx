import React from 'react'
import { Inbox } from 'lucide-react'

export default function EmptyState({ message = 'No data found.', loading = false }) {
  if (loading) {
    return (
      <div className="loading-box">
        <span className="spinner" />
        Loading…
      </div>
    )
  }

  return (
    <div className="empty-state">
      <Inbox size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
      <div>{message}</div>
    </div>
  )
}
