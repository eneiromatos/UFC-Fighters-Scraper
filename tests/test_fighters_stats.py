"""Offline tests against saved UFC.com pages.

The fixtures are real UFC.com pages trimmed to the parts the spider reads.
If UFC changes its markup, re-download them and these tests will show which
fields broke:
    python tests/update_fixtures.py
"""
import csv
import io
import logging
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, Request

from ufcstats import items
from ufcstats.exporters import FlatCsvItemExporter
from ufcstats.flatten import FLAT_FIELDS, flatten
from ufcstats.pipelines import FieldCoveragePipeline
from ufcstats.spiders.fighters_stats import FightersStatsSpider

FIXTURES = Path(__file__).parent / "fixtures"


def response_for(fixture, url, body=None):
    return HtmlResponse(
        url=url,
        body=body if body is not None else (FIXTURES / fixture).read_bytes(),
        encoding="utf-8",
        request=Request(url),
    )


def scrape(slug, body=None, **spider_kwargs):
    spider = FightersStatsSpider(**spider_kwargs)
    response = response_for(f"{slug}.html", f"https://www.ufc.com/athlete/{slug}", body)
    return list(spider.parse_fighter_bio(response))


@pytest.fixture(scope="module")
def jones():
    (fighter,) = scrape("jon-jones")
    return fighter


@pytest.fixture(scope="module")
def malik():
    (fighter,) = scrape("mansur-abdul-malik")
    return fighter


# --- extraction ---------------------------------------------------------------


def test_bio(jones):
    assert jones["name"] == "Jon Jones"
    assert jones["nick_name"] == "Bones"
    assert jones["division"] == "Heavyweight"
    assert jones["status"] == "Active"
    assert jones["place_of_birth"] == "Rochester, NY, United States"
    assert jones["trains_at"] == "Team Jones"
    assert jones["age"] == 38
    assert jones["height"] == 76.0
    assert jones["weight"] == 240
    assert jones["octagon_debut"] == "2008-08-09"
    assert jones["reach"] == 84.5
    assert jones["leg_reach"] == 45.0


def test_no_nickname_is_omitted(malik):
    assert "nick_name" not in malik
    assert malik["fighting_style"] == "Freestyle"


def test_records(malik):
    assert malik["records"] == {
        "wins": 9,
        "losses": 2,
        "draws": 1,
        "wins_by_knockout": 7,
        "wins_by_submission": 2,
        "first_round_finishes": 7,
    }


def test_main_stats(jones):
    stats = jones["fighter_stats"]
    assert stats["sig_strikes_defense"] == 64
    assert stats["takedown_defense"] == 95
    assert stats["knockdown_avg"] == 0.25
    assert stats["avg_fight_time_seconds"] == 14 * 60 + 52
    assert stats["win_by_method"] == {"ko_tko": 11, "dec": 10, "sub": 7}


def test_striking_stats(jones):
    assert jones["fighter_stats"]["striking_stats"] == {
        "accuracy": 59,
        "sig_strikes_landed": 1564,
        "sig_strikes_attempted": 2655,
        "sig_strikes_landed_per_min": 4.38,
        "sig_strikes_absorbed_per_min": 2.24,
        "sig_str_by_position": {"standing": 1012, "clinch": 250, "ground": 302},
        "sig_str_by_target": {"head": 759, "body": 375, "leg": 430},
    }


def test_grappling_stats(jones):
    assert jones["fighter_stats"]["grappling_stats"] == {
        "accuracy": 37,
        "takedowns_landed": 36,
        "takedowns_attempted": 98,
        "takedowns_avg_per_15_min": 1.89,
        "submission_avg_per_15_min": 0.46,
    }


def test_zero_counts_are_kept(malik):
    # 0 decision wins is real data, unlike a 0.00 height
    assert malik["fighter_stats"]["win_by_method"]["dec"] == 0


def test_blank_landed_with_zero_accuracy_is_zero(malik):
    # UFC renders an empty "Takedowns Landed" (instead of 0) for this fighter,
    # with 0% accuracy. The attempted count must not shift into the landed slot.
    grappling = malik["fighter_stats"]["grappling_stats"]
    assert grappling["accuracy"] == 0
    assert grappling["takedowns_landed"] == 0
    assert grappling["takedowns_attempted"] == 13


