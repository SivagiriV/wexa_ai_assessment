import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_session, close_driver  # noqa: E402
from app.config import settings  # noqa: E402
from seed.seed_data import generate  # noqa: E402


def wipe(session):
    print("Wiping existing graph...")
    session.run("MATCH (n) DETACH DELETE n")


def create_constraints(session):
    print("Creating uniqueness constraints...")
    statements = [
        "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT skill_id IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT team_id IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (proj:Project) REQUIRE proj.id IS UNIQUE",
        "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
    ]
    for stmt in statements:
        session.run(stmt)


def load(session, data):
    print(f"Loading {len(data['people'])} people, {len(data['skills'])} skills, "
          f"{len(data['teams'])} teams, {len(data['projects'])} projects, "
          f"{len(data['knows'])} KNOWS edges...")

    session.run("MERGE (c:Company {id: $id}) SET c.name = $name", data["company"])

    session.run("""
        UNWIND $teams AS t
        MERGE (team:Team {id: t.id}) SET team.name = t.name
        WITH team
        MATCH (c:Company {id: $company_id})
        MERGE (team)-[:PART_OF]->(c)
    """, {"teams": data["teams"], "company_id": data["company"]["id"]})

    session.run("""
        UNWIND $skills AS s
        MERGE (skill:Skill {id: s.id}) SET skill.name = s.name, skill.category = s.category
    """, {"skills": data["skills"]})

    session.run("""
        UNWIND $people AS p
        MERGE (person:Person {id: p.id})
        SET person.name = p.name, person.title = p.title, person.bio = p.bio
        WITH person, p
        MATCH (t:Team {id: p.team_id})
        MERGE (person)-[:MEMBER_OF]->(t)
        WITH person, p, t
        MATCH (t)-[:PART_OF]->(c:Company)
        MERGE (person)-[:WORKS_AT]->(c)
        WITH person, p
        UNWIND p.skills AS sk
        MATCH (skill:Skill {id: sk.skill_id})
        MERGE (person)-[hs:HAS_SKILL]->(skill)
        SET hs.level = sk.level, hs.years = sk.years
    """, {"people": data["people"]})

    session.run("""
        UNWIND $projects AS proj
        MERGE (p:Project {id: proj.id}) SET p.name = proj.name
        WITH p, proj
        UNWIND proj.member_ids AS pid
        MATCH (person:Person {id: pid})
        MERGE (person)-[:WORKED_ON]->(p)
        WITH p, proj
        UNWIND proj.used_skill_ids AS sid
        MATCH (skill:Skill {id: sid})
        MERGE (p)-[:USED_SKILL]->(skill)
    """, {"projects": data["projects"]})

    session.run("""
        UNWIND $knows AS k
        MATCH (a:Person {id: k.from_id}), (b:Person {id: k.to_id})
        MERGE (a)-[r:KNOWS]-(b)
        SET r.strength = k.strength
    """, {"knows": data["knows"]})

    print("Done.")


def main():
    missing = settings.validate()
    if missing:
        print(f"Missing required environment variables: {missing}. "
              f"Copy .env.example to .env and fill in your CognoDB credentials.")
        sys.exit(1)

    data = generate()
    with get_session() as session:
        if "--wipe" in sys.argv:
            wipe(session)
        create_constraints(session)
        load(session, data)
    close_driver()


if __name__ == "__main__":
    main()
