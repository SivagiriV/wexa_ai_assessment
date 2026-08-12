import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Find an expert', end: true },
  { to: '/path', label: 'Introduction path' },
  { to: '/teams', label: 'Team skill gaps' },
]

export default function Nav() {
  return (
    <aside className="sidebar">
      <div className="wordmark">
        Skill<span className="dot">Path</span>
      </div>
      <nav className="nav-links">
        {LINKS.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.end}
            className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
          >
            {l.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        Nimbus Systems, internal graph
        <br />
        powered by CognoDB
      </div>
    </aside>
  )
}
