from pathlib import Path
from job_hunting.utils import (
    all_company_candidate_files,
    applications_dir,
    company_candidates_file,
    scores_dir,
    vacancies_dir,
)


def test_vacancies_dir():
    assert vacancies_dir("2026-05-10") == Path("data/2026-05-10/vacancies")


def test_scores_dir():
    assert scores_dir("2026-05-10") == Path("data/2026-05-10/scores")


def test_applications_dir():
    result = applications_dir("2026-05-10", "acme--senior-pm")
    assert result == Path("data/2026-05-10/applications/acme--senior-pm")


def test_company_candidates_file_uses_run_date():
    assert company_candidates_file("2026-05-11") == Path(
        "data/2026-05-11/company_candidates.csv"
    )


def test_all_company_candidate_files_finds_historical_files(tmp_path, monkeypatch):
    first = tmp_path / "data" / "2026-05-10" / "company_candidates.csv"
    second = tmp_path / "data" / "2026-05-11" / "company_candidates.csv"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("company,career_page\nAcme,https://acme.com/careers\n")
    second.write_text("company,career_page\nRamp,https://ramp.com/careers\n")

    monkeypatch.chdir(tmp_path)

    assert all_company_candidate_files() == [
        Path("data/2026-05-10/company_candidates.csv"),
        Path("data/2026-05-11/company_candidates.csv"),
    ]
