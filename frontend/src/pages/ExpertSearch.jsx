import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Loading, EmptyState, ErrorState } from "../components/States";

export default function ExpertSearch() {
  const [skills, setSkills] = useState([]);
  const [people, setPeople] = useState([]);
  const [skill, setSkill] = useState("");
  const [fromPerson, setFromPerson] = useState("");
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listSkills()
      .then(setSkills)
      .catch(() => {});
    api
      .listPeople()
      .then(setPeople)
      .catch(() => {});
  }, []);

  async function search(e) {
    e?.preventDefault();
    if (!skill.trim()) return;
    setStatus("loading");
    setError("");
    try {
      const data = await api.findExperts({
        skill: skill.trim(),
        fromPerson: fromPerson || undefined,
      });
      setResults(data);
      setStatus("idle");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  return (
    <div>
      <div className="page-header">
        <span className="eyebrow">
          Query · HAS_SKILL + variable-length KNOWS traversal
        </span>
        <h1>Who actually knows this stuff?</h1>
        <p>
          Search by skill. If you tell us who you are, results are ranked by how
          close they are in the org's introduction network — not just who lists
          the skill.
        </p>
      </div>

      <form className="field-row" onSubmit={search}>
        <div className="field">
          <label htmlFor="skill">Skill</label>
          <input
            id="skill"
            list="skill-options"
            placeholder="e.g. Rust, Machine Learning, Kubernetes"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          />
          <datalist id="skill-options">
            {skills.map((s) => (
              <option key={s.name} value={s.name} />
            ))}
          </datalist>
        </div>
        <div className="field">
          <label htmlFor="from">
            You are (optional, ranks by network distance)
          </label>
          <input
            id="from"
            list="person-options"
            placeholder="Start typing your name…"
            onChange={(e) => {
              const match = people.find((p) => p.name === e.target.value);
              setFromPerson(match ? match.id : "");
            }}
          />
          <datalist id="person-options">
            {people.map((p) => (
              <option key={p.id} value={p.name} />
            ))}
          </datalist>
        </div>
        <button className="btn" type="submit" disabled={!skill.trim()}>
          Search
        </button>
      </form>

      {status === "loading" && <Loading label="Searching the skill graph…" />}
      {status === "error" && <ErrorState message={error} />}
      {status === "idle" && results && results.length === 0 && (
        <EmptyState
          title={`No one at Nimbus lists "${skill}" yet.`}
          hint="Try a broader term, like the category (e.g. “AI” or “Infra”)."
        />
      )}
      {status === "idle" && results && results.length > 0 && (
        <div className="person-list">
          {results.map((r) => (
            <Link to={`/people/${r.id}`} key={r.id} className="person-card">
              <div>
                <div className="person-name">{r.name}</div>
                <div className="person-meta">{r.title}</div>
                <span className={`chip level-${r.level}`}>
                  {r.level} · {r.years} yrs
                </span>
              </div>
              <div className="rank-stat">
                {r.hops != null
                  ? `${r.hops} hop${r.hops === 1 ? "" : "s"} away`
                  : fromPerson
                    ? "no path found"
                    : ""}
                {r.mutualConnections > 0 && (
                  <div>
                    {r.mutualConnections} mutual connection
                    {r.mutualConnections === 1 ? "" : "s"}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
