import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Loading, EmptyState, ErrorState } from "../components/States";

export default function TeamGaps() {
  const [teams, setTeams] = useState([]);
  const [teamId, setTeamId] = useState("");
  const [gaps, setGaps] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listTeams()
      .then((t) => {
        setTeams(t);
        if (t.length) setTeamId(t[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!teamId) return;
    setStatus("loading");
    api
      .teamSkillGaps(teamId)
      .then((g) => {
        setGaps(g);
        setStatus("idle");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, [teamId]);

  return (
    <div>
      <div className="page-header">
        <span className="eyebrow">
          Query · graph set-difference across two traversal paths
        </span>
        <h1>What is this team missing?</h1>
        <p>
          Skills used across the company's projects that nobody on this team
          currently has — with the org's top expert in each, in case you need to
          borrow one.
        </p>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="team">Team</label>
          <select
            id="team"
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
          >
            {teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.memberCount})
              </option>
            ))}
          </select>
        </div>
      </div>

      {status === "loading" && <Loading label="Comparing skill sets…" />}
      {status === "error" && <ErrorState message={error} />}
      {status === "idle" && gaps && gaps.length === 0 && (
        <EmptyState
          title="No gaps found."
          hint="This team covers every skill used across active projects."
        />
      )}
      {status === "idle" && gaps && gaps.length > 0 && (
        <div className="person-list">
          {gaps.map((g) => (
            <div className="person-card" key={g.missingSkill}>
              <div className="person-name">{g.missingSkill}</div>
              <div className="rank-stat">
                {g.orgExperts.filter((e) => e.name).length
                  ? g.orgExperts
                      .filter((e) => e.name)
                      .map((e) => e.name)
                      .join(", ")
                  : "no one at Nimbus has this yet"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
