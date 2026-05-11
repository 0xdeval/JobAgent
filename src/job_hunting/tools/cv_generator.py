import json
import subprocess
import tempfile
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = PROJECT_ROOT / "personalized-outreach/templates/cv-template.md"
SCRIPT_PATH = PROJECT_ROOT / "personalized-outreach/scripts/fill-template.js"
PROFILE_DIR = PROJECT_ROOT / "knowledge/profile"


class CVGeneratorInput(BaseModel):
    tailored_json: str = Field(
        description="JSON string with tailored CV data: summary, workExperienceIds, "
        "workExperienceDescriptions, projectIds, projectDescriptions, skills"
    )
    output_tex_path: str = Field(description="Absolute or relative path for the output .tex file")


class CVGeneratorTool(BaseTool):
    name: str = "CV Generator"
    description: str = (
        "Generate a tailored CV PDF from the candidate's profile. "
        "Provide tailored JSON data and the output file path. "
        "Returns the path to the generated PDF, or an error message."
    )
    args_schema: type[BaseModel] = CVGeneratorInput

    def _run(self, tailored_json: str, output_tex_path: str) -> str:
        output_path = Path(output_tex_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix="tailored-cv-"
        ) as f:
            f.write(tailored_json)
            json_path = f.name

        result = subprocess.run(
            [
                "node",
                str(SCRIPT_PATH),
                str(TEMPLATE_PATH),
                json_path,
                str(output_path),
                str(PROFILE_DIR),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Error generating .tex: {result.stderr}"

        pdf_path = output_path.with_suffix(".pdf")
        tex_dir = str(output_path.parent)

        draft_result = subprocess.run(
            [
                "pdflatex",
                "-draftmode",
                "-interaction=nonstopmode",
                f"-output-directory={tex_dir}",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if draft_result.returncode != 0:
            return (
                f"LaTeX validation failed. Fix the .tex file before converting to PDF.\n"
                f"Errors:\n{draft_result.stdout[-2000:]}"
            )

        compile_result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={tex_dir}",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )
        if compile_result.returncode != 0:
            return f"PDF compilation failed:\n{compile_result.stdout[-2000:]}"

        return str(pdf_path)
