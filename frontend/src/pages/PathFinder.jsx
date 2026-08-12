import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { Loading, EmptyState, ErrorState } from "../components/States";

export default function PathFinder() {
  const [searchParams] = useSearchParams();
  const [people, setPeople] = useState([]);
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState(searchParams.get("to") || "");
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listPeople()
      .then(setPeople)
      .catch(() => {});
  }, []);

  const nameFor = (id) => people.find((p) => p.id === id)?.name || "";

  async function search(e) {
    e?.preventDefault();
    if (!fromId || !toId) return;
    setStatus("loading");
    setError("");
    try {
      const data = await api.findPath({ fromId, toId });
      setResult(data);
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
          Query · shortestPath((a)-[:KNOWS*1..6]-(b))
        </span>
        <h1>How do I get an introduction?</h1>
        <p>
          Pick two people and we'll trace the shortest chain of introductions
          between them through the KNOWS network — the query a relational schema
          handles poorly.
        </p>
      </div>

      <form className="field-row" onSubmit={search}>
        <div className="field">
          <label htmlFor="from">From</label>
          <input
            id="from"
            list="people-a"
            placeholder="Your name…"
            defaultValue={nameFor(fromId)}
            onChange={(e) => {
              const match = people.find((p) => p.name === e.target.value);
              setFromId(match ? match.id : "");
            }}
          />
          <datalist id="people-a">
            {people.map((p) => (
              <option key={p.id} value={p.name} />
            ))}
          </datalist>
        </div>
        <div className="field">
          <label htmlFor="to">To</label>
          <input
            id="to"
            list="people-b"
            placeholder="Who you want to reach…"
            defaultValue={nameFor(toId)}
            onChange={(e) => {
              const match = people.find((p) => p.name === e.target.value);
              setToId(match ? match.id : "");
            }}
          />
          <datalist id="people-b">
            {people.map((p) => (
              <option key={p.id} value={p.name} />
            ))}
          </datalist>
        </div>
        <button className="btn" type="submit" disabled={!fromId || !toId}>
          Trace path
        </button>
      </form>

      {status === "loading" && <Loading label="Following the thread…" />}
      {status === "error" && <ErrorState message={error} />}
      {status === "idle" && result && !result.found && (
        <EmptyState
          title="No path found within 6 hops."
          hint="These two people aren't connected closely enough in the current graph."
        />
      )}
      {status === "idle" && result && result.found && (
        <div className="card">
          <div className="eyebrow">
            {result.hops} hop{result.hops === 1 ? "" : "s"}
          </div>
          <div className="thread-chain">
            {result.people.map((p, i) => (
              <div style={{ display: "contents" }} key={p.id}>
                <div className="thread-node">
                  <div className="thread-pin" />
                  <Link to={`/people/${p.id}`} className="name">
                    {p.name}
                  </Link>
                  <div className="title">{p.title}</div>
                </div>
                {i < result.people.length - 1 && (
                  <div className="thread-link">
                    <span className="strength">
                      strength {result.linkStrengths[i]}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
