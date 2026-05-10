import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from job_hunting.utils import all_vacancy_files


class DedupInput(BaseModel):
    url: str = Field(description="The vacancy URL to check for duplicates")


class DedupTool(BaseTool):
    name: str = "Vacancy Dedup Checker"
    description: str = (
        "Check if a vacancy URL has already been scraped in a previous run. "
        "Returns 'duplicate' if seen before, 'new' if not."
    )
    args_schema: type[BaseModel] = DedupInput

    def _run(self, url: str) -> str:
        for vacancy_file in all_vacancy_files():
            try:
                data = json.loads(vacancy_file.read_text())
                if data.get("url") == url:
                    return "duplicate"
            except (json.JSONDecodeError, OSError):
                continue
        return "new"
