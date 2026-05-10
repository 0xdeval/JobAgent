from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool, FileWriterTool
from typing import List
from job_hunting.config import get_llm
from job_hunting.tools import CVGeneratorTool, CoverLetterTool


@CrewBase
class ApplicationCrew:
    """Generates tailored CV, cover letter, and Q&A answers for an approved vacancy."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def profile_steward(self) -> Agent:
        return Agent(
            config=self.agents_config["profile_steward"],
            llm=get_llm(),
            tools=[FileReadTool()],
            verbose=True,
        )

    @agent
    def qa_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["qa_analyst"],
            llm=get_llm(),
            tools=[FileWriterTool()],
            verbose=True,
        )

    @agent
    def cv_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["cv_architect"],
            llm=get_llm(),
            tools=[FileReadTool(), CVGeneratorTool()],
            verbose=True,
        )

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["cover_letter_writer"],
            llm=get_llm(),
            tools=[FileReadTool(), CoverLetterTool()],
            verbose=True,
        )

    @task
    def profile_brief_task(self) -> Task:
        return Task(config=self.tasks_config["profile_brief_task"])

    @task
    def qa_task(self) -> Task:
        return Task(config=self.tasks_config["qa_task"])

    @task
    def cv_task(self) -> Task:
        return Task(config=self.tasks_config["cv_task"])

    @task
    def cover_letter_task(self) -> Task:
        return Task(config=self.tasks_config["cover_letter_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
