import asyncio
import csv
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from job_hunting.bot.telegram_bot import handle_callback
from job_hunting.tools.telegram_notifier import TelegramNotifierTool


def _update(callback_data: str):
    query = MagicMock()
    query.data = callback_data
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    update = MagicMock()
    update.callback_query = query
    update.effective_chat.id = 123
    return update, query


def test_company_approve_updates_candidate_and_appends_approved_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_ALLOWED_USERS", "")
    Path("knowledge").mkdir()
    Path("knowledge/companies.csv").write_text("Company,Career page\n", encoding="utf-8")
    candidate_file = Path("data/2026-05-13/company_candidates.csv")
    candidate_file.parent.mkdir(parents=True)
    candidate_file.write_text(
        "candidate_id,company,career_page,website,description,industry,source,match_score,match_reason,status,discovered_at,reviewed_at\n"
        "acme-id,Acme,https://acme.example/jobs,https://acme.example,Description,FinTech,search,90,Fit,pending_review,2026-05-13T09:00:00Z,\n",
        encoding="utf-8",
    )
    update, query = _update("company_approve:acme-id:2026-05-13")

    asyncio.run(handle_callback(update, MagicMock()))

    rows = list(csv.DictReader(candidate_file.open()))
    assert rows[0]["status"] == "approved"
    assert rows[0]["reviewed_at"]
    approved_rows = list(
        csv.DictReader(Path("knowledge/approved-company-candidates.csv").open())
    )
    assert approved_rows == [{"Company": "Acme", "Career page": "https://acme.example/jobs"}]
    query.edit_message_text.assert_awaited_once()
    assert "Approved company" in query.edit_message_text.await_args.args[0]


def test_company_decline_updates_candidate_without_approved_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_ALLOWED_USERS", "")
    candidate_file = Path("data/2026-05-13/company_candidates.csv")
    candidate_file.parent.mkdir(parents=True)
    candidate_file.write_text(
        "candidate_id,company,career_page,website,description,industry,source,match_score,match_reason,status,discovered_at,reviewed_at\n"
        "acme-id,Acme,https://acme.example/jobs,https://acme.example,Description,FinTech,search,90,Fit,pending_review,2026-05-13T09:00:00Z,\n",
        encoding="utf-8",
    )
    update, query = _update("company_decline:acme-id:2026-05-13")

    asyncio.run(handle_callback(update, MagicMock()))

    rows = list(csv.DictReader(candidate_file.open()))
    assert rows[0]["status"] == "declined"
    assert rows[0]["reviewed_at"]
    assert not Path("knowledge/approved-company-candidates.csv").exists()
    assert "Declined company" in query.edit_message_text.await_args.args[0]


def test_invalid_company_callback_does_not_create_approved_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_ALLOWED_USERS", "")
    update, query = _update("company_approve:missing-id:2026-05-13")

    asyncio.run(handle_callback(update, MagicMock()))

    assert not Path("knowledge/approved-company-candidates.csv").exists()
    assert "Could not find company candidate" in query.edit_message_text.await_args.args[0]


def test_company_approve_with_truncated_callback_id_resolves_unique_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr("job_hunting.bot.telegram_bot.TELEGRAM_ALLOWED_USERS", "")
    Path("knowledge").mkdir()
    Path("knowledge/companies.csv").write_text("Company,Career page\n", encoding="utf-8")
    candidate_file = Path("data/2026-05-13/company_candidates.csv")
    candidate_file.parent.mkdir(parents=True)
    long_candidate_id = "very-long-company-candidate-id-that-was-truncated"
    candidate_file.write_text(
        "candidate_id,company,career_page,website,description,industry,source,match_score,match_reason,status,discovered_at,reviewed_at\n"
        f"{long_candidate_id},Acme,https://acme.example/jobs,https://acme.example,Description,FinTech,search,90,Fit,pending_review,2026-05-13T09:00:00Z,\n",
        encoding="utf-8",
    )
    callback = TelegramNotifierTool._build_company_callback_data(
        "company_approve", long_candidate_id, "2026-05-13"
    )
    update, query = _update(callback)

    asyncio.run(handle_callback(update, MagicMock()))

    rows = list(csv.DictReader(candidate_file.open()))
    assert rows[0]["status"] == "approved"
    approved_rows = list(
        csv.DictReader(Path("knowledge/approved-company-candidates.csv").open())
    )
    assert approved_rows == [{"Company": "Acme", "Career page": "https://acme.example/jobs"}]
    assert "Approved company" in query.edit_message_text.await_args.args[0]
