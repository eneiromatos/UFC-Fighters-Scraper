# UFC Fighter Web Scraper

This web scraper extracts data on all UFC fighters from the official UFC website ([https://www.ufc.com/](https://www.ufc.com/)). The data can be exported in either JSON or CSV format and includes the following fields:

-   `profile_url`: the URL of the fighter's profile on the UFC website
-   `name`: the fighter's name
-   `nick_name`: the fighter's nickname (omitted if they have none)
-   `division`: weight class, e.g. `Middleweight`
-   `status`: `Active` or `Not Fighting`
-   `place_of_birth`, `trains_at`, `fighting_style`
-   `age`: the fighter's age
-   `height`: the fighter's height in inches
-   `weight`: the fighter's weight in pounds
-   `octagon_debut`: the date of the fighter's debut in the UFC octagon
-   `reach`: the fighter's reach in inches
-   `leg_reach`: the fighter's leg reach in inches
-   `records`: `wins`, `losses`, `draws` (as shown on the profile) plus any of `fight_win_streak`, `wins_by_knockout`, `wins_by_submission`, `wins_by_decision`, `first_round_finishes`, `title_defenses` that UFC displays for that fighter
-   `fighter_stats`:
    -   `sig_strikes_defense`, `takedown_defense`: percentages
    -   `knockdown_avg`: average knockdowns per fight
    -   `avg_fight_time`: mm:ss
    -   `win_by_method`: `ko_tko`, `dec`, `sub`
    -   `striking_stats`:
        -   `accuracy` (%), `sig_strikes_landed`, `sig_strikes_attempted`
        -   `sig_strikes_landed_per_min`, `sig_strikes_absorbed_per_min`
        -   `sig_str_by_position`: `standing`, `clinch`, `ground`
        -   `sig_str_by_target`: `head`, `body`, `leg`
    -   `grappling_stats`:
        -   `accuracy` (%), `takedowns_landed`, `takedowns_attempted`
        -   `takedowns_avg_per_15_min`, `submission_avg_per_15_min`

Fields UFC doesn't show for a given fighter are left out of that fighter's record.

### Example

```json
{"profile_url": "https://www.ufc.com/athlete/jon-jones", "name": "Jon Jones", "nick_name": "Bones", "division": "Heavyweight", "status": "Active", "place_of_birth": "Rochester, NY, United States", "trains_at": "Team Jones", "age": "38", "height": "76.00", "weight": "240 lbs", "octagon_debut": "Aug. 9, 2008", "reach": "84.50", "leg_reach": "45.00",
 "records": {"wins": "28", "losses": "1", "draws": "0", "wins_by_knockout": "11", "wins_by_submission": "7"},
 "fighter_stats": {"sig_strikes_defense": "64", "takedown_defense": "95", "knockdown_avg": "0.25", "avg_fight_time": "14:52",
  "striking_stats": {"accuracy": "59", "sig_strikes_landed": "1564", "sig_strikes_attempted": "2655", "sig_strikes_landed_per_min": "4.38", "sig_strikes_absorbed_per_min": "2.24", "sig_str_by_position": {"standing": "1012", "clinch": "250", "ground": "302"}, "sig_str_by_target": {"head": "759", "body": "375", "leg": "430"}},
  "grappling_stats": {"accuracy": "37", "takedowns_landed": "36", "takedowns_attempted": "98", "takedowns_avg_per_15_min": "1.89", "submission_avg_per_15_min": "0.46"},
  "win_by_method": {"ko_tko": "11", "dec": "10", "sub": "7"}}}
```

## Usage

1.  Clone the repository

`git clone https://github.com/eneiromatos/UFC-Fighters-Scraper.git` 

2.  Install the required packages

`pip install -r requirements.txt` 

3.  Run the script

`scrapy crawl fighters_stats -O ufc_fighters_stats.json`

    Only active fighters:

    `scrapy crawl fighters_stats -a active_only=true -O active_fighters.json`

    Quick test run (stop after ~20 fighters):

    `scrapy crawl fighters_stats -s CLOSESPIDER_ITEMCOUNT=20 -O sample.json`

4.  This scraper requires a USA IP address to run correctly.

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

## Note

The scraper will take a while to run and extract all the data, as it has to go through all the fighter's profile and collect the data.

It is also important to note that if the UFC website changes the structure of the website, it might affect the scraper's ability to extract the data. In this case, the script would have to be updated accordingly.