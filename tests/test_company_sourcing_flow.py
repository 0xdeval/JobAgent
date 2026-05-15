from pathlib import Path
from unittest.mock import MagicMock

import pytest

from job_hunting.flows.company_sourcing_flow import CompanySourcingFlow
from job_hunting.tools.company_candidate_store import CompanyCandidate, CompanyCandidateStore


def test_run_company_sourcing_crew_and_notify(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.today", lambda: "2026-05-11")

    output = Path("data/2026-05-11/company_candidates.csv")

    def _write_candidates(inputs):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "candidate_id,company,career_page,website,description,industry,source,match_score,match_reason,status,discovered_at,reviewed_at\n"
            "acme-id,Acme,https://acme.com/careers,https://acme.com,Builds tools for operators.,FinTech,public_search,85,Strong fit,pending_review,2026-05-11T09:00:00Z,\n"
            "beta-id,Beta,https://beta.com/careers,https://beta.com,Builds beta tools.,SaaS,public_search,70,Weak fit,skipped,2026-05-11T09:00:00Z,\n"
            "gamma-id,Gamma,https://gamma.com/jobs,https://gamma.com,Builds AI tools.,AI,public_search,92,Excellent fit,pending_review,2026-05-11T09:00:00Z,\n",
            encoding="utf-8",
        )

    kickoff = MagicMock(side_effect=_write_candidates)
    crew_obj = MagicMock()
    crew_obj.kickoff = kickoff
    crew_cls = MagicMock()
    crew_cls.return_value.crew.return_value = crew_obj
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.CompanySourcingCrew", crew_cls)

    notifier = MagicMock()
    notifier_cls = MagicMock(return_value=notifier)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.TelegramNotifierTool", notifier_cls)

    flow = CompanySourcingFlow()
    result = flow.run_company_sourcing_crew()

    assert result == {
        "run_date": "2026-05-11",
        "candidate_count": 2,
        "path": output,
        "candidates": [
            {
                "candidate_id": "acme-id",
                "company": "Acme",
                "career_page": "https://acme.com/careers",
                "website": "https://acme.com",
                "description": "Builds tools for operators.",
                "industry": "FinTech",
                "source": "public_search",
                "match_score": "85",
                "match_reason": "Strong fit",
                "status": "pending_review",
                "discovered_at": "2026-05-11T09:00:00Z",
                "reviewed_at": "",
            },
            {
                "candidate_id": "gamma-id",
                "company": "Gamma",
                "career_page": "https://gamma.com/jobs",
                "website": "https://gamma.com",
                "description": "Builds AI tools.",
                "industry": "AI",
                "source": "public_search",
                "match_score": "92",
                "match_reason": "Excellent fit",
                "status": "pending_review",
                "discovered_at": "2026-05-11T09:00:00Z",
                "reviewed_at": "",
            },
        ],
    }
    kickoff.assert_called_once_with(inputs={"today": "2026-05-11"})

    flow.send_review_notification(result)
    assert notifier.send_company_candidate_review.call_count == 2
    notifier.send_company_candidate_review.assert_any_call(
        run_date="2026-05-11",
        candidate=result["candidates"][0],
    )
    notifier.send_company_candidate_review.assert_any_call(
        run_date="2026-05-11",
        candidate=result["candidates"][1],
    )


def test_run_company_sourcing_crew_does_not_notify_for_old_pending_rows(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.today", lambda: "2026-05-11")

    output = Path("data/2026-05-11/company_candidates.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "candidate_id,company,career_page,website,description,industry,source,match_score,match_reason,status,discovered_at,reviewed_at\n"
        "acme-id,Acme,https://acme.com/careers,https://acme.com,Builds tools for operators.,FinTech,public_search,85,Strong fit,pending_review,2026-05-11T09:00:00Z,\n",
        encoding="utf-8",
    )

    kickoff = MagicMock()
    crew_obj = MagicMock()
    crew_obj.kickoff = kickoff
    crew_cls = MagicMock()
    crew_cls.return_value.crew.return_value = crew_obj
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.CompanySourcingCrew", crew_cls)

    notifier = MagicMock()
    notifier_cls = MagicMock(return_value=notifier)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.TelegramNotifierTool", notifier_cls)

    flow = CompanySourcingFlow()
    result = flow.run_company_sourcing_crew()

    assert result == {
        "run_date": "2026-05-11",
        "candidate_count": 0,
        "path": output,
        "candidates": [],
    }

    flow.send_review_notification(result)
    notifier.send_company_candidate_review.assert_not_called()


def test_run_company_sourcing_crew_accepts_fully_deduped_empty_output(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.today", lambda: "2026-05-11")

    knowledge_file = tmp_path / "knowledge" / "companies.csv"
    knowledge_file.parent.mkdir(parents=True)
    knowledge_file.write_text(
        "Company,Career page\nAcme,https://acme.com/careers\n",
        encoding="utf-8",
    )

    def _write_deduped_empty_candidates(inputs):
        store = CompanyCandidateStore(run_date=inputs["today"])
        store.write_candidates(
            [
                CompanyCandidate(
                    company="Acme",
                    career_page="https://acme.com/careers",
                    website="https://acme.com",
                    source="public_search",
                    industry="FinTech",
                    match_score=85,
                    match_reason="Already known",
                    status="pending_review",
                    discovered_at="2026-05-11T09:00:00Z",
                )
            ]
        )

    kickoff = MagicMock(side_effect=_write_deduped_empty_candidates)
    crew_obj = MagicMock()
    crew_obj.kickoff = kickoff
    crew_cls = MagicMock()
    crew_cls.return_value.crew.return_value = crew_obj
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.CompanySourcingCrew", crew_cls)

    flow = CompanySourcingFlow()
    result = flow.run_company_sourcing_crew()

    assert result == {
        "run_date": "2026-05-11",
        "candidate_count": 0,
        "path": Path("data/2026-05-11/company_candidates.csv"),
        "candidates": [],
    }
    assert Path("data/2026-05-11/company_candidates.csv").exists()


def test_send_review_notification_skips_when_no_pending(monkeypatch, capsys):
    notifier = MagicMock()
    notifier_cls = MagicMock(return_value=notifier)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.TelegramNotifierTool", notifier_cls)

    flow = CompanySourcingFlow()
    flow.send_review_notification(
        {
            "run_date": "2026-05-11",
            "candidate_count": 0,
            "path": Path("data/2026-05-11/company_candidates.csv"),
            "candidates": [],
        }
    )

    captured = capsys.readouterr()
    assert "No company candidates pending review." in captured.out
    notifier.send_company_candidate_review.assert_not_called()


def test_run_company_sourcing_crew_raises_when_output_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.today", lambda: "2026-05-11")

    kickoff = MagicMock()
    crew_obj = MagicMock()
    crew_obj.kickoff = kickoff
    crew_cls = MagicMock()
    crew_cls.return_value.crew.return_value = crew_obj
    monkeypatch.setattr("job_hunting.flows.company_sourcing_flow.CompanySourcingCrew", crew_cls)

    flow = CompanySourcingFlow()

    with pytest.raises(FileNotFoundError, match="Company sourcing completed without creating"):
        flow.run_company_sourcing_crew()

    kickoff.assert_called_once_with(inputs={"today": "2026-05-11"})

