import csv
import os
from typing import List, Dict, Any

import itemadapter


class ScrapyPipeline:
    """Base Scrapy pipeline item."""

    def process_item(self, item, spider):
        raise NotImplementedError


class ExamtopicsExamsStdoutPipeline(ScrapyPipeline):
    """Stdout exporter for ExamTopics exams."""

    def process_item(self, item, spider):
        dict_item = itemadapter.ItemAdapter(item).asdict()
        # Ensure 'code' and 'name' exist before printing
        code = dict_item.get('code', 'N/A')
        name = dict_item.get('name', 'N/A')
        print(f"{code}: {name}") # Added colon for clarity
        return item


class ExamtopicsQuestionsStdoutPipeline(ScrapyPipeline):
    """Stdout exporter for ExamTopics question discussions."""

    def process_item(self, item, spider):
        print(itemadapter.ItemAdapter(item).asdict().get('url', 'URL not found')) # Safer access
        return item


class ExamtopicsQuestionsCsvPipeline(ScrapyPipeline):
    """CSV exporter for ExamTopics question discussions (id, url)."""

    def __init__(self, output_file):
        self.output_file = output_file
        self.file_handle = None
        self.csv_writer = None

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get('CSV_OUTPUT_PATH')
        if not output_file:
            raise ValueError("CSV_OUTPUT_PATH setting is required for ExamtopicsQuestionsCsvPipeline")
        # Ensure the directory exists before returning the instance
        output_dir = os.path.dirname(output_file)
        if output_dir: # Only create if path includes a directory
            os.makedirs(output_dir, exist_ok=True)
        return cls(output_file=output_file)

    def open_spider(self, spider):
        try:
            self.file_handle = open(self.output_file, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file_handle)
            self.csv_writer.writerow(['id', 'url'])  # Write header
        except IOError as e:
            spider.logger.error(f"Failed to open CSV file {self.output_file}: {e}")
            self.file_handle = None # Ensure handle is None if open fails
            self.csv_writer = None

    def close_spider(self, spider):
        if self.file_handle:
            self.file_handle.close()

    def process_item(self, item, spider):
        if not self.csv_writer:
            spider.logger.warning("CSV writer not available, skipping item.")
            return item # Drop item if file couldn't be opened

        adapter = itemadapter.ItemAdapter(item)
        # Use 'question' field as 'id' if available, otherwise use a placeholder or log
        item_id = adapter.get('question', f"ID_MISSING_{adapter.get('url', 'NO_URL')}")
        row = [item_id, adapter.get('url')]
        try:
            self.csv_writer.writerow(row)
        except Exception as e:
             spider.logger.error(f"Failed to write row to CSV: {row} - {e}")
        return item

# --- New Pipeline ---
class ItemCollectorPipeline:
    """
    A Scrapy pipeline that collects all processed items into an in-memory list.
    The collected items can be accessed via the `items` attribute after the
    spider has finished running.
    """
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def open_spider(self, spider):
        self.items = [] # Ensure list is clear for each run
        spider.logger.info("ItemCollectorPipeline opened.")

    def close_spider(self, spider):
        spider.logger.info(f"ItemCollectorPipeline closed. Collected {len(self.items)} items.")

    def process_item(self, item, spider):
        adapter = itemadapter.ItemAdapter(item)
        # Adapt the item to a dictionary and append.
        # Ensure 'question' is used as 'id' for consistency with CSV pipeline logic
        item_dict = adapter.asdict()
        item_id = item_dict.get('question', f"ID_MISSING_{item_dict.get('url', 'NO_URL')}")
        processed_item = {'id': item_id, 'url': item_dict.get('url')}
        self.items.append(processed_item)
        return item # Return item for potential further processing by other pipelines

# Removed generate_questions_html_exporter and ExamtopicsQuestionsHtmlPipeline
