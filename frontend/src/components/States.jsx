export function Loading({ label = 'Tracing the graph…' }) {
  return <div className="state-block">{label}</div>
}

export function EmptyState({ title, hint }) {
  return (
    <div className="state-block">
      <div>{title}</div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  )
}

export function ErrorState({ message }) {
  return (
    <div className="state-block error">
      <div>Something went wrong.</div>
      <div className="hint">{message}</div>
    </div>
  )
}
