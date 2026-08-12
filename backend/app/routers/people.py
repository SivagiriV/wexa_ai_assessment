from fastapi import APIRouter, HTTPException, Query

from ..db import run_query

router = APIRouter(prefix="/api/people", tags=["people"])


@router.get("")
def list_people(q: str = Query("", description="Search by name, case-insensitive substring")):
    """Simple lookup used to populate the search/autocomplete boxes in the UI."""
    query = """
        MATCH (p:Person)
        WHERE $q = '' OR toLower(p.name) CONTAINS toLower($q)
        OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
        RETURN p.id AS id, p.name AS name, p.title AS title, c.name AS company
        ORDER BY p.name
        LIMIT 50
    """
    return run_query(query, {"q": q})


@router.get("/{person_id}")
def get_person(person_id: str):
    """Full profile: skills, team, company, and direct connections (1 hop)."""
    query = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(t:Team)
        OPTIONAL MATCH (p)-[hs:HAS_SKILL]->(s:Skill)
        WITH p, c, t, collect(DISTINCT {name: s.name, level: hs.level, years: hs.years}) AS skills
        OPTIONAL MATCH (p)-[:WORKED_ON]->(proj:Project)
        WITH p, c, t, skills, collect(DISTINCT proj.name) AS projects
        OPTIONAL MATCH (p)-[k:KNOWS]-(friend:Person)
        WITH p, c, t, skills, projects,
             collect(DISTINCT {id: friend.id, name: friend.name, strength: k.strength}) AS connections
        RETURN p.id AS id, p.name AS name, p.title AS title, p.bio AS bio,
               c.name AS company, t.name AS team, skills, projects, connections
    """
    rows = run_query(query, {"id": person_id})
    if not rows or rows[0]["id"] is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return rows[0]
