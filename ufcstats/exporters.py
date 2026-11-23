from scrapy.exporters import CsvItemExporter

from .flatten import FLAT_FIELDS, flatten


class FlatCsvItemExporter(CsvItemExporter):
    """CSV with one column per stat instead of nested dicts in a cell.

    Always writes every column (in FLAT_FIELDS order), so the header doesn't
    depend on which fields the first fighter happens to have.
    """

    def __init__(self, file, **kwargs):
        if not kwargs.get("fields_to_export"):
            kwargs["fields_to_export"] = FLAT_FIELDS
        super().__init__(file, **kwargs)

    def export_item(self, item):
        super().export_item(flatten(item))
