import asyncio
import time

import chainlit as cl
from crewai import Task, Crew, Process
from job_hunting.agents.career_advisor import build_career_advisor


@cl.on_message
async def on_message(message: cl.Message) -> None:
    advisor = build_career_advisor()

    task = Task(
        description=(
            f"The candidate asks: {message.content}\n\n"
            "You MUST follow this process when using tools:\n"
            "1) First use 'List Data Files'. Then use 'List Profile Files'.\n"
            "2) Read only concrete file paths returned by that listing tool.\n"
            "3) Never call file-reading tools on directories (e.g. data/, knowledge/profile/) "
            "or wildcard/glob paths (e.g. data/*/scores/*.json).\n"
            "4) Profile files are markdown files in knowledge/profile/ (not profile.json).\n\n"
            "If asked which jobs are already applied, derive the answer from "
            "data/<date>/applications/<vacancy_id>/ directories and corresponding files.\n\n"
            "Answer accurately from real files. Prioritize:\n"
            "- data/<date>/scores/*.json for application status and fit\n"
            "- data/<date>/vacancies/*.json for vacancy details\n"
            "- data/<date>/applications/** for generated application artifacts"
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

    status_message = cl.Message(content="Working on the request...")
    await status_message.send()

    stop_event = asyncio.Event()
    start_time = time.monotonic()

    async def progress_callback() -> None:
        ticks = 0
        while not stop_event.is_set():
            dots = "." * ((ticks % 3) + 1)
            elapsed = int(time.monotonic() - start_time)
            status_message.content = f"Working on the request{dots} ({elapsed}s)"
            await status_message.update()
            ticks += 1
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=2)
            except TimeoutError:
                continue

    progress_task = asyncio.create_task(progress_callback())

    try:
        result = await asyncio.to_thread(crew.kickoff)
        status_message.content = str(result)
    except Exception as exc:
        status_message.content = (
            "I hit an error while analyzing your files.\n\n"
            f"`{type(exc).__name__}: {exc}`"
        )
    finally:
        stop_event.set()
        await progress_task
        await status_message.update()