def test_blank_landed_with_nonzero_accuracy_stays_missing():
    page = (FIXTURES / "jon-jones.html").read_bytes()
    page = page.replace(b'c-overlap__stats-value">36<', b'c-overlap__stats-value"><')
    assert b'c-overlap__stats-value"><' in page
    (fighter,) = scrape("jon-jones", body=page)
    grappling = fighter["fighter_stats"]["grappling_stats"]
    assert "takedowns_landed" not in grappling
    assert grappling["takedowns_attempted"] == 98


def test_unknown_height_is_omitted():
    page = (FIXTURES / "jon-jones.html").read_bytes()
    page = page.replace(b'c-bio__text">76.00<', b'c-bio__text">0.00<')
    (fighter,) = scrape("jon-jones", body=page)
    assert "height" not in fighter


def test_active_only_filter():
    assert len(scrape("jon-jones", active_only="true")) == 1

    page = (FIXTURES / "jon-jones.html").read_bytes()
    retired = page.replace(b'c-bio__text">Active<', b'c-bio__text">Not Fighting<')
    assert scrape("jon-jones", body=retired, active_only="true") == []
    assert len(scrape("jon-jones", body=retired)) == 1


def test_listing_follows_profiles_and_next_page():
    spider = FightersStatsSpider()
    response = response_for("athletes-all.html", "https://www.ufc.com/athletes/all")
    urls = [r.url for r in spider.parse(response)]
    profiles = [u for u in urls if "/athlete/" in u]
    assert len(profiles) >= 10
    assert "https://www.ufc.com/athletes/all?page=1" in urls


# --- conversions --------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Aug. 9, 2008", "2008-08-09"),
        ("May. 18, 2019", "2019-05-18"),
        ("May 18, 2019", "2019-05-18"),
        ("Sept. 3, 2016", "2016-09-03"),
        ("soon", None),
    ],
)
def test_to_iso_date(text, expected):
    assert items.to_iso_date(text) == expected


@pytest.mark.parametrize("text, expected", [("14:52", 892), ("00:19", 19), ("n/a", None)])
def test_mmss_to_seconds(text, expected):
    assert items.mmss_to_seconds(text) == expected


# --- flattening, CSV, coverage -------------------------------------------------


def test_flatten(jones):
    flat = flatten(jones)
    assert flat["name"] == "Jon Jones"
    assert flat["wins"] == 28
    assert flat["striking_accuracy"] == 59
    assert flat["grappling_accuracy"] == 37
    assert flat["striking_sig_str_by_target_head"] == 759
    assert flat["win_by_method_ko_tko"] == 11
    assert not any(isinstance(v, dict) for v in flat.values())
    assert set(flat) <= set(FLAT_FIELDS)


def test_csv_export_has_every_column(jones, malik):
    out = io.BytesIO()
    exporter = FlatCsvItemExporter(out)
    exporter.start_exporting()
    # malik first: his missing nickname must not drop the column
    exporter.export_item(malik)
    exporter.export_item(jones)
    exporter.finish_exporting()

    rows = list(csv.DictReader(io.StringIO(out.getvalue().decode("utf-8"))))
    assert list(rows[0]) == FLAT_FIELDS
    assert rows[0]["nick_name"] == ""
    assert rows[1]["nick_name"] == "Bones"
    assert rows[1]["striking_sig_strikes_landed"] == "1564"


def test_coverage_report(jones, malik, caplog):
    spider = FightersStatsSpider()
    pipeline = FieldCoveragePipeline()
    pipeline.open_spider(spider)
    pipeline.process_item(jones, spider)
    pipeline.process_item(malik, spider)
    with caplog.at_level(logging.INFO):
        pipeline.close_spider(spider)

    assert pipeline.present["name"] == 2
    assert pipeline.present["nick_name"] == 1
    assert "Field coverage" in caplog.text
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_coverage_warns_when_ufc_layout_changes(jones, caplog):
    spider = FightersStatsSpider()
    pipeline = FieldCoveragePipeline()
    pipeline.open_spider(spider)
    broken = dict(jones)
    del broken["division"]
    pipeline.process_item(broken, spider)
    with caplog.at_level(logging.INFO):
        pipeline.close_spider(spider)

    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("'division'" in w for w in warnings)
