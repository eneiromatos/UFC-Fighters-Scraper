# UFC Fighter Web Scraper

This web scraper extracts data on all UFC fighters from the official UFC website ([https://www.ufc.com/](https://www.ufc.com/)). The data can be exported in either JSON or CSV format and includes the following fields:

-   `profile_url`: the URL of the fighter's profile on the UFC website
-   `status`: whether the fighter is currently active or not
-   `fighting_style`: the fighter's primary fighting style
-   `age`: the fighter's age
-   `height`: the fighter's height in inches
-   `weight`: the fighter's weight in pounds
-   `octagon_debut`: the date of the fighter's debut in the UFC octagon
-   `reach`: the fighter's reach in inches
-   `leg_reach`: the fighter's leg reach in inches
-   `records`: an object containing the fighter's record information (e.g. wins, losses, draws)
-   `fighter_stats`: an object containing the fighter's statistics, including:
    -   `sig_strikes_defense`: the fighter's significant strikes defense percentage
    -   `takedown_defense`: the fighter's takedown defense percentage
    -   `avg_fight_time`: the average length of the fighter's fights in mm:ss format
    -   `striking_stats`: an object containing the fighter's striking statistics, including:
        -   `sig_strikes_landed_per_min`: the number of significant strikes landed by the fighter per minute
        -   `sig_strikes_absorbed_per_min`: the number of significant strikes absorbed by the fighter per minute
        -   `sig_str_by_target`: an object containing the number of significant strikes landed by the fighter on different body parts (head, body, leg)
    -   `grappling_stats`: an object containing the fighter's grappling statistics, including:
        -   `takedowns_avg_per_15_min`: the average number of takedowns attempted by the fighter per 15 minutes
        -   `submission_avg_per_15_min`: the average number of submissions attempted by the fighter per 15 minutes

## Usage

1.  Clone the repository

`git clone https://github.com/eneiromatos/UFC-Fighters-Scraper.git` 

2.  Install the required packages

`pip install -r requirements.txt` 

3.  Run the script

`scrapy crawl fighters_stats -O ufc_fighters_stats.json ` 

4.  This scraper requires a USA IP address to run correctly.

## Note

The scraper will take a while to run and extract all the data, as it has to go through all the fighter's profile and collect the data.

It is also important to note that if the UFC website changes the structure of the website, it might affect the scraper's ability to extract the data. In this case, the script would have to be updated accordingly.