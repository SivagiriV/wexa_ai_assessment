import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function StatusBanner() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function check() {
      try {
        await api.health()
        if (!cancelled) setStatus('ok')
      } catch {
        if (!cancelled) setStatus('down')
      }
    }
    check()
    const interval = setInterval(check, 15000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  if (status !== 'down') return null

  return (
    <div className="banner" role="alert">
      <span className="pulse" aria-hidden="true" />
      Can't reach the graph database right now. Check that CognoDB is running and
      COGNODB_URI / COGNODB_PASSWORD are set correctly, then refresh.
    </div>
  )
}
