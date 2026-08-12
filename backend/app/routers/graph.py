from fastapi import APIRouter, Query

from ..db import run_query

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/ego/{person_id}")
def ego_network(person_id: str, hops: int = Query(2, ge=1, le=3)):
    """Returns the local KNOWS neighborhood around a person, for the
    force-directed visualization in the frontend."""
    query = f"""
        MATCH path = (center:Person {{id: $id}})-[:KNOWS*1..{hops}]-(other:Person)
        WITH collect(DISTINCT center) + collect(DISTINCT other) AS people, collect(path) AS paths
        UNWIND people AS p
        WITH DISTINCT p, paths
        WITH collect({{id: p.id, name: p.name, title: p.title}}) AS nodes, paths
        UNWIND paths AS path
        UNWIND relationships(path) AS rel
        WITH nodes, collect(DISTINCT {{
            source: startNode(rel).id, target: endNode(rel).id, strength: rel.strength
        }}) AS links
        RETURN nodes, links
    """
    rows = run_query(query, {"id": person_id})
    if not rows:
        return {"nodes": [], "links": []}
    return rows[0]


@router.get("/teams/{team_id}/skill-gaps")
def team_skill_gaps(team_id: str):
    """
    For a given team, shows which skills used across the org's projects are
    under-represented on this specific team. Useful, and a genuinely awkward
    query relationally: it's a graph-shaped 'set difference' across two
    different traversal paths (team membership vs. project skill usage).
    """
    query = """
        MATCH (t:Team {id: $team_id})
        MATCH (proj:Project)-[:USED_SKILL]->(orgSkill:Skill)
        WITH t, collect(DISTINCT orgSkill) AS orgSkills
        MATCH (t)<-[:MEMBER_OF]-(:Person)-[:HAS_SKILL]->(teamSkill:Skill)
        WITH orgSkills, collect(DISTINCT teamSkill) AS teamSkills
        UNWIND orgSkills AS s
        WITH s, teamSkills
        WHERE NOT s IN teamSkills
        OPTIONAL MATCH (expert:Person)-[hs:HAS_SKILL]->(s)
        WITH s, expert, hs
        ORDER BY hs.level DESC
        WITH s, collect({name: expert.name, level: hs.level})[0..3] AS orgExperts
        RETURN s.name AS missingSkill, orgExperts
        ORDER BY missingSkill
    """
    return run_query(query, {"team_id": team_id})


@router.get("/teams")
def list_teams():
    query = """
        MATCH (t:Team)
        OPTIONAL MATCH (t)<-[:MEMBER_OF]-(p:Person)
        RETURN t.id AS id, t.name AS name, count(p) AS memberCount
        ORDER BY t.name
    """
    return run_query(query)
