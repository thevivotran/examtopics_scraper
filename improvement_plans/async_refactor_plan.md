# Plan: Refactor process_data.py for Asynchronous Processing

**Goal:** Improve the performance of `process_data.py` by refactoring it to use asynchronous I/O (`asyncio` and `aiohttp`) for fetching URLs concurrently, while limiting the number of simultaneous requests to avoid overwhelming the target server.

**Analysis of Current Script:**

*   Reads URLs from a CSV file.
*   Iterates through each URL, making a synchronous HTTP request using the `requests` library.
*   Parses the HTML response using `lxml` and XPath.
*   Writes the results to an output CSV.
*   The primary bottleneck is the sequential nature of the `requests.get()` calls.

**Proposed Asynchronous Refactoring with Concurrency Limit:**

*   **Libraries:** `asyncio`, `aiohttp`.
*   **Concurrency Limit:** Use `asyncio.Semaphore(10)` to limit simultaneous requests to 10.
*   **Core Changes:**
    *   Modify the main processing function (`process_csv`) to be an `async` function.
    *   Introduce an `asyncio.Semaphore(10)` within `process_csv`.
    *   Create an `async` helper function (`fetch_and_extract`) that accepts the `aiohttp.ClientSession`, URL, and `semaphore`.
    *   Wrap the network request within `fetch_and_extract` using `async with semaphore:`.
    *   In `process_csv`, create an `aiohttp.ClientSession`.
    *   Read the input CSV and create a list of `asyncio` tasks, each calling `fetch_and_extract`.
    *   Use `asyncio.gather` to run tasks concurrently (managed by the semaphore).
    *   Process results and write to the output CSV.
    *   Update `if __name__ == "__main__":` to use `asyncio.run()`.

**Benefits:**

*   **Performance:** Significant speedup compared to the sequential version.
*   **Efficiency:** Better resource utilization.
*   **Server Friendliness:** Controlled concurrency reduces the risk of overloading the server or getting blocked.

**Considerations:**

*   **Error Handling:** Robust error handling within each task is essential.
*   **Dependencies:** `aiohttp` needs to be added as a project dependency.

**Workflow Diagram:**

```mermaid
graph TD
    A[Start process_csv] --> B[Create Semaphore(limit=10)];
    B --> C{Read Input CSV};
    C --> D{Create aiohttp Session};
    D --> E[Loop through URLs];
    E --> F{Create async task for URL};
    F --> G[fetch_and_extract (async)];
    G --> H{Acquire Semaphore (await)};
    H --> I{aiohttp.get (await)};
    I --> J{Parse HTML};
    J --> K{Extract Data};
    K --> L{Release Semaphore};
    L --> M[Return Extracted Data];
    E --> D; subgraph Concurrent Tasks (Limited by Semaphore)
    direction TB
    T1[Task 1: fetch_and_extract(url1)]
    T2[Task 2: fetch_and_extract(url2)]
    T3[...]
    T1 --> R1{Result 1}
    T2 --> R2{Result 2}
    T3 --> R3{...}
    end
    D -- All URLs processed --> N{asyncio.gather(tasks)};
    N --> O[Collect Results];
    O --> P{Write Output CSV};
    P --> Q[End];

    style G fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#ff9,stroke:#333,stroke-width:2px
    style I fill:#ccf,stroke:#333,stroke-width:2px
    style L fill:#ff9,stroke:#333,stroke-width:2px
    style N fill:#f9f,stroke:#333,stroke-width:2px