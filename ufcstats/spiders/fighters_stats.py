import scrapy
from .. import items


class FightersStatsSpider(scrapy.Spider):
    name = "fighters_stats"
    allowed_domains = ["ufc.com"]

    def start_requests(self):
        urls = ["https://www.ufc.com/athletes/all"]
        for url in urls:
            yield scrapy.Request(url, self.parse_athletes_listing)

    def parse_athletes_listing(self, response):
        athletes = response.css('div[class*="flipcard__action"] a::attr("href")')
        athletes = [response.urljoin(url.get()) for url in athletes]

        next_url = response.css('li.pager__item a::attr("href")')
        next_url = [response.urljoin(url.get()) for url in next_url]

        yield from response.follow_all(athletes, self.parse_fighter_bio)
        yield from response.follow_all(next_url, self.parse_athletes_listing)

    def parse_fighter_bio(self, response):
        item = items.FighterBioItemLoader(selector=response)
        item.add_value("profile_url", response.url)
        item.add_css("name", "div.c-hero__header h1::text")
        item.add_css("nick_name", 'div.c-hero__header div[class*="nickname"]::text')
        item.add_css(
            "status", '.c-bio__row--1col div[class="c-bio__field"] .c-bio__text::text'
        )
        item.add_css(
            "division",
            '.l-main__hero .c-hero__header div[class*="headline-suffix"]::text',
        )

        bio_fields = response.css(".c-bio__info-details .c-bio__field")
        for field in bio_fields:
            if "Status" == field.css(".c-bio__label::text").get():
                item.add_value("status", field.css(".c-bio__text::text").get())
            elif "Hometown" == field.css(".c-bio__label::text").get():
                item.add_value("hometown", field.css(".c-bio__text::text").get())
            elif "Trains at" == field.css(".c-bio__label::text").get():
                item.add_value("trains_at", field.css(".c-bio__text::text").get())
            elif "Fighting style" == field.css(".c-bio__label::text").get():
                item.add_value("fighting_style", field.css(".c-bio__text::text").get())
            elif "Age" == field.css(".c-bio__label::text").get():
                item.add_value("age", field.css(".c-bio__text .field::text").get())
            elif "Height" == field.css(".c-bio__label::text").get():
                item.add_value("height", field.css(".c-bio__text::text").get())
            elif "Weight" == field.css(".c-bio__label::text").get():
                item.add_value("weight", field.css(".c-bio__text::text").get())
            elif "Octagon Debut" == field.css(".c-bio__label::text").get():
                item.add_value("octagon_debut", field.css(".c-bio__text::text").get())
            elif "Reach" == field.css(".c-bio__label::text").get():
                item.add_value("reach", field.css(".c-bio__text::text").get())
            elif "Leg reach" == field.css(".c-bio__label::text").get():
                item.add_value("leg_reach", field.css(".c-bio__text::text").get())

        item.add_value("records", self.parse_records(response))
        item.add_value("fighter_stats", self.parse_main_fighter_stats(response))
        yield item.load_item()

    def parse_main_fighter_stats(self, response):
        item = items.MainFighterStatsItemLoader(selector=response)

        stats = response.css('div[class*="c-stat-compare__group-"]')
        for stat in stats:
            if "Knockdown Ratio" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "knockdown_ratio", stat.css(".c-stat-compare__number::text").get()
                )
            elif "Average fight time" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "avg_fight_time", stat.css(".c-stat-compare__number::text").get()
                )
            elif "Sig. Str. Defense" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "sig_strikes_defense",
                    stat.css(".c-stat-compare__number::text").get(),
                )
            elif "Takedown Defense" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "takedown_defense", stat.css(".c-stat-compare__number::text").get()
                )

        item.add_value("strinking_stats", self.parse_striking_stats(response))
        item.add_value("grappling_stats", self.parse_grappling_stats(response))
        item.add_value("win_by_way", self.parse_win_way(response))
        yield item.load_item()

    def parse_striking_stats(self, response):
        item = items.StrikingStatsItemLoader(selector=response)

        accuracy_card = response.css(".c-overlap-athlete-detail__card")
        for card in accuracy_card:
            if "striking" in card.css("h2::text").get().casefold():
                item.add_value("accuracy", card.css("text::text").get())
                item.add_value(
                    "sig_strikes_landed",
                    card.css(".c-overlap__stats-value:nth-child(2)::text").get(),
                )
                item.add_value(
                    "sig_strikes_attempted",
                    card.css(".c-overlap__stats-value:nth-child(4)::text").get(),
                )

        stats = response.css('div[class*="c-stat-compare__group-"]')
        for stat in stats:
            if "Sig. Str. Landed" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "sig_strikes_landed_per_min",
                    stat.css(".c-stat-compare__number::text").get(),
                )
            elif "Sig. Str. Absorbed" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "sig_strikes_absorbed_per_min",
                    stat.css(".c-stat-compare__number::text").get(),
                )

        item.add_value("sig_str_by_position", self.parse_str_possition(response))
        item.add_value("sig_str_by_target", self.parse_str_target(response))
        yield item.load_item()

    def parse_grappling_stats(self, response):
        item = items.GrapplingStatsItemLoader(selector=response)

        accuracy_card = response.css(".c-overlap-athlete-detail__card")
        for card in accuracy_card:
            if "grappling" in card.css("h2::text").get().casefold():
                item.add_value("accuracy", card.css("text::text").get())
                item.add_value(
                    "takedowns_landed",
                    card.css(".c-overlap__stats-value:nth-child(2)::text").get(),
                )
                item.add_value(
                    "takedowns_attempted",
                    card.css(".c-overlap__stats-value:nth-child(4)::text").get(),
                )

        stats = response.css('div[class*="c-stat-compare__group-"]')
        for stat in stats:
            if "Takedown avg" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "takedowns_avg_per_15_min",
                    stat.css(".c-stat-compare__number::text").get(),
                )
            elif "Submission avg" == stat.css(".c-stat-compare__label::text").get():
                item.add_value(
                    "submission_avg_per_15_min",
                    stat.css(".c-stat-compare__number::text").get(),
                )
        yield item.load_item()

    def parse_str_possition(self, response):
        graph_stats = response.css(".c-stats-group-3col__item")
        for stats in graph_stats:
            if "Sig. Str. By Position" in stats.css("h2::text").get():
                item = items.StrPossitionItemLoader(selector=stats)
                item.add_css(
                    "standing",
                    ".c-stat-3bar__group:nth-child(1) .c-stat-3bar__value::text",
                )
                item.add_css(
                    "clinch",
                    ".c-stat-3bar__group:nth-child(2) .c-stat-3bar__value::text",
                )
                item.add_css(
                    "ground",
                    ".c-stat-3bar__group:nth-child(3) .c-stat-3bar__value::text",
                )
                yield item.load_item()

    def parse_str_target(self, response):
        item = items.StrTargetItemLoader(selector=response)
        item.add_css("head", '.c-stat-body text[id*="head_value"]::text')
        item.add_css("body", '.c-stat-body text[id*="body_value"]::text')
        item.add_css("leg", '.c-stat-body text[id*="leg_value"]::text')
        yield item.load_item()

    def parse_win_way(self, response):
        graph_stats = response.css(".c-stats-group-3col__item")
        for stats in graph_stats:
            if "Win By Way" in stats.css("h2::text").get():
                item = items.WinWayItemLoader(selector=stats)
                item.add_css(
                    "ko_tko",
                    ".c-stat-3bar__group:nth-child(1) .c-stat-3bar__value::text",
                )
                item.add_css(
                    "dec", ".c-stat-3bar__group:nth-child(2) .c-stat-3bar__value::text"
                )
                item.add_css(
                    "sub", ".c-stat-3bar__group:nth-child(3) .c-stat-3bar__value::text"
                )
                yield item.load_item()

    def parse_records(self, response):
        item = items.RecordsItemLoader(selector=response)

        records = response.css(".c-record")
        for record in records:
            if "Fight Win Streak" == record.css(".c-record__promoted-text::text").get():
                item.add_value(
                    "fight_win_streak",
                    record.css(".c-record__promoted-figure::text").get(),
                )
            if "Wins by Knockout" == record.css(".c-record__promoted-text::text").get():
                item.add_value(
                    "wins_by_knockout",
                    record.css(".c-record__promoted-figure::text").get(),
                )
            if (
                "Wins by Submission"
                == record.css(".c-record__promoted-text::text").get()
            ):
                item.add_value(
                    "wins_by_submission",
                    record.css(".c-record__promoted-figure::text").get(),
                )
            if "Wins by Decision" == record.css(".c-record__promoted-text::text").get():
                item.add_value(
                    "wins_by_decision",
                    record.css(".c-record__promoted-figure::text").get(),
                )
            if (
                "First Round Finishes"
                == record.css(".c-record__promoted-text::text").get()
            ):
                item.add_value(
                    "first_round_finishes",
                    record.css(".c-record__promoted-figure::text").get(),
                )
            if "Title Defenses" == record.css(".c-record__promoted-text::text").get():
                item.add_value(
                    "title_defenses",
                    record.css(".c-record__promoted-figure::text").get(),
                )

        yield item.load_item()
