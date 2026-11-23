import re

from itemloaders import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst
from scrapy import Field, Item

# Fields holding a nested item declare it with Field(nested=...), so the CSV
# exporter and coverage report can work out every column up front.


class RecordsItem(Item):
    wins = Field()
    losses = Field()
    draws = Field()
    fight_win_streak = Field()
    wins_by_knockout = Field()
    wins_by_submission = Field()
    wins_by_decision = Field()
    first_round_finishes = Field()
    title_defenses = Field()


class WinByMethodItem(Item):
    ko_tko = Field()
    dec = Field()
    sub = Field()


class StrTargetItem(Item):
    head = Field()
    body = Field()
    leg = Field()


class StrPositionItem(Item):
    standing = Field()
    clinch = Field()
    ground = Field()


class GrapplingStatsItem(Item):
    accuracy = Field()
    takedowns_landed = Field()
    takedowns_attempted = Field()
    takedowns_avg_per_15_min = Field()
    submission_avg_per_15_min = Field()


class StrikingStatsItem(Item):
    accuracy = Field()
    sig_strikes_landed = Field()
    sig_strikes_attempted = Field()
    sig_strikes_landed_per_min = Field()
    sig_strikes_absorbed_per_min = Field()
    sig_str_by_position = Field(nested=StrPositionItem)
    sig_str_by_target = Field(nested=StrTargetItem)


class MainFighterStatsItem(Item):
    knockdown_avg = Field()
    avg_fight_time_seconds = Field()
    sig_strikes_defense = Field()
    takedown_defense = Field()
    striking_stats = Field(nested=StrikingStatsItem)
    grappling_stats = Field(nested=GrapplingStatsItem)
    win_by_method = Field(nested=WinByMethodItem)


class FighterBioItem(Item):
    profile_url = Field()
    name = Field()
    nick_name = Field()
    status = Field()
    division = Field()
    place_of_birth = Field()
    trains_at = Field()
    fighting_style = Field()
    age = Field()
    height = Field()
    weight = Field()
    octagon_debut = Field()
    reach = Field()
    leg_reach = Field()
    records = Field(nested=RecordsItem)
    fighter_stats = Field(nested=MainFighterStatsItem)


# --- text cleanup -----------------------------------------------------------


def clean_text(text):
    """Collapse whitespace and drop the quotes UFC wraps nicknames in."""
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip('"').strip()


def clean_parenthesis(text):
    """'89 (49%)' -> '89'"""
    return re.sub(r"\s*\(\s*\d*\s*%\s*\)", "", text).strip()


def clean_division(text):
    """'Middleweight Division' -> 'Middleweight'"""
    return re.sub(r"\s+Division$", "", text)


def drop_empty(text):
    return text or None


# --- conversion to numbers ----------------------------------------------------
# Each returns None when the text isn't a number; None values are dropped, so
# the field is left out rather than holding a half-parsed value.


def to_int(text):
    """'185 lbs' -> 185, '46%' -> 46, '1,564' -> 1564"""
    match = re.search(r"-?\d+", text.replace(",", ""))
    return int(match.group()) if match else None


def to_float(text):
    """'4.38' -> 4.38"""
    match = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(match.group()) if match else None


def nonzero(value):
    """UFC shows '0.00' for an unknown height/reach; treat it as missing."""
    return value or None


def mmss_to_seconds(text):
    """'14:52' -> 892"""
    match = re.fullmatch(r"(\d+):(\d{2})", text.strip())
    return int(match.group(1)) * 60 + int(match.group(2)) if match else None


MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]


def to_iso_date(text):
    """'Aug. 9, 2008' -> '2008-08-09'"""
    match = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{1,2}),\s*(\d{4})", text.strip())
    if not match:
        return None
    month = match.group(1)[:3].lower()
    if month not in MONTHS:
        return None
    return f"{match.group(3)}-{MONTHS.index(month) + 1:02d}-{int(match.group(2)):02d}"


TEXT = MapCompose(clean_text, drop_empty)
INT = MapCompose(clean_text, drop_empty, to_int)
FLOAT = MapCompose(clean_text, drop_empty, to_float)
NESTED = MapCompose()  # already-built dicts pass through untouched


# --- loaders ------------------------------------------------------------------


class FighterItemLoader(ItemLoader):
    default_input_processor = TEXT
    default_output_processor = TakeFirst()


class FighterBioItemLoader(FighterItemLoader):
    default_item_class = FighterBioItem
    division_in = MapCompose(clean_text, clean_division, drop_empty)
    age_in = INT
    height_in = MapCompose(clean_text, drop_empty, to_float, nonzero)
    weight_in = MapCompose(clean_text, drop_empty, to_int, nonzero)
    reach_in = MapCompose(clean_text, drop_empty, to_float, nonzero)
    leg_reach_in = MapCompose(clean_text, drop_empty, to_float, nonzero)
    octagon_debut_in = MapCompose(clean_text, drop_empty, to_iso_date)
    records_in = NESTED
    fighter_stats_in = NESTED


class MainFighterStatsItemLoader(FighterItemLoader):
    default_item_class = MainFighterStatsItem
    knockdown_avg_in = FLOAT
    avg_fight_time_seconds_in = MapCompose(clean_text, drop_empty, mmss_to_seconds)
    sig_strikes_defense_in = INT
    takedown_defense_in = INT
    striking_stats_in = NESTED
    grappling_stats_in = NESTED
    win_by_method_in = NESTED


class StrikingStatsItemLoader(FighterItemLoader):
    default_item_class = StrikingStatsItem
    default_input_processor = INT
    sig_strikes_landed_per_min_in = FLOAT
    sig_strikes_absorbed_per_min_in = FLOAT
    sig_str_by_position_in = NESTED
    sig_str_by_target_in = NESTED


class GrapplingStatsItemLoader(FighterItemLoader):
    default_item_class = GrapplingStatsItem
    default_input_processor = INT
    takedowns_avg_per_15_min_in = FLOAT
    submission_avg_per_15_min_in = FLOAT


class StrPositionItemLoader(FighterItemLoader):
    default_item_class = StrPositionItem
    default_input_processor = MapCompose(clean_text, clean_parenthesis, drop_empty, to_int)


class StrTargetItemLoader(FighterItemLoader):
    default_item_class = StrTargetItem
    default_input_processor = INT


class WinByMethodItemLoader(FighterItemLoader):
    default_item_class = WinByMethodItem
    default_input_processor = MapCompose(clean_text, clean_parenthesis, drop_empty, to_int)


class RecordsItemLoader(FighterItemLoader):
    default_item_class = RecordsItem
    default_input_processor = INT
