import json
from datetime import date
from crewai.flow.flow import Flow, listen, start
from job_hunting.crews.discovery.crew import DiscoveryCrew
from job_hunting.config import MIN_SCORE
from job_hunting.tools.telegram_notifier import TelegramNotifierTool
from job_hunting.utils import scores_dir


class DiscoveryFlow(Flow):

    @start()
    def run_discovery_crew(self) -> list[dict]:
        today = date.today().isoformat()
        DiscoveryCrew().crew().kickoff(inputs={"today": today})
        qualifying = []
        score_dir = scores_dir(today)
        if score_dir.exists():
            for score_file in score_dir.glob("*.json"):
                try:
                    data = json.loads(score_file.read_text())
                    if data.get("score", 0) >= MIN_SCORE and data.get("status") == "pending_approval":
                        qualifying.append(data)
                except (json.JSONDecodeError, OSError):
                    continue
        return qualifying

    @listen(run_discovery_crew)
    def send_approval_requests(self, qualifying_vacancies: list[dict]) -> None:
        if not qualifying_vacancies:
            print("No qualifying vacancies found today.")
            return

        notifier = TelegramNotifierTool()
        for vacancy in qualifying_vacancies:
            notifier._run(
                message_type="approval",
                company=vacancy["company"],
                title=vacancy["title"],
                url=vacancy.get("url", ""),
                score=vacancy["score"],
                vacancy_id=vacancy["vacancy_id"],
                date=vacancy["date"],
            )
            print(f"Sent approval request for {vacancy['vacancy_id']}")
