import csv
import os

import itemadapter


class ScrapyPipeline:
    """Base Scrapy pipeline item."""

    def process_item(self, item, spider):
        raise NotImplementedError


class ExamtopicsExamsStdoutPipeline(ScrapyPipeline):
    """Stdout exporter for ExamTopics exams."""

    def process_item(self, item, spider):
        dict_item = itemadapter.ItemAdapter(item).asdict()
        print(f"{dict_item['code']}{dict_item['name']}")
        return item


class ExamtopicsQuestionsStdoutPipeline(ScrapyPipeline):
    """Stdout exporter for ExamTopics question discussions."""

    def process_item(self, item, spider):
        print(itemadapter.ItemAdapter(item).asdict()['url'])
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
        return cls(output_file=output_file)

    def open_spider(self, spider):
        # Ensure the directory exists
        # print(self.output_file)
        # os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        self.file_handle = open(self.output_file, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.file_handle)
        self.csv_writer.writerow(['id', 'url'])  # Write header

    def close_spider(self, spider):
        if self.file_handle:
            self.file_handle.close()

    def process_item(self, item, spider):
        adapter = itemadapter.ItemAdapter(item)
        # Use 'question' field as 'id'
        row = [adapter.get('question'), adapter.get('url')]
        if self.csv_writer:
            self.csv_writer.writerow(row)
        return item

# Removed generate_questions_html_exporter and ExamtopicsQuestionsHtmlPipeline
