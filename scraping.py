import requests
import pandas as pd
import time
from bs4 import BeautifulSoup

# Time Range Definition
years = list(range(2022, 2020, -1))
all_matches = []
leauge_table_url = "https://fbref.com/en/comps/12/La-Liga-Stats"


# Scraping
# Avoiding timeout by sleep
for year in years:
    data = requests.get(leauge_table_url)
    soup = BeautifulSoup(data.text, 'html.parser')
    time.sleep(5)

    league_table = soup.select("table.stats_table")[0]
    links = [link.get("href") for link in league_table.find_all('a')]
    links = [link for link in links if '/squads/' in link]
    team_urls = [f"https://fbref.com{l}" for l in links]
    previous_season = soup.select("a.prev")[0].get("href")
    leauge_table_url = f"https://fbref.com/{previous_season}"

    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats","").replace("-"," ")
        
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(5)

        links = [link.get("href") for link in soup.find_all("a")]
        links = [link for link in links if link and "all_comps/xg_details/" in link]

        data = requests.get(f"https://fbref.com{links[0]}")
        xg_details = pd.read_html(data.text, match="xg_details")[0]
        xg_details.columns = xg_details.columns.droplevel()

        try:
            team_data = matches.merge(xg_details[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except "No more information":
            continue

        team_data = team_data[team_data["Comp"] == "La Liga"]
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(5)


# Output
match_df = pd.concat(all_matches)
match_df.to_csv("matches.csv")
