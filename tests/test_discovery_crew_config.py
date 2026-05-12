from pathlib import Path

import yaml


def test_vacancy_scout_iteration_budget_covers_company_rows():
    config_path = Path("src/job_hunting/crews/discovery/config/agents.yaml")
    companies_path = Path("knowledge/companies.csv")

    agents_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    company_count = max(
        0, len(companies_path.read_text(encoding="utf-8-sig").splitlines()) - 1
    )

    assert agents_config["vacancy_scout"]["max_iter"] >= company_count * 2
