from collections import Counter

from .flatten import FLAT_FIELDS, flatten

# Fields that nearly every fighter has (>95% in a full run). If one of these
# drops below EXPECTED_MIN_COVERAGE, UFC has most likely changed its pages.
EXPECTED_FIELDS = [
    "name",
    "status",
    "division",
    "weight",
    "wins",
    "striking_sig_str_by_target_head",
]
EXPECTED_MIN_COVERAGE = 0.5


class FieldCoveragePipeline:
    """Report, at the end of a run, how many fighters had each field."""

    def open_spider(self, spider):
        self.total = 0
        self.present = Counter()

    def process_item(self, item, spider):
        self.total += 1
        self.present.update(
            key for key, value in flatten(item).items() if value not in (None, "")
        )
        return item

    def close_spider(self, spider):
        if not self.total:
            spider.logger.warning("No fighters were scraped.")
            return

        width = max(len(field) for field in FLAT_FIELDS)
        lines = [
            f"  {field:<{width}}  {self.present[field]:>6}/{self.total}"
            f"  {self.present[field] / self.total:>4.0%}"
            for field in FLAT_FIELDS
        ]
        spider.logger.info(
            "Field coverage (fighters with each field):\n%s", "\n".join(lines)
        )

        for field in EXPECTED_FIELDS:
            coverage = self.present[field] / self.total
            if coverage < EXPECTED_MIN_COVERAGE:
                spider.logger.warning(
                    "Only %d/%d fighters have '%s'. UFC.com has probably changed "
                    "its page layout; see the README's Tests section.",
                    self.present[field],
                    self.total,
                    field,
                )
