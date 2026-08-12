# SkillPath

**Find the expert. Find the path to them.**

SkillPath is an internal tool for a (fictional) company, Nimbus Systems, that answers two
questions people-search tools are usually bad at:

1. _"Who here actually knows Rust?"_ — ranked not just by who lists the skill, but by how
   reachable they are through the internal social network.
2. _"How do I get an introduction to them?"_ — the shortest chain of people who can vouch
   for you along the way.

It's backed by **CognoDB**, a managed graph database, via the official Neo4j Python driver.

---

## Why a graph database?

Nimbus's own data — people, skills, teams, projects, and who-knows-whom — is naturally a
graph: the interesting questions are about _paths and connections_, not rows.

- **"Who can introduce me to the person I want to reach?"** is a shortest-path query over a
  variable number of hops. In Postgres this means a recursive CTE that self-joins a
  `connections` table N times, gets slower as the chain grows, and needs a hard-coded hop
  limit to stay safe. In Cypher it's one line: `shortestPath((a)-[:KNOWS*1..6]-(b))`.
- **"Rank experts by network closeness and mutual connections"** combines a property filter
  (has the skill) with a graph traversal (how far away, through how many mutual friends) in
  a single pass. Relationally this is several joins plus app-side graph logic, or a stored
  procedure that re-implements BFS.
- **"What skills does this team lack, relative to what the org's projects actually use?"**
  is a set difference computed across two different traversal paths (team membership vs.
  project skill usage) starting from the same skill nodes — awkward to express declaratively
  in SQL without a CTE per traversal direction.
- The schema also **grows painlessly**: adding a new relationship type (e.g. `MENTORED_BY`)
  never requires a migration or a new join table, just a new edge type.

None of this data is _huge_ — that's the point. The size isn't why it's a graph problem; the
shape of the questions is.

---

## Data model

```
                    ┌──────────┐
                    │ Company  │
                    └────┬─────┘
                         │ PART_OF
                    ┌────┴─────┐
                    │  Team    │
                    └────┬─────┘
                         │ MEMBER_OF
        ┌────────────────┴────────────────┐
        │              Person              │──KNOWS──▶ Person   (weighted, undirected in practice)
        └───┬────────────────┬─────────────┘
            │ HAS_SKILL       │ WORKED_ON
      {level, years}          ▼
            ▼            ┌─────────┐
       ┌─────────┐       │ Project │
       │  Skill  │◀──────┘ USED_SKILL
       └─────────┘
```

| Node      | Key properties       |
| --------- | -------------------- |
| `Person`  | id, name, title, bio |
| `Skill`   | id, name, category   |
| `Team`    | id, name             |
| `Project` | id, name             |
| `Company` | id, name             |

| Relationship                         | Direction                     | Properties       |
| ------------------------------------ | ----------------------------- | ---------------- |
| `(:Person)-[:KNOWS]-(:Person)`       | undirected (MERGEd both ways) | `strength` (1–5) |
| `(:Person)-[:HAS_SKILL]->(:Skill)`   | Person → Skill                | `level`, `years` |
| `(:Person)-[:WORKED_ON]->(:Project)` | Person → Project              | —                |
| `(:Project)-[:USED_SKILL]->(:Skill)` | Project → Skill               | —                |
| `(:Person)-[:MEMBER_OF]->(:Team)`    | Person → Team                 | —                |
| `(:Person)-[:WORKS_AT]->(:Company)`  | Person → Company              | —                |
| `(:Team)-[:PART_OF]->(:Company)`     | Team → Company                | —                |

Seed data: ~140 people, 41 skills, 10 teams, 26 projects, and ~700+ `KNOWS` edges
generated with denser ties inside teams and sparser cross-team "connector" ties — so
cross-team introduction paths are meaningful rather than trivial.

---

## Main queries (see `backend/app/routers/`)

**1. Expert search, ranked by network closeness** (`experts.py`) — multi-hop, and the
query relational databases handle worst:

