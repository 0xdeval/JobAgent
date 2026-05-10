from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from job_hunting.tools.cover_letter_tool import CoverLetterTool


SAMPLE_TEMPLATE = r"""
\begin{document}
==INTRO==

==MAIN BODY==

==CONCLUSION==
\end{document}
"""


def test_cover_letter_fills_placeholders(tmp_path):
    tool = CoverLetterTool()
    output_path = tmp_path / "cover-letter.tex"

    mock_result = MagicMock(returncode=0, stdout="", stderr="")

    with patch("builtins.open", mock_open(read_data=SAMPLE_TEMPLATE)), \
         patch("subprocess.run", return_value=mock_result), \
         patch.object(Path, "write_text"):
        tool._run(
            intro="I was excited to see this role at Acme.",
            main_body="At Blockscout, I grew MAU by 300% through product-led growth.",
            conclusion="I would love to discuss this further.",
            output_tex_path=str(output_path),
        )


def test_cover_letter_returns_error_on_compile_failure(tmp_path):
    tool = CoverLetterTool()
    output_path = tmp_path / "cover-letter.tex"

    mock_fail = MagicMock(returncode=1, stdout="LaTeX Error", stderr="")

    with patch("builtins.open", mock_open(read_data=SAMPLE_TEMPLATE)), \
         patch("subprocess.run", return_value=mock_fail), \
         patch.object(Path, "write_text"):
        result = tool._run(
            intro="intro",
            main_body="body",
            conclusion="conclusion",
            output_tex_path=str(output_path),
        )
        assert "failed" in result.lower()
