const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`)
  } catch (err) {
    throw new Error('Could not reach the SkillPath API. Is the backend running?')
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      detail = body.detail || body.message || detail
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  listPeople: (q = '') => request(`/api/people?q=${encodeURIComponent(q)}`),
  getPerson: (id) => request(`/api/people/${id}`),
  listSkills: (q = '') => request(`/api/experts/skills?q=${encodeURIComponent(q)}`),
  findExperts: ({ skill, fromPerson, maxHops = 3 }) => {
    const params = new URLSearchParams({ skill, max_hops: String(maxHops) })
    if (fromPerson) params.set('from_person', fromPerson)
    return request(`/api/experts?${params.toString()}`)
  },
  findPath: ({ fromId, toId, maxHops = 6 }) =>
    request(`/api/path?from_id=${fromId}&to_id=${toId}&max_hops=${maxHops}`),
  listTeams: () => request('/api/graph/teams'),
  teamSkillGaps: (teamId) => request(`/api/graph/teams/${teamId}/skill-gaps`),
}
