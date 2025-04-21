import argparse
import sys
from typing import TypedDict, Optional

import scrapy.crawler

from examtopics_scraper.exporters import (ExamtopicsExamsStdoutPipeline,
                                          ExamtopicsQuestionsStdoutPipeline,
                                          ExamtopicsQuestionsCsvPipeline,
                                          ScrapyPipeline)
from examtopics_scraper.spiders import ExamtopicsExamsSpider, ExamtopicsQuestionsSpider


class CrawlerSettings(TypedDict, total=False): # Use total=False for optional keys
    ITEM_PIPELINES: dict[str | type[ScrapyPipeline], int] # Allow string paths for pipelines
    LOG_LEVEL: str
    CSV_OUTPUT_PATH: str # Add optional setting key


def run():
    parser = argparse.ArgumentParser(prog="examtopics_scraper",
                                     description="Simple scraper for question discussions on "
                                                 "ExamTopics")
    parser.add_argument("provider", help="exam provider")
    parser.add_argument("-e", "--exam", help="exam code")
    parser.add_argument("-o", "--output", help="output path for question discussions CSV") # Updated help text
    parser.add_argument("-v", "--verbose", action="count", help="enable debug logging")
    args = parser.parse_args()

    if not args.verbose:
        log_level = "ERROR"
    elif args.verbose == 1:
        log_level = "INFO"
    else:
        log_level = "DEBUG"

    if args.exam:
        scrape_questions(args.provider, args.exam, args.output, log_level)
    elif args.output:
        # This condition might be less relevant now, but keep for consistency
        print("Cannot save output of provider scraper (use -e for exam questions).")
        sys.exit(64)
    else:
        scrape_exams(args.provider, log_level)


def scrape_exams(provider: str, log_level: str = "ERROR"):
    """Scrape exams on ExamTopics for a given provider."""
    settings: CrawlerSettings = {
        "ITEM_PIPELINES": {ExamtopicsExamsStdoutPipeline: 300},
        "LOG_LEVEL": log_level
    }
    process = scrapy.crawler.CrawlerProcess(settings=settings)
    process.crawl(ExamtopicsExamsSpider, provider=provider)
    process.start()


def scrape_questions(provider: str, exam: str, output: Optional[str], log_level: str = "ERROR"):
    """Scrape question discussions on ExamTopics."""
    settings: CrawlerSettings = {"LOG_LEVEL": log_level}
    if output:
        # Use the pipeline class path string and pass the output path via settings
        settings["ITEM_PIPELINES"] = {ExamtopicsQuestionsStdoutPipeline: 300} # Corrected line
        settings["CSV_OUTPUT_PATH"] = output
    else:
        # Keep using Stdout pipeline if no output file is specified
        settings["ITEM_PIPELINES"] = {ExamtopicsQuestionsStdoutPipeline: 300}

    process = scrapy.crawler.CrawlerProcess(settings=settings)
    process.crawl(ExamtopicsQuestionsSpider, provider=provider, exam=exam)
    process.start()
