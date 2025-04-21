# Refactoring Plan: Examtopics Scraper Export and Processing

This document outlines the plan to refactor the data export functionality of the `examtopics_scraper` project. The goal is to replace the current HTML export with a two-stage process:

1.  A Scrapy pipeline exports basic information (`id`, `url`) to a CSV file.
2.  A separate Python script processes this initial CSV, fetches detailed data from each URL, and generates a final, comprehensive CSV file.

## Phase 1: Refactor Scrapy Exporter (Modify existing Scrapy project)

1.  **Dependencies:** Add `requests` and `lxml` to the project dependencies (e.g., update `pyproject.toml`).
2.  **Create CSV Pipeline (`examtopics_scraper/exporters.py`):**
    *   Define a new class `ExamtopicsQuestionsCsvPipeline(ScrapyPipeline)`.
    *   Implement `from_crawler(cls, crawler)` to read the output file path from `crawler.settings.get('CSV_OUTPUT_PATH')` and pass it to `__init__`.
    *   Implement `__init__(self, output_file)` to store the `output_file` path.
    *   Implement `open_spider(self, spider)` to open the `output_file`, initialize a `csv.writer`, and write the header row: `id,url`.
    *   Implement `process_item(self, item, spider)` to get the item dictionary, write a row containing `item['question']` (as `id`) and `item['url']`, and return the item.
    *   Implement `close_spider(self, spider)` to close the CSV file handle.
    *   Remove or comment out the old `generate_questions_html_exporter` function and `ExamtopicsQuestionsHtmlPipeline` class.
3.  **Update Runner Script (`examtopics_scraper/_run.py`):**
    *   Import the new `ExamtopicsQuestionsCsvPipeline`.
    *   In `scrape_questions`:
        *   If `output` is provided, add it to Scrapy `settings` as `CSV_OUTPUT_PATH`.
        *   Set `ITEM_PIPELINES` to use `{ExamtopicsQuestionsCsvPipeline: 300}`.

## Phase 2: Create New Data Processing Script (New file)

1.  **Create `process_data.py`:**
    *   Use `argparse` for two required arguments: `input_csv` and `output_csv`.
    *   Import `csv`, `requests`, `lxml.html`, `sys`, `argparse`.
    *   Store required XPaths (mapping column names to XPath strings).
    *   Define the output header: `['id', 'url', 'Question', 'Correct Answer', 'Answer 1', 'Answer 2', 'Answer 3', 'Answer 4', 'Answer 5']`.
2.  **Implement Processing Logic:**
    *   Open input/output CSVs, create reader/writer.
    *   Write the header to `output_csv`.
    *   Skip the header in `input_csv`.
    *   Loop through each row (`input_id`, `input_url`) in `input_csv`:
        *   Initialize data holder.
        *   **Fetch:** Use `requests.get()`. Handle `requests.exceptions.RequestException` and HTTP errors (`response.raise_for_status()`). On error, print to `sys.stderr` and set data fields to empty/None.
        *   **Parse:** Use `lxml.html.fromstring()`. Handle general exceptions. On error, print to `sys.stderr` and set fields to empty/None.
        *   **Extract:** Iterate through XPaths. Use `tree.xpath()`. Handle exceptions and missing elements (especially `Answer 5`). On error or missing data, print to `sys.stderr` and store empty string/None.
        *   **Write:** Write the complete row to `output_csv`.

## Workflow Diagram

```mermaid
graph TD
    subgraph Step 1: Scrapy Crawl & Initial Export
        A[Run: examtopics_scraper -p <provider> -e <exam> -o initial_export.csv] --> B(ExamtopicsQuestionsSpider);
        B -- Item (question, url, ...) --> C(ExamtopicsQuestionsCsvPipeline);
        C -- Reads 'CSV_OUTPUT_PATH' from settings --> C;
        C -- Writes row (id=question, url) --> D[initial_export.csv];
    end

    subgraph Step 2: Data Processing Script
        E[Run: python process_data.py initial_export.csv final_data.csv] --> F{Read initial_export.csv};
        F -- Row (id, url) --> G{Fetch HTML from url};
        G -- Success --> H{Parse HTML (lxml)};
        H -- Success --> I{Extract Data via XPaths};
        I -- Extracted Data --> J{Write Row to final_data.csv};
        G -- Fetch Error --> K[Print Error (stderr) & Set Nulls];
        H -- Parse Error --> K;
        I -- XPath Error/Missing --> K;
        K --> J;
        J --> L[final_data.csv];
    end

    D --> E;