import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from job_hunting.tools.dedup_tool import DedupTool


def test_url_not_seen_returns_new(tmp_path):
    tool = DedupTool()
    with patch("job_hunting.tools.dedup_tool.all_vacancy_files", return_value=[]):
        result = tool._run(url="https://acme.com/jobs/pm")
    assert result == "new"


def test_url_already_seen_returns_duplicate(tmp_path):
    vacancy = {"url": "https://acme.com/jobs/pm", "id": "acme--pm"}
    vacancy_file = tmp_path / "acme--pm.json"
    vacancy_file.write_text(json.dumps(vacancy))

    tool = DedupTool()
    with patch(
        "job_hunting.tools.dedup_tool.all_vacancy_files",
        return_value=[vacancy_file],
    ):
        result = tool._run(url="https://acme.com/jobs/pm")
    assert result == "duplicate"
