import csv
import sys
import requests
import random
from lxml import html
from typing import List, Dict, Any

# Define XPaths for data extraction (copied from process_data.py)
XPATHS = {
    'Question': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/p/text()',
    'Correct Answer': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[3]/span[1]/span/text()',
    'Answer 1': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[1]/text()',
    'Answer 2': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[2]/text()',
    'Answer 3': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[3]/text()',
    'Answer 4': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[4]/text()',
    'Answer 5': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[5]/text()', # Optional
}

# Define the header for the output CSV (copied from process_data.py)
OUTPUT_HEADER = ['Question', 'Correct Answer', 'Answer 1', 'Answer 2', 'Answer 3', 'Answer 4', 'Answer 5']

# Define a list of User-Agent strings (copied from process_data.py)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
]


def extract_data(tree, xpath: str) -> str:
    """Safely extracts text content using XPath."""
    try:
        result = tree.xpath(xpath)
        if result:
            # Join potentially fragmented text nodes and strip whitespace
            return "".join(result).strip()
        else:
            return "" # Return empty string if XPath yields no result
    except Exception as e:
        # Log XPath extraction errors specifically if needed
        # print(f"XPath extraction error for {xpath}: {e}", file=sys.stderr)
        return "" # Return empty string on error


def process_question_data(scraped_items: List[Dict[str, Any]], output_csv_path: str):
    """
    Fetches detailed question data based on scraped URLs, processes it,
    and writes the results to a CSV file.

    Args:
        scraped_items: A list of dictionaries, where each dictionary
                       contains at least 'id' and 'url' keys from the
                       initial scraping phase.
        output_csv_path: The path to the CSV file where the processed
                         data will be written.
    """
    print(f"Processing {len(scraped_items)} scraped items...")
    print(f"Writing output CSV to: {output_csv_path}")

    processed_count = 0
    error_count = 0

    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(OUTPUT_HEADER) # Write header

            for item_num, item in enumerate(scraped_items, start=1):
                input_id = item.get('id', 'N/A') # Get id if available
                input_url = item.get('url')

                if not input_url:
                    print(f"Skipping item {item_num} due to missing URL.", file=sys.stderr)
                    error_count += 1
                    continue

                extracted_data: Dict[str, Any] = {'id': input_id, 'url': input_url} # Keep original id/url if needed later
                fetch_successful = False

                # Initialize data fields to empty strings based on OUTPUT_HEADER
                for key in OUTPUT_HEADER:
                    extracted_data[key] = ""

                # --- Fetch ---
                try:
                    random_user_agent = random.choice(USER_AGENTS)
                    headers = {'User-Agent': random_user_agent}
                    response = requests.get(input_url, headers=headers, timeout=15) # Slightly longer timeout
                    response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
                    fetch_successful = True
                except requests.exceptions.Timeout:
                    print(f"Timeout fetching URL (Item {item_num}, ID: {input_id}): {input_url}", file=sys.stderr)
                    error_count += 1
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching URL (Item {item_num}, ID: {input_id}): {input_url} - {e}", file=sys.stderr)
                    error_count += 1

                # --- Parse & Extract ---
                if fetch_successful:
                    try:
                        # Ensure response content is not None before parsing
                        if response.content:
                            tree = html.fromstring(response.content)
                            # Extract data using defined XPaths
                            for key, xpath in XPATHS.items():
                                extracted_data[key] = extract_data(tree, xpath)
                        else:
                             print(f"Empty content received (Item {item_num}, ID: {input_id}): {input_url}", file=sys.stderr)
                             error_count += 1

                    except Exception as e:
                        # Catch potential parsing errors from lxml
                        print(f"Error parsing HTML (Item {item_num}, ID: {input_id}): {input_url} - {e}", file=sys.stderr)
                        error_count += 1
                        # Ensure data fields remain empty if parsing fails mid-way
                        for key in OUTPUT_HEADER:
                            if key not in extracted_data or extracted_data[key] is None:
                                extracted_data[key] = ""

                # --- Process Correct Answer (Adapted from process_data.py) ---
                correct_answer_key = extracted_data.get('Correct Answer', '').strip().upper() # Normalize key

                # Create a mapping from answer key ('A', 'B', ...) to the extracted answer text
                answer_map = {
                    'A': extracted_data.get('Answer 1', ''),
                    'B': extracted_data.get('Answer 2', ''),
                    'C': extracted_data.get('Answer 3', ''),
                    'D': extracted_data.get('Answer 4', ''),
                    'E': extracted_data.get('Answer 5', '')
                }

                # Build the final correct answer string dynamically
                result_answers = []
                for char_key in correct_answer_key:
                    # Get the answer corresponding to the character key from the map
                    answer_text = answer_map.get(char_key)
                    # Append the answer text if the key was valid (A-E) and text was found
                    if answer_text is not None:
                         # Only append non-empty answers to avoid extra newlines for missing optional answers
                         if answer_text:
                            result_answers.append(answer_text)

                # Join the collected answers with newline characters
                # If correct_answer_key was invalid or all corresponding answers were empty, this will be empty.
                extracted_data['Correct Answer'] = "; ".join(result_answers)

                # --- Write ---
                # Ensure the order matches OUTPUT_HEADER
                output_row = [extracted_data.get(col, "") for col in OUTPUT_HEADER]
                writer.writerow(output_row)
                processed_count += 1

                # Optional: Print progress
                if processed_count % 50 == 0:
                    print(f"Processed {processed_count} items...")

    except IOError as e:
        print(f"Error writing to output file {output_csv_path}: {e}", file=sys.stderr)
        # Decide if this should halt the whole process or just log
        # For now, we let the exception propagate up if needed.
        raise # Re-raise the exception for the caller (Typer command) to handle
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}", file=sys.stderr)
        raise # Re-raise

    print(f"\nProcessing complete.")
    print(f"Total items processed successfully: {processed_count}")
    print(f"Items with fetch/parse errors: {error_count}")