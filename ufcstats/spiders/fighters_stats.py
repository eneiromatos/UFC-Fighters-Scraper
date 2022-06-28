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
            if "Hometown" == field.css(".c-bio__label::text").get():
                item.add_value("hometown", field.css(".c-bio__text::text").get())
            if "Trains at" == field.css(".c-bio__label::text").get():
                item.add_value("trains_at", field.css(".c-bio__text::text").get())
            if "Fighting style" == field.css(".c-bio__label::text").get():
                item.add_value("fighting_style", field.css(".c-bio__text::text").get())
            if "Age" == field.css(".c-bio__label::text").get():
                item.add_value("age", field.css(".c-bio__text .field::text").get())
            if "Height" == field.css(".c-bio__label::text").get():
                item.add_value("height", field.css(".c-bio__text::text").get())
            if "Weight" == field.css(".c-bio__label::text").get():
                item.add_value("weight", field.css(".c-bio__text::text").get())
            if "Octagon Debut" == field.css(".c-bio__label::text").get():
                item.add_value("octagon_debut", field.css(".c-bio__text::text").get())
            if "Reach" == field.css(".c-bio__label::text").get():
                item.add_value("reach", field.css(".c-bio__text::text").get())
            if "Leg reach" == field.css(".c-bio__label::text").get():
                item.add_value("leg_reach", field.css(".c-bio__text::text").get())

        item.add_value("fighter_stats", self.parse_main_fighter_stats(response))
        yield item.load_item()

    def parse_main_fighter_stats(self, response):
        item = items.MainFighterStatsItemLoader(selector=response)
        stats = response.css('div[class*="c-stat-compare__group"]')
        item.add_value(
            "knockdown_ratio", stats[6].css('div[class*="number"]::text').get()
        )
        item.add_value(
            "avg_fight_time", stats[7].css('div[class*="number"]::text').get()
        )
        item.add_value(
            "sig_strikes_defense", stats[4].css('div[class*="number"]::text').get()
        )
        item.add_value(
            "takedown_defense", stats[5].css('div[class*="number"]::text').get()
        )
        item.add_value("strinking_stats", self.parse_striking_stats(response))
        item.add_value("grappling_stats", self.parse_grappling_stats(response))
        item.add_value("win_by_way", self.parse_win_way(response))
        yield item.load_item()

    def parse_striking_stats(self, response):
        item = items.StrikingStatsItemLoader(selector=response)
        stats = response.css('div[class*="c-stat-compare__group"]')
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
        item.add_value(
            "sig_strikes_landed_per_min",
            stats[0].css('div[class*="number"]::text').get(),
        )
        item.add_value(
            "sig_strikes_absorbed_per_min",
            stats[1].css('div[class*="number"]::text').get(),
        )
        item.add_value("sig_str_by_position", self.parse_str_possition(response))
        item.add_value("sig_str_by_target", self.parse_str_target(response))
        yield item.load_item()

    def parse_grappling_stats(self, response):
        item = items.GrapplingStatsItemLoader(selector=response)
        stats = response.css('div[class*="c-stat-compare__group"]')
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

        item.add_value(
            "takedowns_avg_per_15_min",
            stats[2].css('div[class*="number"]::text').get(),
        )
        item.add_value(
            "submission_avg_per_15_min",
            stats[3].css('div[class*="number"]::text').get(),
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
