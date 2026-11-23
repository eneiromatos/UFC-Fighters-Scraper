"""Offline tests against saved UFC.com pages.

If UFC changes its markup, re-download the fixtures and these tests will show
which fields broke:
    curl -sL -A "Mozilla/5.0" https://www.ufc.com/athlete/jon-jones -o tests/fixtures/jon-jones.html
"""
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, Request

from ufcstats.spiders.fighters_stats import FightersStatsSpider

FIXTURES = Path(__file__).parent / "fixtures"


def response_for(fixture, url):
    return HtmlResponse(
        url=url,
        body=(FIXTURES / fixture).read_bytes(),
        encoding="utf-8",
        request=Request(url),
    )


def scrape(slug, **spider_kwargs):
    spider = FightersStatsSpider(**spider_kwargs)
    response = response_for(f"{slug}.html", f"https://www.ufc.com/athlete/{slug}")
    return [dict(item) for item in spider.parse_fighter_bio(response)]


@pytest.fixture(scope="module")
def jones():
    (fighter,) = scrape("jon-jones")
    return fighter


@pytest.fixture(scope="module")
def malik():
    (fighter,) = scrape("mansur-abdul-malik")
    return fighter


def test_bio(jones):
    assert jones["name"] == "Jon Jones"
    assert jones["nick_name"] == "Bones"
    assert jones["division"] == "Heavyweight"
    assert jones["status"] == "Active"
    assert jones["place_of_birth"] == "Rochester, NY, United States"
    assert jones["trains_at"] == "Team Jones"
    assert jones["age"] == "38"
    assert jones["height"] == "76.00"
    assert jones["weight"] == "240 lbs"
    assert jones["octagon_debut"] == "Aug. 9, 2008"
    assert jones["reach"] == "84.50"
    assert jones["leg_reach"] == "45.00"


def test_no_nickname_is_omitted(malik):
    assert "nick_name" not in malik
    assert malik["fighting_style"] == "Freestyle"


def test_records(malik):
    assert malik["records"] == {
        "wins": "9",
        "losses": "2",
        "draws": "1",
        "wins_by_knockout": "7",
        "wins_by_submission": "2",
        "first_round_finishes": "7",
    }


def test_main_stats(jones):
    stats = jones["fighter_stats"]
    assert stats["sig_strikes_defense"] == "64"
    assert stats["takedown_defense"] == "95"
    assert stats["knockdown_avg"] == "0.25"
    assert stats["avg_fight_time"] == "14:52"
    assert stats["win_by_method"] == {"ko_tko": "11", "dec": "10", "sub": "7"}


def test_striking_stats(jones):
    striking = jones["fighter_stats"]["striking_stats"]
    assert striking["accuracy"] == "59"
    assert striking["sig_strikes_landed"] == "1564"
    assert striking["sig_strikes_attempted"] == "2655"
    assert striking["sig_strikes_landed_per_min"] == "4.38"
    assert striking["sig_strikes_absorbed_per_min"] == "2.24"
    assert striking["sig_str_by_position"] == {
        "standing": "1012",
        "clinch": "250",
        "ground": "302",
    }
    assert striking["sig_str_by_target"] == {"head": "759", "body": "375", "leg": "430"}


def test_grappling_stats(jones):
    assert jones["fighter_stats"]["grappling_stats"] == {
        "accuracy": "37",
        "takedowns_landed": "36",
        "takedowns_attempted": "98",
        "takedowns_avg_per_15_min": "1.89",
        "submission_avg_per_15_min": "0.46",
    }


def test_blank_value_is_omitted_not_misaligned(malik):
    # UFC renders an empty "Takedowns Landed" for this fighter; the attempted
    # count must not shift into the landed slot.
    grappling = malik["fighter_stats"]["grappling_stats"]
    assert "takedowns_landed" not in grappling
    assert grappling["takedowns_attempted"] == "13"


def test_active_only_filter():
    assert len(scrape("jon-jones", active_only="true")) == 1

    url = "https://www.ufc.com/athlete/jon-jones"
    retired = response_for("jon-jones.html", url).replace(
        body=(FIXTURES / "jon-jones.html")
        .read_bytes()
        .replace(b'c-bio__text">Active<', b'c-bio__text">Not Fighting<')
    )
    assert list(FightersStatsSpider(active_only="true").parse_fighter_bio(retired)) == []
    assert len(list(FightersStatsSpider().parse_fighter_bio(retired))) == 1


def test_listing_follows_profiles_and_next_page():
    spider = FightersStatsSpider()
    response = response_for("athletes-all.html", "https://www.ufc.com/athletes/all")
    urls = [r.url for r in spider.parse(response)]
    profiles = [u for u in urls if "/athlete/" in u]
    assert len(profiles) >= 10
    assert "https://www.ufc.com/athletes/all?page=1" in urls
