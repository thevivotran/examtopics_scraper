# examtopics-scraper
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/aserpi/examtopics_scraper)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/aserpi/examtopics_scraper/package.yml)
![Python version](https://img.shields.io/badge/python-v3.10+-blue)

_examtopics-scraper_ is a unified command-line tool for scraping ExamTopics. It allows you to list available exams for a provider or scrape and process question discussion details for a specific exam, saving the results directly to a CSV file.

## Installation

```bash
# Install from source
git clone https://github.com/aserpi/examtopics_scraper.git
cd examtopics_scraper
pip install .
# Or for development:
# pip install -e .
```
*Requires Python 3.10+.*

## Usage

The tool now provides a single entry point `examtopics-scraper` with different commands:

### `list-exams` Command

Lists all available exams for a given provider.

**Usage:**

```bash
examtopics-scraper list-exams [OPTIONS] PROVIDER
```

**Arguments:**

*   `PROVIDER`: The exam provider code (e.g., 'microsoft', 'google', 'aws'). [required]

**Example:**

*   List available exams for Microsoft:
    ```bash
    examtopics-scraper list-exams microsoft
    ```

### `scrape` Command

Scrapes question discussion URLs for a specific exam, fetches the detailed content (question, answers, correct answer) for each URL, processes the data, and saves the final results to a specified CSV file.

**Usage:**

```bash
examtopics-scraper scrape [OPTIONS] PROVIDER EXAM_CODE
```

**Arguments:**

*   `PROVIDER`: The exam provider code (e.g., 'microsoft', 'google', 'aws'). [required]
*   `EXAM_CODE`: The specific exam code (e.g., 'az-900', 'SAA-C03'). [required]

**Options:**

*   `-o, --output PATH`: Path to the output CSV file where processed question data will be saved. [required]
*   `--help`: Show help message and exit.

**Example:**

*   Scrape and process questions for AWS SAA-C03, saving results to `saa-c03_details.csv`:
    ```bash
    examtopics-scraper scrape aws SAA-C03 -o saa-c03_details.csv
    ```

This command performs the entire workflow: scraping the initial URLs, visiting each URL to extract detailed question data using specific XPaths, processing the correct answer format, and writing the final, comprehensive data to the output CSV. Errors during fetching or parsing will be printed to the standard error stream.
