from crewai.flow.flow import Flow, listen, start

from job_hunting.crews.company_sourcing.crew import CompanySourcingCrew
from job_hunting.tools.company_candidate_store import CompanyCandidateStore
from job_hunting.tools.telegram_notifier import TelegramNotifierTool
from job_hunting.utils import company_candidates_file, today


class CompanySourcingFlow(Flow):

    @start()
    def run_company_sourcing_crew(self) -> dict:
        run_date = today()
        output = company_candidates_file(run_date)
        output.parent.mkdir(parents=True, exist_ok=True)
        store = CompanyCandidateStore(run_date=run_date)
        pending_before = store.list_pending_candidate_ids()

        CompanySourcingCrew().crew().kickoff(inputs={"today": run_date})
        if not output.exists():
            raise FileNotFoundError(
                f"Company sourcing completed without creating expected output: {output}"
            )

        candidates = store.list_pending_candidates(exclude_ids=pending_before)
        return {
            "run_date": run_date,
            "candidate_count": len(candidates),
            "path": output,
            "candidates": candidates,
        }

    @listen(run_company_sourcing_crew)
    def send_review_notification(self, result: dict) -> None:
        candidates = result.get("candidates", [])
        if not candidates:
            print("No company candidates pending review.")
            return

        notifier = TelegramNotifierTool()
        for candidate in candidates:
            notifier.send_company_candidate_review(
                run_date=result["run_date"],
                candidate=candidate,
            )
