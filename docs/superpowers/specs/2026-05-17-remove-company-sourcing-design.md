# Remove Company Sourcing Design

## Goal

Remove the `job_hunting_source_companies` feature and all related source files, tests, data files, configuration, and documentation. After the change, the project should support only curated-company vacancy discovery through `knowledge/companies.csv`, Telegram vacancy approval/status handling, `/prep_vacancy`, application artifact generation, and the advisor UI.

## Background

Company sourcing was previously a separate cron-style workflow that searched for new company career pages, wrote `data/<date>/company_candidates.csv`, sent Telegram review controls, and optionally added approved sourced companies through `knowledge/approved-company-candidates.csv`. That workflow is no longer required. Keeping its code and documentation creates extra maintenance surface and makes the current product path harder to understand.

## Scope

Remove the complete company-sourcing subsystem:

- `job_hunting_source_companies` package script and `run_company_sourcing` entry point.
- Company sourcing flow and crew files.
- Company sourcing tools, query planner, candidate store, public search helper, and sourcing-only career-page resolver usage.
- Telegram company-candidate notifications and company approve/decline callback handling.
- Discovery loading from `knowledge/approved-company-candidates.csv`.
- Company-sourcing tests and shared-test expectations that reference sourced candidates.
- `knowledge/company-source-queries.yaml`, `knowledge/approved-company-candidates.csv` when present, and checked-in `data/*/company_candidates.csv` files.
- Current README/setup-guide references and historical Superpowers specs/plans whose topic is company sourcing or company-sourcing Telegram approval.

Out of scope:

- Vacancy discovery from `knowledge/companies.csv`.
- Vacancy scoring and application artifact generation.
- Telegram vacancy approval/status callbacks.
- `/prep_vacancy`.
- Chainlit advisor.

## Architecture

Discovery becomes the only company-driven workflow. It reads curated companies from `knowledge/companies.csv`, dedupes or validates according to existing discovery behavior, initializes discovery coverage from that same curated list, discovers vacancies, scores them, and sends vacancy approval cards.

There will be no generated-company review state. `knowledge/companies.csv` remains the single source of monitored company career pages. Removing `knowledge/approved-company-candidates.csv` from discovery avoids hidden inputs and keeps company selection explicit.

Telegram bot behavior narrows to vacancy callbacks and command handling. Callback data for company candidates, candidate CSV mutation, and approved sourced-company appends are deleted.

## File Changes

Expected removals include:

- `src/job_hunting/flows/company_sourcing_flow.py`
- `src/job_hunting/crews/company_sourcing/`
- `src/job_hunting/tools/company_sourcing_tools.py`
- `src/job_hunting/tools/company_query_planner.py`
- `src/job_hunting/tools/company_candidate_store.py`
- company-sourcing-specific tests under `tests/`
- `knowledge/company-source-queries.yaml`
- checked-in `data/*/company_candidates.csv`
- Superpowers docs/plans/specs focused on company sourcing

Expected edits include:

- `pyproject.toml`: remove the script entry.
- `src/job_hunting/main.py`: remove `run_company_sourcing`.
- `src/job_hunting/utils.py`: remove company-candidate and approved sourced-company helpers.
- `src/job_hunting/flows/discovery_flow.py`: load only curated companies.
- `src/job_hunting/bot/telegram_bot.py`: remove company-candidate callback handling.
- `src/job_hunting/tools/telegram_notifier.py`: remove company-candidate review notification methods.
- `README.md` and `docs/setup-guide.md`: describe only current supported workflows.
- Shared tests: update assertions to match the curated-company-only discovery path and remaining Telegram behavior.

## Error Handling

Discovery should continue to treat missing or malformed `knowledge/companies.csv` according to current discovery behavior. Missing company-sourcing files are no longer a supported or meaningful runtime state because those files will not be referenced.

Telegram callbacks for removed company-candidate actions should not be accepted as a supported API. The bot should only route known vacancy and prep-vacancy actions. If an old callback reaches a running bot, it can fall through to the existing unknown-action behavior.

## Testing

Verification must prove both removal and preservation:

- `rg` should find no active references to `job_hunting_source_companies`, company sourcing, company candidates, approved sourced companies, `company-source-queries`, or `company_candidates.csv`, except in the new removal design/plan docs if those docs need to name the removed feature.
- Targeted tests should cover discovery loading from `knowledge/companies.csv` only.
- Telegram bot tests should cover the remaining vacancy approval/status and `/prep_vacancy` behavior.
- Shared utility and notifier tests should pass after deleted helpers are removed.
- The full suite should pass with `uv run pytest`.

## Completion Criteria

- The feature branch is based on `develop` in a separate worktree.
- All company-sourcing runtime code, tests, config, data, and docs are removed or updated.
- Current docs no longer instruct users to run, configure, or review company sourcing.
- `job_hunting_source_companies` is no longer installable as a package script.
- Discovery uses only `knowledge/companies.csv` as its company input.
- Tests pass locally.
- The completed branch is pushed to GitHub as a separate remote branch.
