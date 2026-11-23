# UFC Fighter Web Scraper

This web scraper extracts data on all UFC fighters from the official UFC website ([https://www.ufc.com/](https://www.ufc.com/)). The data can be exported as JSON or CSV and includes the following fields:

-   `profile_url`: the URL of the fighter's profile on the UFC website
-   `name`: the fighter's name
-   `nick_name`: the fighter's nickname (omitted if they have none)
-   `division`: weight class, e.g. `Middleweight`
-   `status`: `Active`, `Not Fighting` or `Retired`
-   `place_of_birth`, `trains_at`, `fighting_style`
-   `age`: years
-   `height`: inches
-   `weight`: pounds
-   `octagon_debut`: date of the fighter's UFC debut, as `YYYY-MM-DD`
-   `reach`: inches
-   `leg_reach`: inches
-   `records`: `wins`, `losses`, `draws` (as shown on the profile) plus any of `fight_win_streak`, `wins_by_knockout`, `wins_by_submission`, `wins_by_decision`, `first_round_finishes`, `title_defenses` that UFC displays for that fighter
-   `fighter_stats`:
    -   `sig_strikes_defense`, `takedown_defense`: percentages
    -   `knockdown_avg`: average knockdowns per fight
    -   `avg_fight_time_seconds`: average fight length in seconds
    -   `win_by_method`: `ko_tko`, `dec`, `sub`
    -   `striking_stats`:
        -   `accuracy` (%), `sig_strikes_landed`, `sig_strikes_attempted`
        -   `sig_strikes_landed_per_min`, `sig_strikes_absorbed_per_min`
        -   `sig_str_by_position`: `standing`, `clinch`, `ground`
        -   `sig_str_by_target`: `head`, `body`, `leg`
    -   `grappling_stats`:
        -   `accuracy` (%), `takedowns_landed`, `takedowns_attempted`
        -   `takedowns_avg_per_15_min`, `submission_avg_per_15_min`

Numbers are stored as numbers (`76.0`, `240`, `59`), not text. Fields UFC doesn't show for a given fighter are left out, and so is a height or reach UFC lists as `0.00` (unknown).

### Example (JSON)

```json
{"profile_url": "https://www.ufc.com/athlete/jon-jones", "name": "Jon Jones", "nick_name": "Bones", "status": "Active", "division": "Heavyweight", "place_of_birth": "Rochester, NY, United States", "trains_at": "Team Jones", "age": 38, "height": 76.0, "weight": 240, "octagon_debut": "2008-08-09", "reach": 84.5, "leg_reach": 45.0,
 "records": {"wins": 28, "losses": 1, "draws": 0, "wins_by_knockout": 11, "wins_by_submission": 7},
 "fighter_stats": {"sig_strikes_defense": 64, "takedown_defense": 95, "knockdown_avg": 0.25, "avg_fight_time_seconds": 892,
  "striking_stats": {"accuracy": 59, "sig_strikes_landed": 1564, "sig_strikes_attempted": 2655, "sig_strikes_landed_per_min": 4.38, "sig_strikes_absorbed_per_min": 2.24, "sig_str_by_position": {"standing": 1012, "clinch": 250, "ground": 302}, "sig_str_by_target": {"head": 759, "body": 375, "leg": 430}},
  "grappling_stats": {"accuracy": 37, "takedowns_landed": 36, "takedowns_attempted": 98, "takedowns_avg_per_15_min": 1.89, "submission_avg_per_15_min": 0.46},
  "win_by_method": {"ko_tko": 11, "dec": 10, "sub": 7}}}
```

### CSV columns

A CSV export has one column per stat, so it opens cleanly in Excel or pandas. Nested names are joined with `_`, and the `records` / `fighter_stats` levels are dropped:

| JSON | CSV column |
|---|---|
| `records.wins` | `wins` |
| `fighter_stats.sig_strikes_defense` | `sig_strikes_defense` |
| `fighter_stats.striking_stats.accuracy` | `striking_accuracy` |
| `fighter_stats.striking_stats.sig_str_by_target.head` | `striking_sig_str_by_target_head` |
| `fighter_stats.grappling_stats.takedowns_landed` | `grappling_takedowns_landed` |
| `fighter_stats.win_by_method.ko_tko` | `win_by_method_ko_tko` |

Every CSV has the same 46 columns in the same order; a fighter missing a field has an empty cell.

## Usage

1.  Clone the repository and install the required packages:

    ```
    git clone https://github.com/broganlema/UFC-Fighters-Scraper.git
    cd UFC-Fighters-Scraper
    pip install -r requirements.txt
    ```

2.  Run the scraper (a full run takes about a minute):

    ```
    scrapy crawl fighters_stats -O ufc_fighters_stats.json
    ```

    The file extension picks the format, and you can write several at once:

    ```
    scrapy crawl fighters_stats -O fighters.json -O fighters.csv
    ```

    Only active fighters:

    ```
    scrapy crawl fighters_stats -a active_only=true -O active_fighters.csv
    ```

    Quick test run (stops after ~20 fighters):

    ```
    scrapy crawl fighters_stats -s CLOSESPIDER_ITEMCOUNT=20 -O sample.json
    ```

3.  This scraper may require a USA IP address to run correctly.

### Coverage report

At the end of every run the log shows how many fighters had each field:

```
Field coverage (fighters with each field):
  name                                     3240/3240  100%
  division                                 3121/3240   96%
  ...
```

If a field almost every fighter has (`name`, `status`, `division`, `weight`, `wins`, strikes by target) drops below 50%, a warning says UFC.com has probably changed its page layout. See [Tests](#tests) for how to find what broke.

### Caching pages while developing

When you're changing the parsing code and re-running the scraper over and over, save the downloaded pages so later runs don't contact UFC.com:

```
scrapy crawl fighters_stats -s HTTPCACHE_ENABLED=true -s CLOSESPIDER_ITEMCOUNT=50 -O sample.json
```

Pages are stored in `.scrapy/httpcache/`. Delete that folder (or leave off `HTTPCACHE_ENABLED`) to get fresh data.

## Tests

The tests run offline against saved copies of UFC.com pages in `tests/fixtures/` (trimmed down to just the parts the scraper reads):

```
pip install -r requirements-dev.txt
pytest
```

If UFC redesigns its site, re-download the fixture pages and re-run the tests; the failing tests point at the fields whose selectors need updating:

```
python tests/update_fixtures.py
pytest
```

Fighters' stats change over time, so a few expected values in the tests may need updating after a re-download too.

## Notes on UFC's data

-   UFC leaves "Takedowns Landed" / "Sig. Strikes Landed" blank instead of showing 0 when accuracy is 0%. The scraper records these as `0`.
-   A handful of profiles have obviously wrong values on UFC.com itself (for example a height of `155.0` that is really a weight). The scraper doesn't try to correct these.
-   If the UFC website changes its structure, the scraper will need updating; the coverage report and tests are there to make that quick to spot.
