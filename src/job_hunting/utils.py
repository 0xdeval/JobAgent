from datetime import date
from pathlib import Path


def today() -> str:
    return date.today().isoformat()


def vacancies_dir(run_date: str) -> Path:
    return Path(f"data/{run_date}/vacancies")


def scores_dir(run_date: str) -> Path:
    return Path(f"data/{run_date}/scores")


def applications_dir(run_date: str, vacancy_id: str) -> Path:
    return Path(f"data/{run_date}/applications/{vacancy_id}")


def company_candidates_file(run_date: str) -> Path:
    return Path(f"data/{run_date}/company_candidates.csv")


def all_vacancy_files() -> list[Path]:
    return list(Path("data").glob("*/vacancies/*.json"))


def all_score_files() -> list[Path]:
    return list(Path("data").glob("*/scores/*.json"))


def all_company_candidate_files() -> list[Path]:
    return sorted(Path("data").glob("*/company_candidates.csv"))
