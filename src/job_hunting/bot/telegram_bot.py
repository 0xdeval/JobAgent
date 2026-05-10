import json
import logging
import threading
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from job_hunting.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from job_hunting.utils import scores_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _update_status(vacancy_id: str, date: str, status: str) -> None:
    score_path = scores_dir(date) / f"{vacancy_id}.json"
    if not score_path.exists():
        logger.warning(f"Score file not found: {score_path}")
        return
    data = json.loads(score_path.read_text())
    data["status"] = status
    score_path.write_text(json.dumps(data, indent=2))


def _parse_callback(data: str) -> tuple[str, str, str]:
    """Parse 'action:vacancy_id:date' → (action, vacancy_id, date)."""
    parts = data.split(":", 2)
    return parts[0], parts[1], parts[2]


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id != TELEGRAM_CHAT_ID:
        return

    await query.answer()
    action, vacancy_id, date = _parse_callback(query.data)

    if action == "approve":
        _update_status(vacancy_id, date, "approved")
        await query.edit_message_text(f"✅ Approved — starting application for {vacancy_id}…")
        threading.Thread(
            target=_run_application_flow,
            args=(vacancy_id, date),
            daemon=True,
        ).start()

    elif action == "decline":
        _update_status(vacancy_id, date, "declined")
        await query.edit_message_text(f"❌ Declined: {vacancy_id}")

    elif action == "applied":
        _update_status(vacancy_id, date, "applied")
        await query.edit_message_text(f"✅ Marked as applied: {vacancy_id}")

    elif action == "not_applied":
        _update_status(vacancy_id, date, "not_applied")
        await query.edit_message_text(f"📝 Noted — not applied: {vacancy_id}")


def _run_application_flow(vacancy_id: str, date: str) -> None:
    from job_hunting.flows.application_flow import ApplicationFlow
    try:
        ApplicationFlow(vacancy_id=vacancy_id, date=date).kickoff()
    except Exception as e:
        logger.error(f"ApplicationFlow failed for {vacancy_id}: {e}")


def run() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_callback))
    logger.info("Bot started. Listening for callbacks…")
    app.run_polling(drop_pending_updates=True)
