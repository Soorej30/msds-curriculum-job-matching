# MSDS Curriculum & Job Role Matching

Research project mapping the CU Boulder Master of Science in Data Science (MS-DS) curriculum against data science job market requirements.

## Live Dashboard

**[View the dashboard →](https://soorej30.github.io/msds-curriculum-job-matching/msds_dashboard.html)**

> GitHub Pages takes ~1–2 minutes to go live after the first push.

Browse all 69 MSDS courses and 100 LinkedIn job postings in one place. Filter by section, specialization, role, and more.

## Contents

| File | Description |
|---|---|
| `msds_dashboard.html` | Interactive dashboard (self-contained, no build step) |
| `cu_boulder_msds_courses.json` | 69 MSDS courses — descriptions from CU Boulder catalog |
| `linkedin_ds_jobs_20260629_142606.json` | 100 LinkedIn job postings across 7 data science roles |
| `scrape_linkedin_jobs.py` | Script used to collect LinkedIn job data |

## Data Sources

- **Courses**: [CU Boulder MS-DS Program](https://www.colorado.edu/program/data-science/) and [CU Boulder Catalog](https://catalog.colorado.edu/courses-a-z/dtsa/)
- **Jobs**: LinkedIn public jobs API (scraped June 2026), roles: Data Scientist, AI Engineer, ML Engineer, MLOps Engineer, Machine Learning Engineer, Applied Scientist, Data Science

## Setup

```bash
pip install requests beautifulsoup4 lxml
python scrape_linkedin_jobs.py
```
