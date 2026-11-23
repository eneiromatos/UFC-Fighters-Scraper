import re

import scrapy

from .. import items

BIO_FIELDS = {
    "Status": "status",
    "Place of Birth": "place_of_birth",
    "Trains at": "trains_at",
    "Fighting style": "fighting_style",
    "Age": "age",
    "Height": "height",
    "Weight": "weight",
    "Octagon Debut": "octagon_debut",
    "Reach": "reach",
    "Leg reach": "leg_reach",
}

RECORD_FIELDS = {
    "Fight Win Streak": "fight_win_streak",
    "Wins by Knockout": "wins_by_knockout",
    "Wins by Submission": "wins_by_submission",
    "Wins by Decision": "wins_by_decision",
    "First Round Finishes": "first_round_finishes",
    "Title Defenses": "title_defenses",
}

# label in a .c-stat-compare__group -> (which loader, field name)
COMPARE_FIELDS = {
    "Sig. Str. Landed": ("striking", "sig_strikes_landed_per_min"),
    "Sig. Str. Absorbed": ("striking", "sig_strikes_absorbed_per_min"),
    "Takedown avg": ("grappling", "takedowns_avg_per_15_min"),
    "Submission avg": ("grappling", "submission_avg_per_15_min"),
    "Sig. Str. Defense": ("main", "sig_strikes_defense"),
    "Takedown Defense": ("main", "takedown_defense"),
    "Knockdown Avg": ("main", "knockdown_avg"),
    "Average fight time": ("main", "avg_fight_time"),
}

OVERLAP_FIELDS = {
    "Sig. Strikes Landed": "sig_strikes_landed",
    "Sig. Strikes Attempted": "sig_strikes_attempted",
    "Takedowns Landed": "takedowns_landed",
    "Takedowns Attempted": "takedowns_attempted",
}

POSITION_FIELDS = {"Standing": "standing", "Clinch": "clinch", "Ground": "ground"}
WIN_METHOD_FIELDS = {"KO/TKO": "ko_tko", "DEC": "dec", "SUB": "sub"}


def text_of(selector, css):
    """All text inside the matched node(s), whitespace-collapsed."""
    return " ".join(" ".join(selector.css(css + " ::text").getall()).split())


class FightersStatsSpider(scrapy.Spider):
    name = "fighters_stats"
    allowed_domains = ["ufc.com"]
    start_urls = ["https://www.ufc.com/athletes/all"]

    def __init__(self, active_only="false", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_only = str(active_only).lower() in ("1", "true", "yes")

    def parse(self, response):
        """Athletes listing page: follow every profile, then the next page."""
        athletes = response.css('div[class*="flipcard__action"] a::attr(href)').getall()
        yield from response.follow_all(athletes, self.parse_fighter_bio)
        yield from response.follow_all(
            response.css("li.pager__item a::attr(href)").getall(), self.parse
        )

    def parse_fighter_bio(self, response):
        item = items.FighterBioItemLoader(selector=response)
        item.add_value("profile_url", response.url)
        item.add_css("name", "h1.hero-profile__name::text")
        item.add_css("nick_name", ".hero-profile__nickname::text")
        item.add_css("division", ".hero-profile__division-title::text")

        for field in response.css(".c-bio__field"):
            key = BIO_FIELDS.get(text_of(field, ".c-bio__label"))
            if key:
                item.add_value(key, text_of(field, ".c-bio__text"))

        item.add_value("records", self.parse_records(response))
        item.add_value("fighter_stats", self.parse_fighter_stats(response))
        fighter = item.load_item()

        if self.active_only and fighter.get("status") != "Active":
            return
        if not fighter.get("name"):
            self.logger.warning("No fighter name found on %s", response.url)
        yield fighter

    def parse_records(self, response):
        item = items.RecordsItemLoader(selector=response)

        # "9-2-1 (W-L-D)"
        wld = text_of(response, ".hero-profile__division-body")
        match = re.match(r"(\d+)-(\d+)-(\d+)", wld)
        if match:
            item.add_value("wins", match.group(1))
            item.add_value("losses", match.group(2))
            item.add_value("draws", match.group(3))

        for stat in response.css(".athlete-stats__stat"):
            key = RECORD_FIELDS.get(text_of(stat, ".athlete-stats__stat-text"))
            if key:
                item.add_value(key, text_of(stat, ".athlete-stats__stat-numb"))

        return dict(item.load_item())

    def parse_fighter_stats(self, response):
        loaders = {
            "main": items.MainFighterStatsItemLoader(selector=response),
            "striking": items.StrikingStatsItemLoader(selector=response),
            "grappling": items.GrapplingStatsItemLoader(selector=response),
        }

        for group in response.css(".c-stat-compare__group"):
            target = COMPARE_FIELDS.get(text_of(group, ".c-stat-compare__label"))
            if target:
                loader, key = target
                # number node also contains a nested "%" div; take only its own text
                loaders[loader].add_value(
                    key, group.css(".c-stat-compare__number::text").get()
                )

        # Striking / Takedown accuracy donut charts
        for card in response.css(".overlap-athlete-content"):
            title = text_of(card, "h2").casefold()
            if "striking" in title:
                loader = loaders["striking"]
            elif "takedown" in title or "grappling" in title:
                loader = loaders["grappling"]
            else:
                continue
            loader.add_value("accuracy", text_of(card, ".e-chart-circle__percent"))
            for pair in card.css("dl.c-overlap__stats"):
                key = OVERLAP_FIELDS.get(text_of(pair, "dt"))
                if key:
                    loader.add_value(key, text_of(pair, "dd"))

        striking = loaders["striking"]
        striking.add_value(
            "sig_str_by_position",
            self.parse_3bar(
                response, "by position", items.StrPositionItemLoader, POSITION_FIELDS
            ),
        )
        striking.add_value("sig_str_by_target", self.parse_str_target(response))

        main = loaders["main"]
        main.add_value("striking_stats", dict(striking.load_item()))
        main.add_value("grappling_stats", dict(loaders["grappling"].load_item()))
        main.add_value(
            "win_by_method",
            self.parse_3bar(
                response, "win by", items.WinByMethodItemLoader, WIN_METHOD_FIELDS
            ),
        )
        return dict(main.load_item())

    def parse_3bar(self, response, title_contains, loader_cls, fields):
        """Parse a .c-stat-3bar chart (e.g. 'Sig. Str. By Position', 'Win by Method')."""
        for chart in response.css(".c-stat-3bar"):
            if title_contains not in text_of(chart, ".c-stat-3bar__title").casefold():
                continue
            item = loader_cls(selector=chart)
            for group in chart.css(".c-stat-3bar__group"):
                key = fields.get(text_of(group, ".c-stat-3bar__label"))
                if key:
                    item.add_value(key, text_of(group, ".c-stat-3bar__value"))
            return dict(item.load_item())
        return None

    def parse_str_target(self, response):
        item = items.StrTargetItemLoader(selector=response)
        for part in ("head", "body", "leg"):
            item.add_css(part, f'.c-stat-body text[id$="{part}_value"]::text')
        return dict(item.load_item())
