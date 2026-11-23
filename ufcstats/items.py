import re

from itemloaders import ItemLoader
from itemloaders.processors import Compose, MapCompose, TakeFirst
from scrapy import Field, Item


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
    sig_str_by_position = Field()
    sig_str_by_target = Field()


class MainFighterStatsItem(Item):
    knockdown_avg = Field()
    avg_fight_time = Field()
    sig_strikes_defense = Field()
    takedown_defense = Field()
    win_by_method = Field()
    striking_stats = Field()
    grappling_stats = Field()


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
    records = Field()
    fighter_stats = Field()


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


def clean_percent(text):
    return text.rstrip("%").strip()


def drop_empty(text):
    return text or None


class FighterItemLoader(ItemLoader):
    default_input_processor = MapCompose(clean_text, drop_empty)
    default_output_processor = TakeFirst()


class FighterBioItemLoader(FighterItemLoader):
    default_item_class = FighterBioItem
    division_in = MapCompose(clean_text, clean_division, drop_empty)
    records_in = MapCompose()
    fighter_stats_in = MapCompose()


class MainFighterStatsItemLoader(FighterItemLoader):
    default_item_class = MainFighterStatsItem
    striking_stats_in = MapCompose()
    grappling_stats_in = MapCompose()
    win_by_method_in = MapCompose()


class StrikingStatsItemLoader(FighterItemLoader):
    default_item_class = StrikingStatsItem
    accuracy_in = MapCompose(clean_text, clean_percent, drop_empty)
    sig_str_by_position_in = MapCompose()
    sig_str_by_target_in = MapCompose()


class GrapplingStatsItemLoader(FighterItemLoader):
    default_item_class = GrapplingStatsItem
    accuracy_in = MapCompose(clean_text, clean_percent, drop_empty)


class StrPositionItemLoader(FighterItemLoader):
    default_item_class = StrPositionItem
    default_input_processor = MapCompose(clean_text, clean_parenthesis, drop_empty)


class StrTargetItemLoader(FighterItemLoader):
    default_item_class = StrTargetItem


class WinByMethodItemLoader(FighterItemLoader):
    default_item_class = WinByMethodItem
    default_input_processor = MapCompose(clean_text, clean_parenthesis, drop_empty)


class RecordsItemLoader(FighterItemLoader):
    default_item_class = RecordsItem
