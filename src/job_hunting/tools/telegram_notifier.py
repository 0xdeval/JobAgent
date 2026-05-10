import asyncio
from typing import Literal
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from job_hunting.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class NotifierInput(BaseModel):
    message_type: Literal["approval", "completion"] = Field(
        description="'approval' sends Approve/Decline buttons; 'completion' sends Applied/Not applied buttons"
    )
    company: str = Field(description="Company name")
    title: str = Field(description="Job title")
    url: str = Field(description="Vacancy URL")
    score: int = Field(description="Fit score 0-100")
    vacancy_id: str = Field(description="Vacancy ID (e.g. acme--senior-pm)")
    date: str = Field(description="Discovery date (YYYY-MM-DD)")


class TelegramNotifierTool(BaseTool):
    name: str = "Telegram Notifier"
    description: str = "Send a Telegram notification about a vacancy with action buttons."
    args_schema: type[BaseModel] = NotifierInput

    def _run(
        self,
        message_type: str,
        company: str,
        title: str,
        url: str,
        score: int,
        vacancy_id: str,
        date: str,
    ) -> str:
        asyncio.run(self._send(message_type, company, title, url, score, vacancy_id, date))
        return f"Telegram notification sent for {vacancy_id}"

    async def _send(
        self,
        message_type: str,
        company: str,
        title: str,
        url: str,
        score: int,
        vacancy_id: str,
        date: str,
    ) -> None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        cb = f"{vacancy_id}:{date}"

        if message_type == "approval":
            text = (
                f"🔍 *New vacancy — {company}*\n"
                f"📌 {title}\n"
                f"🔗 [Open]({url})\n"
                f"⭐ Fit score: {score}/100"
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve:{cb}"),
                    InlineKeyboardButton("❌ Decline", callback_data=f"decline:{cb}"),
                ]
            ])
        else:
            text = (
                f"📋 *{company} — {title}*\n"
                f"CV, cover letter, and Q&A answers are ready.\n"
                f"📎 `data/{date}/applications/{vacancy_id}/`"
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Applied", callback_data=f"applied:{cb}"),
                    InlineKeyboardButton("❌ Not applied", callback_data=f"not_applied:{cb}"),
                ]
            ])

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
