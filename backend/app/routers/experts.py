from fastapi import APIRouter, Query

from ..db import run_query

router = APIRouter(prefix="/api/experts", tags=["experts"])


@router.get("")
def find_experts(
    skill: str = Query(..., description="Skill name to search for"),
    from_person: str | None = Query(None, description="Optional person id to rank by network closeness"),
    max_hops: int = Query(3, ge=1, le=5),
):
    """
    Finds people with a given skill, ranked so the most 'reachable' experts
    (fewest hops through the KNOWS network, most mutual connections) surface
    first. This is the query a relational database would find awkward:
    it combines a property filter with a variable-length graph traversal
    and a mutual-connection count in a single pass.
    """
    if from_person:
        query = f"""
            MATCH (target:Person)-[hs:HAS_SKILL]->(s:Skill)
            WHERE toLower(s.name) = toLower($skill)
            MATCH (me:Person {{id: $from_person}})
            OPTIONAL MATCH path = shortestPath((me)-[:KNOWS*1..{max_hops}]-(target))
            WITH target, hs, path
            WHERE target.id <> $from_person
            OPTIONAL MATCH (me:Person {{id: $from_person}})-[:KNOWS]-(mutual:Person)-[:KNOWS]-(target)
            RETURN target.id AS id, target.name AS name, target.title AS title,
                   hs.level AS level, hs.years AS years,
                   CASE WHEN path IS NULL THEN null ELSE length(path) END AS hops,
                   count(DISTINCT mutual) AS mutualConnections
            ORDER BY hops IS NULL, hops ASC, mutualConnections DESC, hs.level DESC
            LIMIT 25
        """
        return run_query(query, {"skill": skill, "from_person": from_person})
    else:
        query = """
            MATCH (target:Person)-[hs:HAS_SKILL]->(s:Skill)
            WHERE toLower(s.name) = toLower($skill)
            RETURN target.id AS id, target.name AS name, target.title AS title,
                   hs.level AS level, hs.years AS years,
                   null AS hops, 0 AS mutualConnections
            ORDER BY hs.level DESC, hs.years DESC
            LIMIT 25
        """
        return run_query(query, {"skill": skill})


@router.get("/skills")
def list_skills(q: str = Query("", description="Filter skill names, for autocomplete")):
    query = """
        MATCH (s:Skill)
        WHERE $q = '' OR toLower(s.name) CONTAINS toLower($q)
        OPTIONAL MATCH (:Person)-[:HAS_SKILL]->(s)
        WITH s, count(*) AS peopleCount
        RETURN s.name AS name, s.category AS category, peopleCount
        ORDER BY peopleCount DESC
        LIMIT 100
    """
    return run_query(query, {"q": q})
