import typer
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.signalmanager import dispatcher
from scrapy import signals

# Import project components
from examtopics_scraper.spiders import ExamtopicsExamsSpider, ExamtopicsQuestionsSpider
from examtopics_scraper.exporters import ItemCollectorPipeline # Import the collector
from examtopics_scraper.processing import process_question_data

# --- Typer App Initialization ---
app = typer.Typer(
    name="examtopics-scraper",
    help="A CLI tool to scrape ExamTopics exam lists and question discussion URLs, then process question details.",
    add_completion=False,
)

# --- Global variable to hold collected items ---
# This is a simple way to pass data from the pipeline back to the main script
# when using CrawlerProcess and signals.
collected_items_global = []

def spider_closed_handler(spider, reason):
    """Signal handler to access collected items after spider closes."""
    global collected_items_global
    # Access the pipeline instance through the crawler's pipeline manager
    # Note: This relies on internal Scrapy structure but is a common pattern.
    # Ensure ItemCollectorPipeline is uniquely identifiable if multiple pipelines exist.
    for p in spider.crawler.engine.scraper.itemproc.middlewares: # CORRECTED LINE based on debug output
        if isinstance(p, ItemCollectorPipeline):
            collected_items_global = p.items
            break
    spider.logger.info(f"Spider closed: {reason}. Items collected: {len(collected_items_global)}")


@app.command("list-exams")
def list_exams(
    provider: str = typer.Argument(..., help="The exam provider code (e.g., 'microsoft', 'amazon').")
):
    """
    Lists all available exams for a given provider by scraping ExamTopics.
    """
    print(f"Fetching exams for provider: {provider}...")

    settings = Settings()
    settings['ITEM_PIPELINES'] = {
        'examtopics_scraper.exporters.ExamtopicsExamsStdoutPipeline': 1
    }
    settings['LOG_LEVEL'] = 'INFO'
    settings['ROBOTSTXT_OBEY'] = False # Be respectful, but ExamTopics often blocks default Scrapy UA

    process = CrawlerProcess(settings)
    process.crawl(ExamtopicsExamsSpider, provider=provider)

    try:
        process.start() # the script will block here until the crawling is finished
        print("Exam listing finished.")
    except Exception as e:
        print(f"An error occurred during the crawl: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command("scrape")
def scrape_and_process(
    provider: str = typer.Argument(..., help="The exam provider code (e.g., 'microsoft', 'amazon')."),
    exam_code: str = typer.Argument(..., help="The specific exam code (e.g., 'az-900', 'aws-certified-solutions-architect-associate')."),
    output_csv: Path = typer.Option(
        ..., # Make output mandatory
        "--output", "-o",
        help="Path to the output CSV file where processed question data will be saved.",
        writable=True,
        resolve_path=True, # Ensure path is absolute
    ),
):
    """
    Scrapes question URLs for a specific exam, fetches details for each question,
    processes the data, and saves it to a CSV file.
    """
    global collected_items_global
    collected_items_global = [] # Reset global list before crawl

    print(f"Starting scrape for {provider}/{exam_code}...")
    print(f"Output will be saved to: {output_csv}")

    # Ensure output directory exists
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    settings = Settings()
    # Configure Scrapy to use the ItemCollectorPipeline
    settings['ITEM_PIPELINES'] = {
        'examtopics_scraper.exporters.ItemCollectorPipeline': 1
    }
    settings['LOG_LEVEL'] = 'INFO'
    settings['ROBOTSTXT_OBEY'] = False

    # Connect the signal handler *before* starting the process
    dispatcher.connect(spider_closed_handler, signal=signals.spider_closed)

    process = CrawlerProcess(settings)
    process.crawl(ExamtopicsQuestionsSpider, provider=provider, exam_code=exam_code)

    try:
        # This starts the Scrapy event loop and blocks until the crawl is finished
        process.start()
    except Exception as e:
        print(f"An error occurred during the scraping crawl: {e}", file=sys.stderr)
        # Disconnect signal handler on error
        dispatcher.disconnect(spider_closed_handler, signal=signals.spider_closed)
        raise typer.Exit(code=1)

    # Disconnect the signal handler now that the crawl is done
    dispatcher.disconnect(spider_closed_handler, signal=signals.spider_closed)

    # --- Processing Step ---
    if not collected_items_global:
        print("No items were collected during the scrape. Check the spider logs.", file=sys.stderr)
        raise typer.Exit(code=1)

    print(f"\nScraping finished. Collected {len(collected_items_global)} question URLs.")
    print("Starting data processing...")

    try:
        process_question_data(collected_items_global, str(output_csv))
        print(f"\nSuccessfully processed data and saved to {output_csv}")
    except Exception as e:
        print(f"An error occurred during data processing: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
