from crewai import Agent
from crewai_tools import FileReadTool
from job_hunting.config import get_llm


def build_career_advisor() -> Agent:
    return Agent(
        role="Career Advisor",
        goal=(
            "Help the candidate understand their job search status, assess fit for specific roles, "
            "and answer any questions about their applications and pipeline."
        ),
        backstory=(
            "You are a knowledgeable career advisor with full access to the candidate's job search data. "
            "You can read vacancy details, fit scores, application statuses, and profile information. "
            "You give direct, honest, and specific answers. You always base your answers on actual data "
            "from the files — never make up information."
        ),
        llm=get_llm(),
        tools=[FileReadTool()],
        verbose=True,
        memory=True,
    )
