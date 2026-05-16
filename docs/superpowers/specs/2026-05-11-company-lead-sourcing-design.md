# Company Lead Sourcing Design Spec

**Date:** 2026-05-11
**Status:** Pending user review

> Archival note: this design spec predates the structured YAML profile section
> migration. References below to Markdown profile files are historical context;
> current company sourcing instructions read `knowledge/profile.yaml` and its
> allowlisted YAML `profile_sections`.

## Objective

Add a separate company lead sourcing capability that discovers new relevant companies and career pages from public/free sources, stores reviewable candidates under `data/`, and notifies the user in Telegram that new candidates are ready to review.

This feature expands the company input surface for vacancy discovery without changing or merging into the curated `knowledge/companies.csv` workflow.

## Scope

The new flow finds companies, not applications. It does not generate CVs, cover letters, or application answers. It does not automatically apply to jobs.

In scope:

- Discover new companies likely to match the user's profile, interests, values, and search criteria.
- Resolve each company website and career page.
- Score and explain company fit.
- Write candidates to a generated CSV under `data/<YYYY-MM-DD>/`.
- Send a Telegram notification when new candidates are available for review.
- Keep generated candidates separate from `knowledge/companies.csv`.

Out of scope for the first version:

- Telegram approve/decline buttons for company candidates.
- Automatic merging into `knowledge/companies.csv`.
- Always-on or real-time monitoring.
- Paid API integrations.
- Broad web crawling.

## Architecture

Add a cron-runnable Company Sourcing Flow and Crew alongside the existing discovery and application flows.

Entry point:

```text
job_hunting_source_companies
```

Source layout:

```text
src/job_hunting/
├── flows/
│   └── company_sourcing_flow.py
├── crews/
│   └── company_sourcing/
│       ├── crew.py
│       └── config/
│           ├── agents.yaml
│           └── tasks.yaml
└── tools/
    ├── company_search_tool.py
    ├── career_page_resolver.py
    └── company_candidate_writer.py
```

The existing discovery flow remains responsible for parsing career pages and scoring vacancies. The new sourcing flow only produces reviewable company candidates.

## Source Strategy

The sourcing crew must not crawl the whole internet. It uses bounded, explicit source definitions.

Create a managed query config file:

```text
knowledge/company-source-queries.yaml
```

The file stores public/free source groups:

```yaml
source_groups:
  ats_search:
    enabled: true
    domains:
      - jobs.ashbyhq.com
      - job-boards.greenhouse.io
      - jobs.lever.co
      - jobs.personio.com
      - apply.workable.com
      - bamboohr.com/careers

  web_search:
    enabled: true
    templates:
      - "{role} remote {industry} careers"
      - "{seniority} product manager {industry} Europe remote"
      - "{industry} startups hiring product manager remote"
      - "site:{domain} \"Product Manager\" \"Remote\" \"{industry}\""
```

The crew expands templates from:

- `knowledge/search-criteria.md`
- `knowledge/profile/profile-summary.md`
- `knowledge/profile/values-and-interests.md`
- other profile files when useful

Initial query execution can use a public-search adapter. The design should hide this behind a small `CompanyLeadSource` interface so a later search API or aggregator API can be added without changing the crew contract.

## Crew Responsibilities

### Source Planner

Reads `search-criteria.md`, profile, and `company-source-queries.yaml`. Produces a bounded list of search queries for the current run.

### Company Researcher

Executes the planned searches, extracts candidate companies and source URLs, and owns deduplication before any downstream resolution or scoring work.

The Company Researcher skips companies that are already present in:

- the current run's in-memory candidates
- earlier `data/*/company_candidates.csv` files
- `knowledge/companies.csv`

This prevents the new sourcing crew from re-adding companies already known to the curated or generated lead pools.

### Career Page Resolver

Finds a company website and career page. It accepts direct ATS URLs when search results already point to a supported ATS board.

### Fit Analyst

Fetches lightweight public company information, such as homepage/about/careers text, and evaluates whether the company fits the user's industries, interests, values, seniority direction, and remote/location preferences.

### Candidate Writer

Writes reviewable rows to the generated candidate CSV.

## Candidate CSV Contract

Generated candidates are stored under the discovery date:

```text
data/<YYYY-MM-DD>/company_candidates.csv
```

Schema:

```csv
company,career_page,website,source,industry,match_score,match_reason,status,discovered_at
```

Statuses:

- `pending_review` — default for all first-version candidates.
- `approved` — manually set by the user after reviewing the CSV.
- `declined` — manually set by the user to prevent future use.

The first version does not auto-approve candidates. This avoids spending discovery work on companies the user does not want to target.

Rows with `status=approved` can later be adapted into the existing two-column discovery format:

```csv
Company,Career page
Ramp,https://ramp.com/careers
```

## Telegram Notification

After the sourcing run finishes, send one Telegram notification if new `pending_review` candidates were written.

Example:

```text
12 new company candidates found.
Review data/2026-05-11/company_candidates.csv and set status=approved for companies you want discovery to monitor.
```

The notification is informational only. It has no inline approval buttons in the first version.

## Data Flow

```text
search criteria + profile + query config
  -> Source Planner
  -> public/free source queries
  -> Company Researcher
  -> company candidates
  -> Career Page Resolver
  -> Fit Analyst
  -> data/<date>/company_candidates.csv
  -> Telegram review notification
```

The existing discovery crew can later read approved candidate rows through a separate adapter. That adapter should not mutate `knowledge/companies.csv`.

## Deduplication

Deduplication is owned by the Company Researcher agent.

Deduplicate candidates by normalized company name, website domain, and career page URL.

The first version should check:

- the current run's candidate rows
- earlier `data/*/company_candidates.csv` files
- `knowledge/companies.csv`

If a candidate is already known, skip it. The first version should not update existing candidate rows or re-add known companies with alternate source evidence.

## Error Handling

- If a search source fails, continue with remaining source groups and record the source error in logs.
- If a company website cannot be resolved, skip the candidate.
- If a career page cannot be resolved, include the candidate only when there is strong company fit and enough evidence to review manually.
- If Telegram notification fails, still keep the generated CSV and log the notification failure.
- If the query config is missing or invalid, fail the sourcing run early with a clear error.

## Testing

Add focused tests for:

- Query template expansion from search criteria/profile inputs.
- Candidate CSV writing and status defaults.
- Deduplication against existing candidates and `knowledge/companies.csv`.
- Approved-row export to the existing `Company,Career page` shape if the adapter is implemented in the same phase.
- Telegram notification message formatting.

Use fake source responses in tests. Do not rely on live search engine results for automated tests.

## Implementation Notes

- Keep the first version cron-driven like the existing discovery flow.
- Prefer free/public source discovery first.
- Design source adapters so paid/API-backed sources can be added later.
- Avoid broad crawling; source lists and query templates must remain explicit and reviewable.
- Do not alter existing application generation behavior.
