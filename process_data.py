import argparse
import csv
import sys
import requests
import random # Added import
from lxml import html

# Define XPaths for data extraction
XPATHS = {
    'Question': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/p/text()',
    'Correct Answer': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[3]/span[1]/span/text()',
    'Answer 1': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[1]/text()',
    'Answer 2': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[2]/text()',
    'Answer 3': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[3]/text()',
    'Answer 4': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[4]/text()',
    'Answer 5': '/html/body/div[2]/div/div[4]/div/div[1]/div[2]/div[2]/ul/li[5]/text()', # Optional
}

# Define the header for the output CSV
# OUTPUT_HEADER = ['id', 'url', 'Question', 'Correct Answer', 'Answer 1', 'Answer 2', 'Answer 3', 'Answer 4', 'Answer 5']
OUTPUT_HEADER = ['Question', 'Correct Answer', 'Answer 1', 'Answer 2', 'Answer 3', 'Answer 4', 'Answer 5']


# Define a list of User-Agent strings
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


def extract_data(tree, xpath):
    """Safely extracts text content using XPath."""
    try:
        result = tree.xpath(xpath)
        # XPath for text() might return a list of strings, join them if needed, or just take the first.
        # Handle cases where the result might be empty or contain whitespace.
        if result:
            # Join potentially fragmented text nodes and strip whitespace
            return "".join(result).strip()
        else:
            return "" # Return empty string if XPath yields no result
    except Exception as e:
        # Log XPath extraction errors specifically if needed, though lxml errors are less common here
        # print(f"XPath extraction error for {xpath}: {e}", file=sys.stderr)
        return "" # Return empty string on error

def process_csv(input_csv_path, output_csv_path):
    """
    Reads the input CSV, fetches data from URLs, and writes to the output CSV.
    """
    print(f"Processing input CSV: {input_csv_path}")
    print(f"Writing output CSV: {output_csv_path}")

    try:
        with open(input_csv_path, 'r', newline='', encoding='utf-8') as infile, \
             open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Write the header to the output file
            writer.writerow(OUTPUT_HEADER)

            # Skip the header row of the input file
            try:
                next(reader)
            except StopIteration:
                print("Input CSV is empty or has no header.", file=sys.stderr)
                return # Exit if no data rows

            processed_count = 0
            error_count = 0
            for row_num, row in enumerate(reader, start=2): # Start row count from 2 for logging
                if len(row) < 2:
                    print(f"Skipping malformed row {row_num}: {row}", file=sys.stderr)
                    continue

                input_id, input_url = row[0], row[1]
                extracted_data = {'id': input_id, 'url': input_url}
                fetch_successful = False

                # Initialize data fields to empty strings
                for key in OUTPUT_HEADER[2:]: # Question, Answers...
                    extracted_data[key] = ""

                # --- Fetch ---
                try:
                    # Select a random User-Agent for this request
                    random_user_agent = random.choice(USER_AGENTS)
                    headers = {'User-Agent': random_user_agent}

                    response = requests.get(input_url, headers=headers, timeout=10) # Increased timeout slightly
                    response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
                    fetch_successful = True
                except requests.exceptions.Timeout:
                    print(f"Timeout fetching URL (Row {row_num}): {input_url}", file=sys.stderr)
                    error_count += 1
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching URL (Row {row_num}): {input_url} - {e}", file=sys.stderr)
                    error_count += 1

                # --- Parse & Extract ---
                if fetch_successful:
                    try:
                        tree = html.fromstring(response.content)
                        # Extract data using defined XPaths
                        for key, xpath in XPATHS.items():
                            extracted_data[key] = extract_data(tree, xpath)

                    except Exception as e:
                        # Catch potential parsing errors from lxml
                        print(f"Error parsing HTML (Row {row_num}): {input_url} - {e}", file=sys.stderr)
                        error_count += 1
                        # Ensure data fields remain empty if parsing fails mid-way
                        for key in OUTPUT_HEADER[2:]:
                            if key not in extracted_data or extracted_data[key] is None:
                                extracted_data[key] = ""

                # --- Process Correct Answer (Refactored) ---
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
                    # Append the answer text if the key was valid (A-E) and text was found (even if empty)
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
                    print(f"Processed {processed_count} rows...")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading/writing file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nProcessing complete.")
    print(f"Total rows processed: {processed_count}")
    print(f"Rows with fetch/parse errors: {error_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch details from URLs listed in a CSV file "
                                                 "generated by the ExamTopics scraper.")
    parser.add_argument("input_csv", help="Path to the input CSV file (containing id, url).")
    parser.add_argument("output_csv", help="Path to the output CSV file for detailed results.")
    args = parser.parse_args()

    process_csv(args.input_csv, args.output_csv)