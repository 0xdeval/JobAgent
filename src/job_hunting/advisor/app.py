import chainlit as cl
from crewai import Task, Crew, Process
from job_hunting.agents.career_advisor import build_career_advisor


@cl.on_message
async def on_message(message: cl.Message) -> None:
    advisor = build_career_advisor()

    task = Task(
        description=(
            f"The candidate asks: {message.content}\n\n"
            "Use FileReadTool to read relevant files from data/ and knowledge/profile/ "
            "to answer accurately. Scan data/*/scores/*.json for application statuses, "
            "data/*/vacancies/*.json for vacancy details, and data/*/applications/ for "
            "generated documents. Always base your answer on actual file contents."
        ),
        expected_output="A clear, specific answer to the candidate's question.",
        agent=advisor,
    )

    crew = Crew(
        agents=[advisor],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    await cl.Message(content=str(result)).send()
