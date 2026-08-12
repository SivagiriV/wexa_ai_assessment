import random
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

SKILLS = [
    ("Python", "Languages"), ("JavaScript", "Languages"), ("TypeScript", "Languages"),
    ("Go", "Languages"), ("Rust", "Languages"), ("Java", "Languages"), ("SQL", "Languages"),
    ("React", "Frontend"), ("Vue", "Frontend"), ("CSS/Design Systems", "Frontend"),
    ("Node.js", "Backend"), ("FastAPI", "Backend"), ("Django", "Backend"), ("Spring Boot", "Backend"),
    ("PostgreSQL", "Data"), ("Neo4j/Cypher", "Data"), ("Kafka", "Data"), ("Spark", "Data"),
    ("Machine Learning", "AI"), ("NLP", "AI"), ("Computer Vision", "AI"), ("LLM Fine-tuning", "AI"),
    ("Kubernetes", "Infra"), ("Docker", "Infra"), ("AWS", "Infra"), ("Terraform", "Infra"),
    ("CI/CD", "Infra"), ("Security/AppSec", "Infra"),
    ("Product Strategy", "Product"), ("UX Research", "Product"), ("Data Visualization", "Product"),
    ("Mobile/iOS", "Mobile"), ("Mobile/Android", "Mobile"), ("React Native", "Mobile"),
    ("Technical Writing", "Other"), ("Public Speaking", "Other"), ("Mentoring", "Other"),
    ("Sales Engineering", "Other"), ("SRE/Observability", "Infra"), ("GraphQL", "Backend"),
    ("Blockchain", "Other"),
]

TEAMS = [
    "Platform Infrastructure", "Growth", "Data & AI", "Core Product", "Mobile",
    "Developer Experience", "Search & Discovery", "Security", "Design Systems", "Sales Engineering",
]

TITLES = [
    "Software Engineer", "Senior Software Engineer", "Staff Engineer", "Engineering Manager",
    "Product Manager", "Data Scientist", "ML Engineer", "Designer", "DevOps Engineer",
    "Solutions Architect", "QA Engineer", "Technical Writer",
]

PROJECT_ADJECTIVES = ["Nova", "Atlas", "Horizon", "Beacon", "Orbit", "Pulse", "Cascade", "Summit",
                       "Lumen", "Vertex", "Aurora", "Ember", "Delta", "Nimbus", "Zenith"]
PROJECT_NOUNS = ["Migration", "Redesign", "Pipeline", "Gateway", "Dashboard", "Recommender",
                  "Onboarding Flow", "Search Engine", "Billing System", "Analytics Suite"]

COMPANY_NAME = "Nimbus Systems"


def _slug(prefix, i):
    return f"{prefix}_{i:04d}"


def generate():
    skills = [{"id": _slug("skill", i), "name": name, "category": cat}
              for i, (name, cat) in enumerate(SKILLS)]
    teams = [{"id": _slug("team", i), "name": name} for i, name in enumerate(TEAMS)]
    company = {"id": "company_0000", "name": COMPANY_NAME}

    people = []
    n_people = 140
    for i in range(n_people):
        team = random.choice(teams)
        n_skills = random.randint(3, 7)
        person_skills = random.sample(skills, n_skills)
        people.append({
            "id": _slug("person", i),
            "name": fake.name(),
            "title": random.choice(TITLES),
            "bio": fake.sentence(nb_words=12),
            "team_id": team["id"],
            "skills": [
                {"skill_id": s["id"], "level": random.choice(["beginner", "intermediate", "advanced", "expert"]),
                 "years": random.randint(1, 12)}
                for s in person_skills
            ],
        })

    projects = []
    n_projects = 26
    for i in range(n_projects):
        name = f"Project {random.choice(PROJECT_ADJECTIVES)} {random.choice(PROJECT_NOUNS)}"
        members = random.sample(people, random.randint(4, 9))
        member_skill_ids = list({s["skill_id"] for m in members for s in m["skills"]})
        used_skills = random.sample(member_skill_ids, min(len(member_skill_ids), random.randint(3, 6)))
        projects.append({
            "id": _slug("project", i),
            "name": f"{name} #{i}",
            "member_ids": [m["id"] for m in members],
            "used_skill_ids": used_skills,
        })
    knows_edges = set()
    by_team = {}
    for p in people:
        by_team.setdefault(p["team_id"], []).append(p)

    for team_people in by_team.values():
        for a in team_people:
            for b in team_people:
                if a["id"] < b["id"] and random.random() < 0.35:
                    knows_edges.add((a["id"], b["id"], random.randint(1, 5)))

    # cross-team weak ties, and a few "connector" people who bridge many teams
    connectors = random.sample(people, 12)
    for c in connectors:
        others = random.sample(people, random.randint(6, 14))
        for o in others:
            if o["id"] == c["id"]:
                continue
            a, b = sorted([c["id"], o["id"]])
            knows_edges.add((a, b, random.randint(1, 3)))

    # extra random sparse ties for realism
    for _ in range(300):
        a, b = random.sample(people, 2)
        pair = tuple(sorted([a["id"], b["id"]]))
        knows_edges.add((pair[0], pair[1], random.randint(1, 3)))

    knows = [{"from_id": a, "to_id": b, "strength": s} for a, b, s in knows_edges]

    return {
        "company": company,
        "teams": teams,
        "skills": skills,
        "people": people,
        "projects": projects,
        "knows": knows,
    }
