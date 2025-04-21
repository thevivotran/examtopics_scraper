# Refactoring Plan: Unify Scraper and Processor with Simplified CLI

**Goal:**

Unify the web scraping functionality of `examtopics_scraper/_run.py` and the data processing logic of `process_data.py` into a single, cohesive command-line application. The application will have two main modes:
1.  Scrape questions for a specific provider and exam, process the data, and save the results to a CSV file.
2.  List all available exams for a given provider.

**Proposed Architecture:**

1.  **CLI Framework:** Utilize `Typer` for creating a clean and structured command-line interface. This simplifies argument parsing and command definition.
2.  **Modularity:**
    *   Keep the Scrapy spiders (`ExamtopicsExamsSpider`, `ExamtopicsQuestionsSpider`) in `examtopics_scraper/spiders.py`.
    *   Keep the Scrapy pipelines/exporters (`ExamtopicsExamsStdoutPipeline`, etc.) in `examtopics_scraper/exporters.py`, adding a new pipeline to collect items in memory (`ItemCollectorPipeline`).
    *   Refactor the core data processing logic from `process_data.py` (URL fetching, HTML parsing with `requests` and `lxml`) into a dedicated function or module (e.g., `examtopics_scraper/processing.py`).
    *   The main CLI entry point (likely `examtopics_scraper/__main__.py`) will use `Typer` and orchestrate the calls to the scraping and processing components.
3.  **Entry Point:** The application will be runnable via `python -m examtopics_scraper ...` or a configured console script entry point in `pyproject.toml` (e.g., `examtopics-scraper`).

**Data Flow:**

```mermaid
graph TD
    subgraph Unified CLI Application (examtopics_scraper)
        direction LR
        subgraph "Command: scrape [provider] [exam_code] -o [output.csv]"
            A[CLI Input] --> B(Typer App);
            B --> C[Configure & Run Scrapy Process];
            C --> D[ExamtopicsQuestionsSpider];
            D -- Scraped Items (id, url) --> E(In-Memory Item Collector Pipeline);
            E --> F{List of Dictionaries};
            B -- Passes Items & Output Path --> G[Call process_question_data];
            G -- Fetches URLs --> H(requests/lxml);
            H -- Parsed Data --> G;
            G -- Final Processed Data --> I[Write to Output CSV];
        end

        subgraph "Command: list-exams [provider]"
             J[CLI Input] --> K(Typer App);
             K --> L[Configure & Run Scrapy Process];
             L --> M[ExamtopicsExamsSpider];
             M -- Scraped Items (code, name) --> N(ExamtopicsExamsStdoutPipeline);
             N -- Formatted Output --> O[Print to Console];
        end
    end

    subgraph External
        P[User] --> A;
        P --> J;
        I --> Q[output.csv File];
        O --> R[Console Output];
    end
```

**Key Modifications:**

1.  **`examtopics_scraper/_run.py`:**
    *   Remove this file. Its `argparse` logic is replaced by `Typer` in `__main__.py`.
    *   The `scrape_exams` and `scrape_questions` functions are removed; `CrawlerProcess` is managed by `Typer` commands.
2.  **`process_data.py`:**
    *   Remove this file.
    *   Refactor its core logic into a function `process_question_data(scraped_items: list[dict], output_csv_path: str)` in a new `examtopics_scraper/processing.py` file. This function will handle fetching, parsing (using existing XPaths/logic), and writing the final CSV.
3.  **`examtopics_scraper/exporters.py`:**
    *   Add a new pipeline (e.g., `ItemCollectorPipeline`) that appends scraped items (`{'id': ..., 'url': ...}`) to an in-memory list instead of writing to a file during the crawl.
    *   `ExamtopicsExamsStdoutPipeline` remains for the `list-exams` command.
4.  **`examtopics_scraper/__main__.py` (New or Existing):**
    *   Implement the main `Typer` application here.
    *   Define the `scrape` command:
        *   Takes `provider`, `exam_code`, and `--output` file path as arguments.
        *   Configures Scrapy settings to use `ItemCollectorPipeline`.
        *   Runs `CrawlerProcess` with `ExamtopicsQuestionsSpider`.
        *   Retrieves the collected items list after the crawl finishes.
        *   Calls `process_question_data` with the collected items and output path.
    *   Define the `list-exams` command:
        *   Takes `provider` as an argument.
        *   Configures Scrapy settings to use `ExamtopicsExamsStdoutPipeline`.
        *   Runs `CrawlerProcess` with `ExamtopicsExamsSpider`.
5.  **`pyproject.toml`:**
    *   Add `typer[all]` as a dependency.
    *   Ensure `requests`, `lxml`, and `Scrapy` are listed as dependencies.
    *   Configure a console script entry point:
        ```toml
        [project.scripts]
        examtopics-scraper = "examtopics_scraper.__main__:app"
        ```

**Implementation Steps:**

1.  **Add Dependencies:** Add `typer[all]` to `pyproject.toml` and run `pip install -e .` (or equivalent).
2.  **Refactor `process_data.py`:** Create `examtopics_scraper/processing.py` and implement the `process_question_data` function based on the logic from the old `process_data.py`. Delete `process_data.py`.
3.  **Create Pipeline:** Implement the `ItemCollectorPipeline` in `examtopics_scraper/exporters.py`.
4.  **Implement CLI:** Create/update `examtopics_scraper/__main__.py` with the `Typer` application and the `scrape` and `list-exams` commands.
5.  **Orchestration:** Ensure the commands correctly configure and run Scrapy, handle item collection, and call the processing function.
6.  **Configure Entry Point:** Add the `[project.scripts]` section to `pyproject.toml`.
7.  **Cleanup:** Delete `examtopics_scraper/_run.py`.
8.  **Testing:** Test both `examtopics-scraper scrape ...` and `examtopics-scraper list-exams ...`. Verify CSV output and console output.
9.  **Documentation:** Update `README.md` with new usage instructions.