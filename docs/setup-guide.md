# Setup Guide

This guide is for people who are comfortable using LLMs and editing text files, but do not want to work with the code.

The service does three main things:

1. Reads your profile and search criteria.
2. Finds suitable vacancies from known company career pages.
3. Optionally finds new company career pages that can be reviewed and added later.

## 1. Install And Configure

Install dependencies:

```bash
pip install uv
uv sync
```

Create your environment file:

```bash
cp .env.example .env
```

Fill `.env`:

```env
OPENAI_API_BASE=https://your-llm-api-endpoint
OPENAI_API_KEY=your-api-key
MODEL=your-model-name
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
TELEGRAM_ALLOWED_USERS=
MIN_SCORE=70
```

Notes:

- `OPENAI_API_BASE`, `OPENAI_API_KEY`, and `MODEL` connect the service to your LLM provider.
- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` let the service send vacancy and candidate notifications.
- `MIN_SCORE` controls which vacancies are good enough to send for approval.

## 2. Fill Your Profile Files

Profile files live in `knowledge/profile/`.

Fill them with real information. The agents use these files to decide whether a company or vacancy fits you and to prepare application materials.

| File | What to add |
| --- | --- |
| `knowledge/profile/general-info.md` | Name, location, email, languages, education, certificates, links. |
| `knowledge/profile/profile-summary.md` | Short career summary: who you are, what you specialize in, strongest achievements. |
| `knowledge/profile/work-experience.md` | Jobs, dates, industries, responsibilities, measurable results. |
| `knowledge/profile/personal-projects.md` | Side projects, open-source work, links, tech stack, outcomes. |
| `knowledge/profile/values-and-interests.md` | Topics, industries, values, work style, company traits you care about. |
| `knowledge/profile/public-performance.md` | Talks, publications, community activity, public proof. |

Use plain language. You do not need a special format, but bullet points with numbers and concrete examples work best.

## 3. Fill Your Search Criteria

Edit:

```text
knowledge/search-criteria.md
```

Use this file to describe what jobs should be considered suitable.

Include:

- Target role names.
- Seniority levels.
- Preferred locations or remote rules.
- Preferred industries.
- Hard exclusions.
- Any salary, timezone, language, or visa constraints.

Example:

```markdown
## Role

Primary target: Senior Product Manager.

Acceptable variations:
- Product Manager
- AI Product Manager
- Crypto Product Manager
- Lead Product Manager

## Location

Prefer remote Europe, EMEA, global remote, or Portugal.
Exclude US-only and Canada-only remote roles.

## Industries

Priority:
1. FinTech
2. AI
3. Crypto/Web3
4. B2B SaaS
```

## 4. Add Known Companies

Edit:

```text
knowledge/companies.csv
```

This is the list of companies whose career pages are already known. Vacancy discovery reads this file.

Format:

```csv
Company,Career page
Example Company,https://example.com/careers
Another Company,https://jobs.ashbyhq.com/another-company
```

Use one row per company.

Good career page URLs usually look like:

- `https://jobs.ashbyhq.com/company`
- `https://job-boards.greenhouse.io/company`
- `https://jobs.lever.co/company`
- `https://jobs.personio.com/company`
- `https://company.com/careers`

Do not put generated company candidates directly into this file unless you have reviewed them.

## 5. Configure Company Sourcing Queries

Edit:

```text
knowledge/company-source-queries.yaml
```

This file controls how the company sourcing crew searches for new company career pages.

It does not store your profile. It stores reusable search templates and ATS domains.

Useful fields:

```yaml
source_groups:
  ats_search:
    enabled: true
    domains:
      - "jobs.ashbyhq.com"
      - "job-boards.greenhouse.io"
      - "jobs.lever.co"

  web_search:
    enabled: true
    templates:
      - "{role} {seniority} {industry} remote Europe"
      - "{role} {seniority} {industry} remote EMEA"
      - "site:{domain} {role} {industry} remote"
```

Supported template variables:

- `{role}`
- `{seniority}`
- `{industry}`
- `{domain}`

The crew reads `search-criteria.md` and profile files, decides which roles/seniorities/industries to use, then fills these templates.

## 6. Run The Service

Start the Telegram bot in one terminal:

```bash
uv run job_hunting_bot
```

Run vacancy discovery in another terminal:

```bash
uv run job_hunting_discover
```

Use this when you already have companies in `knowledge/companies.csv` and want to find matching vacancies.

Run company sourcing:

```bash
uv run job_hunting_source_companies
```

Use this when you want to find new companies and career pages. This writes candidates to:

```text
data/<YYYY-MM-DD>/company_candidates.csv
```

It does not modify `knowledge/companies.csv`.

Run the advisor UI:

```bash
uv run job_hunting_advisor
```

Use this when you want to chat with the local career advisor interface.

## 7. Review Outputs

Generated data is stored under `data/`.

Important paths:

| Path | Meaning |
| --- | --- |
| `data/<YYYY-MM-DD>/vacancies/*.json` | Vacancies found from known companies. |
| `data/<YYYY-MM-DD>/scores/*.json` | Fit scores for vacancies. |
| `data/<YYYY-MM-DD>/applications/<vacancy_id>/` | Generated application assets. |
| `data/<YYYY-MM-DD>/company_candidates.csv` | New company career-page candidates for review. |

When company candidates look good, manually copy reviewed companies into `knowledge/companies.csv`.

## 8. Suggested Routine

Daily or every few hours:

```bash
uv run job_hunting_discover
```

Weekly or when you want more sources:

```bash
uv run job_hunting_source_companies
```

Always keep the bot running if you want Telegram approvals and notifications:

```bash
uv run job_hunting_bot
```

## Troubleshooting

If nothing is found:

- Check that `knowledge/companies.csv` has valid career page URLs.
- Check that `knowledge/search-criteria.md` is not too restrictive.
- Check that `.env` contains valid LLM and Telegram settings.

If company sourcing finds irrelevant companies:

- Make `knowledge/search-criteria.md` more specific.
- Edit `knowledge/company-source-queries.yaml` to remove broad templates.
- Add clearer industries and exclusions.

If Telegram does not work:

- Check `TELEGRAM_BOT_TOKEN`.
- Check `TELEGRAM_CHAT_ID`.
- Start the bot with `uv run job_hunting_bot`.
