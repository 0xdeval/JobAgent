import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from job_hunting.tools.cv_generator import CVGeneratorTool


SAMPLE_TAILORED_JSON = {
    "summary": "Experienced product manager with strong Web3 background.",
    "workExperienceIds": ["blockscout"],
    "workExperienceDescriptions": {
        "blockscout": ["Grew MAU by **300%** via product-led growth initiatives"]
    },
    "projectIds": [],
    "projectDescriptions": {},
    "skills": "Product strategy, Web3, DeFi, SQL, Python",
}


def test_cv_generator_calls_node_script(tmp_path):
    tool = CVGeneratorTool()
    output_path = tmp_path / "cv.tex"

    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        tool._run(
            tailored_json=json.dumps(SAMPLE_TAILORED_JSON),
            output_tex_path=str(output_path),
        )
        assert mock_run.call_count >= 1
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "fill-template.js" in " ".join(first_call_args)


def test_cv_generator_raises_on_node_error(tmp_path):
    tool = CVGeneratorTool()
    output_path = tmp_path / "cv.tex"

    mock_result = MagicMock(returncode=1, stdout="", stderr="Error: template not found")

    with patch("subprocess.run", return_value=mock_result):
        result = tool._run(
            tailored_json=json.dumps(SAMPLE_TAILORED_JSON),
            output_tex_path=str(output_path),
        )
        assert "Error" in result
