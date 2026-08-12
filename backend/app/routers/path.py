from fastapi import APIRouter, HTTPException, Query

from ..db import run_query

router = APIRouter(prefix="/api/path", tags=["path"])


@router.get("")
def introduction_path(
    from_id: str = Query(..., description="Person id you are starting from"),
    to_id: str = Query(..., description="Person id you want an introduction to"),
    max_hops: int = Query(6, ge=1, le=8),
):
    """
    Shortest chain of introductions connecting two people, e.g.
    'You -> Priya -> Marcus -> the Rust expert you actually wanted to reach'.

    This is the canonical multi-hop query: recursive/variable-length path
    finding like this requires recursive CTEs (or app-side BFS) in a
    relational database and gets expensive fast; here it's one shortestPath
    call over the KNOWS relationship.
    """
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="from_id and to_id must differ")

    query = f"""
        MATCH (a:Person {{id: $from_id}}), (b:Person {{id: $to_id}})
        MATCH path = shortestPath((a)-[:KNOWS*1..{max_hops}]-(b))
        RETURN [n IN nodes(path) | {{id: n.id, name: n.name, title: n.title}}] AS people,
               [r IN relationships(path) | r.strength] AS linkStrengths,
               length(path) AS hops
    """
    rows = run_query(query, {"from_id": from_id, "to_id": to_id})
    if not rows:
        return {"found": False, "people": [], "linkStrengths": [], "hops": None}
    return {"found": True, **rows[0]}
