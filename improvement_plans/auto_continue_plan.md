# Plan: Auto-Continue Mechanism for ExamTopics Scraper

This plan outlines the steps to modify the ExamTopics scraper to automatically continue processing from the last successfully processed item if a previous run was interrupted.

## Goal

Modify the scraper so that if a run is interrupted, the next run can pick up where the previous one left off, processing only the items that weren't successfully saved to the CSV before.

## Confirmed Approach

1.  **Modify CSV Output:**
    *   Add a new column named `SourceURL` to the `OUTPUT_HEADER` in `processing.py`.
    *   When writing a row to the CSV, include the original question URL in this new column.
2.  **Enhance `process_question_data` Function (`processing.py`):**
    *   **Check for Existing CSV:** Before opening the output file, check if `output_csv_path` exists and is not empty.
    *   **Load Processed URLs:**
        *   If the CSV exists and has content, open it in read mode (`'r'`).
        *   Use `csv.DictReader` to read the file.
        *   Extract all values from the `SourceURL` column into a Python `set` called `processed_urls`. Handle potential `KeyError` if the column doesn't exist (e.g., in older files). Trust that URLs found indicate successful processing.
        *   If the CSV doesn't exist or is empty, initialize `processed_urls` as an empty set.
    *   **Open CSV for Writing/Appending:**
        *   Determine the open mode: `'a'` (append) if `processed_urls` is not empty, otherwise `'w'` (write).
        *   Open the `output_csv_path` using the determined mode, `newline=''`, and `encoding='utf-8'`.
        *   Create a `csv.writer`.
    *   **Write Header (if needed):** If the mode is `'w'`, write the updated `OUTPUT_HEADER` (including `SourceURL`).
    *   **Modify Processing Loop:**
        *   Iterate through the `scraped_items` list.
        *   For each `item`, get its `url`.
        *   **Check if Already Processed:** If `item['url']` is in the `processed_urls` set, `continue` to the next item (skip).
        *   **Process New Item:** If the URL is *not* in the set:
            *   Perform the existing fetch, parse, and data extraction logic.
            *   If processing is successful:
                *   Add the `item['url']` to the `extracted_data` dictionary under the key `SourceURL`.
                *   Prepare the `output_row` ensuring it includes the `SourceURL` value and matches the `OUTPUT_HEADER` order.
                *   Write the `output_row` to the CSV file.
                *   *(Optional but recommended)* Add the `item['url']` to the in-memory `processed_urls` set.
            *   If processing fails (error during fetch/parse): Log the error. **Do not** add the URL to the `processed_urls` set, allowing it to be retried on the next run.

## Workflow Diagram

```mermaid
graph TD
    A[Start scrape command] --> B{Output CSV Exists & Not Empty?};
    B -- Yes --> C[Read existing CSV];
    C --> D[Load processed URLs from 'SourceURL' column into Set];
    B -- No --> E[Initialize empty Set for processed URLs];
    D --> F[Mode = 'a' (Append)];
    E --> G[Mode = 'w' (Write)];
    F --> H[Open CSV in Append Mode];
    G --> H[Open CSV in Write Mode];
    H --> I{Mode == 'w'?};
    I -- Yes --> J[Write CSV Header (incl. 'SourceURL')];
    I -- No --> K{Iterate Scraped Items (URLs)};
    J --> K;
    K --> L[Get item URL];
    L --> M{URL in Processed Set?};
    M -- Yes --> N[Skip Item];
    M -- No --> O[Fetch & Process URL Data];
    O --> P{Processing Successful?};
    P -- Yes --> Q[Add SourceURL to data];
    Q --> R[Write Row to CSV];
    R --> S[Add URL to Processed Set (In-Memory)];
    P -- No --> T[Log Error];
    N --> U{More Items?};
    S --> U;
    T --> U;
    U -- Yes --> K;
    U -- No --> V[End Processing];
```

## Implementation Notes

*   Ensure robust error handling around file I/O and CSV parsing, especially when reading the existing CSV.
*   The `SourceURL` column should be added consistently to the header and data rows.