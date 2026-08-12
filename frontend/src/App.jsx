import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav'
import StatusBanner from './components/StatusBanner'
import ExpertSearch from './pages/ExpertSearch'
import PersonProfile from './pages/PersonProfile'
import PathFinder from './pages/PathFinder'
import TeamGaps from './pages/TeamGaps'

export default function App() {
  return (
    <div className="app-shell">
      <Nav />
      <div>
        <StatusBanner />
        <main className="main">
          <Routes>
            <Route path="/" element={<ExpertSearch />} />
            <Route path="/people/:id" element={<PersonProfile />} />
            <Route path="/path" element={<PathFinder />} />
            <Route path="/teams" element={<TeamGaps />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
