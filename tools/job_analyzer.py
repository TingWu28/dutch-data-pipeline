#!/usr/bin/env python3
"""
Job Description Analyzer
Compares a job description against Ting's profile and outputs a gap/fit report.
Usage: python job_analyzer.py
"""
import anthropic
import json
import sys
from datetime import datetime
from pathlib import Path

CANDIDATE_PROFILE = """
Name: Ting Wu
Target Role: Data Engineer / Analytics Engineer (NOT Junior — 5+ years professional experience)
Location: Den Bosch, Netherlands (no relocation needed, 2 years in NL)
Available: Graduation Aug 2026 (part-time possible before)

Recent Experience:
- Data Engineering Intern, ASML R&R Dept – SSA Project (Sep 2025 – Feb 2026, Eindhoven)
  * Deployed Databricks workspace for team self-service analytics
  * Built AI-powered NL-to-SQL layer so non-technical colleagues could query in plain English
  * Delivered dashboards and trained colleagues on Databricks workflows

- Senior Data Analyst, Meetsocial Co. (Oct 2018 – Sep 2023, Shanghai)
  * BI dashboards for 5+ departments (Tableau, Power BI, SQL)
  * Python/Excel attribution analysis, 20% campaign efficiency improvement
  * Automated reporting pipelines, 40% turnaround reduction

Education:
- MSc Data Science & AI, TU/e Eindhoven (2024–2026, expected)
- Pre-Master Data Science in Business, JADS (2024)

Technical Skills (current):
- Python: intermediate (notebooks, data analysis, ML — building engineer-level skills)
- SQL: intermediate (CRUD, joins, aggregations — learning window functions/CTEs)
- Databricks: hands-on (ASML internship)
- Cloud: Google Cloud Platform (CI/CD project), learning Azure
- BI: Tableau, Power BI (professional)
- DevOps: Docker, GitHub Actions
- ML/AI: PyTorch, scikit-learn, LLM prompting

Currently Learning (April–July 2026 roadmap):
- Weeks 1–2: Advanced SQL + Python as engineer
- Weeks 3–4: dbt
- Weeks 5–6: Airflow
- Weeks 7–8: Azure (ADF, ADLS)
- Week 9: LLM/AI pipeline integration

Languages: Chinese (native), English (IELTS 7), Japanese (JLPT-2), Dutch (A0, actively learning)
"""

SYSTEM_PROMPT = f"""You are a career advisor specialized in the Dutch data engineering job market (Amsterdam, Utrecht, Eindhoven, Rotterdam).
You help a candidate evaluate job fit objectively and honestly — do not inflate scores.

Candidate Profile:
{CANDIDATE_PROFILE}

Evaluate fit realistically. The candidate has strong analytical and professional experience but is transitioning
into modern DE tooling (dbt, Airflow, Azure). ASML and TU/e are strong credentials in the Dutch market.
Return only valid JSON — no markdown fences, no text outside the JSON object."""


def analyze_job(job_description: str) -> dict:
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this job description for candidate fit.

Job Description:
{job_description}

Return a JSON object with exactly these fields:
{{
  "job_title": "extracted job title",
  "company": "extracted company name or null",
  "match_score": 0-100,
  "apply_now": true or false,
  "apply_when": "now / after week X of training / not recommended",
  "matched_skills": ["skill already matched"],
  "skill_gaps": [
    {{"skill": "dbt", "priority": "critical|important|nice-to-have", "weeks_to_learn": 2}}
  ],
  "strengths_for_this_role": ["specific strength relevant to this role"],
  "recommendation": "2-3 sentence honest assessment"
}}""",
            }
        ],
    )

    return json.loads(response.content[0].text)


def print_report(result: dict) -> None:
    score = result.get("match_score", 0)
    filled = score // 10
    bar = "█" * filled + "░" * (10 - filled)

    print("\n" + "=" * 54)
    print("  JOB FIT REPORT")
    print("=" * 54)
    print(f"  Role    : {result.get('job_title', 'Unknown')}")
    company = result.get("company")
    if company:
        print(f"  Company : {company}")
    print(f"\n  Score   : [{bar}] {score}/100")
    apply = result.get("apply_now")
    when = result.get("apply_when", "")
    print(f"  Apply   : {'✓ Yes' if apply else '✗ Not yet'}  —  {when}")

    strengths = result.get("strengths_for_this_role", [])
    if strengths:
        print("\n  Strengths for this role:")
        for s in strengths:
            print(f"    + {s}")

    gaps = result.get("skill_gaps", [])
    if gaps:
        print("\n  Skill Gaps:")
        for gap in gaps:
            priority = gap.get("priority", "").upper()
            weeks = gap.get("weeks_to_learn", "?")
            skill = gap.get("skill", "")
            print(f"    [{priority:<14}] {skill}  (~{weeks}w)")

    matched = result.get("matched_skills", [])
    if matched:
        print(f"\n  Matched : {', '.join(matched)}")

    print(f"\n  Verdict :")
    rec = result.get("recommendation", "")
    for line in [rec[i : i + 70] for i in range(0, len(rec), 70)]:
        print(f"  {line}")

    print("=" * 54 + "\n")


def save_to_log(result: dict) -> None:
    log_path = Path(__file__).parent.parent / "progress.json"
    try:
        with open(log_path) as f:
            progress = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        progress = {}

    if "job_analyses" not in progress:
        progress["job_analyses"] = []

    progress["job_analyses"].append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "job_title": result.get("job_title"),
            "company": result.get("company"),
            "match_score": result.get("match_score"),
            "apply_now": result.get("apply_now"),
            "apply_when": result.get("apply_when"),
        }
    )

    with open(log_path, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"  Logged to progress.json\n")


def get_job_description() -> str:
    print("Job Description Analyzer")
    print("─" * 40)
    print("Paste the job description below.")
    print("Press Enter twice when done:\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def main():
    job_description = get_job_description()

    if not job_description:
        print("Error: no job description provided.")
        sys.exit(1)

    print("\nAnalyzing...\n")

    try:
        result = analyze_job(job_description)
        print_report(result)
        save_to_log(result)
    except json.JSONDecodeError:
        print("Error: could not parse API response. Try again.")
        sys.exit(1)
    except anthropic.APIError as e:
        print(f"API Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