```cypher
MATCH (target:Person)-[hs:HAS_SKILL]->(s:Skill) WHERE toLower(s.name) = toLower($skill)
MATCH (me:Person {id: $from_person})
OPTIONAL MATCH path = shortestPath((me)-[:KNOWS*1..3]-(target))
OPTIONAL MATCH (me)-[:KNOWS]-(mutual:Person)-[:KNOWS]-(target)
RETURN target.name, hs.level, length(path) AS hops, count(DISTINCT mutual) AS mutualConnections
ORDER BY hops ASC, mutualConnections DESC
```

**2. Introduction path** (`path.py`) — variable-length shortest path, 2+ hops in practice
for most cross-team pairs:

```cypher
MATCH (a:Person {id: $from_id}), (b:Person {id: $to_id})
MATCH path = shortestPath((a)-[:KNOWS*1..6]-(b))
RETURN [n IN nodes(path) | n.name] AS chain, length(path) AS hops
```

**3. Team skill gaps** (`graph.py`) — graph set-difference across two traversal paths:

```cypher
MATCH (proj:Project)-[:USED_SKILL]->(orgSkill:Skill)
WITH collect(DISTINCT orgSkill) AS orgSkills
MATCH (t:Team {id: $team_id})<-[:MEMBER_OF]-(:Person)-[:HAS_SKILL]->(teamSkill:Skill)
WITH orgSkills, collect(DISTINCT teamSkill) AS teamSkills
UNWIND orgSkills AS s WHERE NOT s IN teamSkills
RETURN s.name
```

All queries in the codebase are parameterised through the Neo4j driver (`session.run(query,
params)`) — no string concatenation of user input into Cypher anywhere.

---

## Project structure

```
skillpath/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, health check
│   │   ├── db.py            # Neo4j driver wrapper, connection error handling
│   │   ├── config.py        # env-var based settings
│   │   └── routers/
│   │       ├── people.py    # search, profile
│   │       ├── experts.py   # skill search + ranking
│   │       ├── path.py      # introduction path
│   │       └── graph.py     # ego network, team skill gaps
│   ├── seed/
│   │   ├── seed_data.py     # synthetic data generator
│   │   └── seed.py          # loads data into CognoDB
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── pages/            # ExpertSearch, PersonProfile, PathFinder, TeamGaps
    │   ├── components/       # Nav, StatusBanner, States
    │   └── api/client.js     # fetch wrapper
    └── .env.example
```

---

## Setup & run

### 1. Create your CognoDB instance

1. Sign up at [console.cognodb.com/signup](https://console.cognodb.com/signup) (free, no
   card required).
2. Create a free `c0` instance and pick a region — provisions in under a minute.
3. Copy the connection URI (`bolt+s://<instance-id>.databases.cognodb.cloud`) and the
   generated password for user `cognodb`. **The password is shown once** — save it now.

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env: paste your COGNODB_URI and COGNODB_PASSWORD

python -m seed.seed          # loads ~140 people + the rest of the graph
# python -m seed.seed --wipe # re-run with --wipe to reset first

python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` — should return `{"status": "ok", ...}`.
Interactive API docs: `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000, edit if backend runs elsewhere
npm run dev
```

Visit `http://localhost:5173`.

### 4. What "graceful error handling" looks like here

If the backend can't reach CognoDB (wrong password, instance paused, network issue), every
API call returns a clear 503 instead of crashing, and `/api/health` reports the specific
cause. The frontend polls `/api/health` and shows a persistent banner rather than failing
silently or throwing a raw error at the user.

---

## Deployment

- **Backend**: any Python host works (Render, Railway, Fly.io). Set `COGNODB_URI`,
  `COGNODB_PASSWORD`, and `CORS_ORIGINS` (your deployed frontend URL) as environment
  variables — never commit `.env`.
- **Frontend**: any static host (Vercel, Netlify, Cloudflare Pages). Build with
  `npm run build`, set `VITE_API_URL` to your deployed backend URL.

Backend deployed in render - https://wexa-ai-assessment.onrender.com
swagger url for API - https://wexa-ai-assessment.onrender.com/docs
Frontend deployed in render - https://wexa-ai-assessment-1.onrender.com
