from unittest.mock import AsyncMock, patch, MagicMock
from job_hunting.tools.telegram_notifier import TelegramNotifierTool


def test_send_approval_message_builds_correct_payload():
    tool = TelegramNotifierTool()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=42))

    with patch("job_hunting.tools.telegram_notifier.Bot", return_value=mock_bot), \
         patch("job_hunting.tools.telegram_notifier.asyncio.run") as mock_run:
        tool._run(
            message_type="approval",
            company="Acme",
            title="Senior PM",
            url="https://acme.com/jobs/pm",
            score=85,
            vacancy_id="acme--senior-pm",
            date="2026-05-10",
        )
        mock_run.assert_called_once()


def test_send_completion_message_builds_correct_payload():
    tool = TelegramNotifierTool()
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(return_value=MagicMock(message_id=43))

    with patch("job_hunting.tools.telegram_notifier.Bot", return_value=mock_bot), \
         patch("job_hunting.tools.telegram_notifier.asyncio.run") as mock_run:
        tool._run(
            message_type="completion",
            company="Acme",
            title="Senior PM",
            url="https://acme.com/jobs/pm",
            score=85,
            vacancy_id="acme--senior-pm",
            date="2026-05-10",
        )
        mock_run.assert_called_once()
