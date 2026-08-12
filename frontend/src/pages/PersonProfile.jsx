import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { Loading, ErrorState } from '../components/States'

export default function PersonProfile() {
  const { id } = useParams()
  const [person, setPerson] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    setStatus('loading')
    api
      .getPerson(id)
      .then((p) => {
        setPerson(p)
        setStatus('idle')
      })
      .catch((err) => {
        setError(err.message)
        setStatus('error')
      })
  }, [id])

  if (status === 'loading') return <Loading label="Loading profile…" />
  if (status === 'error') return <ErrorState message={error} />
  if (!person) return null

  return (
    <div>
      <div className="page-header">
        <span className="eyebrow">{person.company} · {person.team}</span>
        <h1>{person.name}</h1>
        <p>{person.title}{person.bio ? ` — ${person.bio}` : ''}</p>
        <Link className="btn secondary" to={`/path?to=${person.id}`} style={{ display: 'inline-block', marginTop: 8 }}>
          Find an introduction path to {person.name.split(' ')[0]}
        </Link>
      </div>

      <h3>Skills</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 28 }}>
        {person.skills.filter((s) => s.name).map((s) => (
          <span key={s.name} className={`chip level-${s.level}`}>
            {s.name} · {s.level} · {s.years} yrs
          </span>
        ))}
      </div>

      <h3>Projects</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 28 }}>
        {person.projects.filter(Boolean).map((p) => (
          <span key={p} className="chip">{p}</span>
        ))}
      </div>

      <h3>Direct connections ({person.connections.filter((c) => c.id).length})</h3>
      <div className="person-list">
        {person.connections.filter((c) => c.id).map((c) => (
          <Link to={`/people/${c.id}`} key={c.id} className="person-card">
            <div className="person-name">{c.name}</div>
            <div className="rank-stat">strength {c.strength}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
