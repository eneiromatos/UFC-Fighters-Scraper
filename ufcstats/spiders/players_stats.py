import scrapy
from .. import items


class PlayersStatsSpider(scrapy.Spider):
    name = "players_stats"
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
        # yield from response.follow_all(next_url, self.parse_athletes_listing)

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
        item.add_css(
            "hometown",
            '.c-bio__row--1col div[class*="border-bottom"] .c-bio__text::text',
        )
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
        yield item.load_item()

    def parse_striking_stats(self, response):
        item = items.StrikingStatsItemLoader(selector=response)
        stats = response.css('div[class*="c-stat-compare__group"]')
        stats_2 = response.css(".c-overlap__stats-value::text").getall()
        accuracy = response.css(".c-overlap__chart text::text").getall()

        if len(accuracy) > 0:
            item.add_value("accuracy", accuracy[0])
            item.add_value("sig_strikes_landed", stats_2[0])
            item.add_value("sig_strikes_attempted", stats_2[1])

        item.add_value(
            "sig_strikes_landed_per_min",
            stats[0].css('div[class*="number"]::text').get(),
        )
        item.add_value(
            "sig_strikes_absorbed_per_min",
            stats[1].css('div[class*="number"]::text').get(),
        )

        yield item.load_item()

    def parse_grappling_stats(self, response):
        pass

    def parse_str_possition(self, response):
        pass

    def parse_str_target(self, response):
        pass

    def parse_win_way(self, response):
        pass
