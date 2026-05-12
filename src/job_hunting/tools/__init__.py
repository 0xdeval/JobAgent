from importlib import import_module
from typing import Any

__all__ = [
    "DedupTool",
    "TelegramNotifierTool",
    "CVGeneratorTool",
    "CoverLetterTool",
    "SafeSeleniumScrapingTool",
    "DiscoveryCoverageStore",
    "DiscoveryCoverageTool",
    "CompanyCandidate",
    "CompanyCandidateStore",
    "PublicCompanySearch",
    "CareerPageResolver",
    "CompanyQueryPlannerTool",
    "PublicCompanySearchTool",
    "CareerPageResolverTool",
    "CompanyCandidateDedupTool",
    "CompanyCandidateWriterTool",
]


def __getattr__(name: str) -> Any:
    module_map = {
        "DedupTool": "job_hunting.tools.dedup_tool",
        "TelegramNotifierTool": "job_hunting.tools.telegram_notifier",
        "CVGeneratorTool": "job_hunting.tools.cv_generator",
        "CoverLetterTool": "job_hunting.tools.cover_letter_tool",
        "SafeSeleniumScrapingTool": "job_hunting.tools.safe_selenium_scraper",
        "DiscoveryCoverageStore": "job_hunting.tools.discovery_coverage",
        "DiscoveryCoverageTool": "job_hunting.tools.discovery_coverage",
        "CompanyCandidate": "job_hunting.tools.company_candidate_store",
        "CompanyCandidateStore": "job_hunting.tools.company_candidate_store",
        "PublicCompanySearch": "job_hunting.tools.company_public_search",
        "CareerPageResolver": "job_hunting.tools.career_page_resolver",
        "CompanyQueryPlannerTool": "job_hunting.tools.company_sourcing_tools",
        "PublicCompanySearchTool": "job_hunting.tools.company_sourcing_tools",
        "CareerPageResolverTool": "job_hunting.tools.company_sourcing_tools",
        "CompanyCandidateDedupTool": "job_hunting.tools.company_sourcing_tools",
        "CompanyCandidateWriterTool": "job_hunting.tools.company_sourcing_tools",
    }
    if name not in module_map:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_map[name])
    return getattr(module, name)
