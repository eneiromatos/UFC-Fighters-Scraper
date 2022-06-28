import re
from scrapy import Item, Field
from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst, Compose


class PecordsItem(Item):
    fight_win_streak = Field()
    wins_by_knockout = Field()
    wins_by_submission = Field()
    wins_by_decision = Field()
    first_round_finishes = Field()
    title_defenses = Field()


class WinWayItem(Item):
    ko_tko = Field()
    dec = Field()
    sub = Field()


class StrTargetItem(Item):
    head = Field()
    body = Field()
    leg = Field()


class StrPossitionItem(Item):
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
    knockdown_ratio = Field()
    avg_fight_time = Field()
    sig_strikes_defense = Field()
    takedown_defense = Field()
    win_by_way = Field()
    strinking_stats = Field()
    grappling_stats = Field()


class FighterBioItem(Item):
    profile_url = Field()
    name = Field()
    nick_name = Field()
    status = Field()
    division = Field()
    hometown = Field()
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


def clean_text(text: str):
    text = text.strip().replace('"', "")
    text = re.sub(r"\n *", " ", text)
    return text


def clean_parenthesis(text: str):
    text = re.sub(r" \(\d*%\)| \(\d* %\)", "", text)
    return text


class FighterItemLoader(ItemLoader):
    default_output_processor = Compose(TakeFirst(), clean_text)


class FighterBioItemLoader(FighterItemLoader):
    default_item_class = FighterBioItem
    records_out = TakeFirst()
    fighter_stats_out = TakeFirst()


class MainFighterStatsItemLoader(FighterItemLoader):
    default_item_class = MainFighterStatsItem
    strinking_stats_out = TakeFirst()
    grappling_stats_out = TakeFirst()
    win_by_way_out = TakeFirst()


class StrikingStatsItemLoader(FighterItemLoader):
    default_item_class = StrikingStatsItem
    sig_str_by_position_out = TakeFirst()
    sig_str_by_target_out = TakeFirst()


class GrapplingStatsItemLoader(FighterItemLoader):
    default_item_class = GrapplingStatsItem


class StrPossitionItemLoader(FighterItemLoader):
    default_output_processor = Compose(TakeFirst(), clean_text, clean_parenthesis)
    default_item_class = StrPossitionItem


class StrTargetItemLoader(FighterItemLoader):
    default_item_class = StrTargetItem


class WinWayItemLoader(FighterItemLoader):
    default_item_class = WinWayItem
    default_output_processor = Compose(TakeFirst(), clean_text, clean_parenthesis)


class RecordsItemLoader(FighterItemLoader):
    default_item_class = PecordsItem
