import csv
import datetime
import logging
import time

from typing import Any

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from constants import CUSTOM_DATA_QUERY, INIT_DATA_QUERY, TIERS
from settings import TOKEN


logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='logs.log',
    filemode='w',
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class GQLRunner:
    """Extracts dota2 matches from stratz GraphQL API.
    """
    DATA_FILE = "dota2_matches_{}.csv"
    DATA_FIELDS = [
        "league",
        "league_id",
        "league_tier",
        "league_start_date_time",
        "league_end_date_time",
        "league_region",
        "series_id",
        "series_type",
        "match_id",
        "match_start_date_time",
        "match_duration_seconds",
        "first_blood_time_seconds",
        "radiant_team_id",
        "radiant_team_name",
        "dire_team_id",
        "dire_team_name",
        "winner_id",
        "radiant_kills",
        "dire_kills",
    ]
    for faction in ("radiant", "dire"):
        for num in range(1, 6):
            prefix = f"{faction}_player_{num}"
            for field in ("id", "name", "hero_id", "hero", "position", "lane",
                          "role", "kills", "deaths", "assists", "networth"):
                DATA_FIELDS.append(f"{prefix}_{field}")

    def __init__(self):
        url = f"https://api.stratz.com/graphql?key={TOKEN}"
        transport = RequestsHTTPTransport(
            url=url,
            verify=True,
            retries=3,
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def get_init_data(self) -> None:
        """Gets all available matches for every leagues.
        """
        logging.info("Starting initial parsing...")
        file_name = self.DATA_FILE.format("init")
        with open(file_name, "w", encoding='utf-8') as file:
            csv.writer(file).writerow(self.DATA_FIELDS)
        with open(file_name, "a", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            leagues_per_page, series_per_page = 10, 20
            skip_leagues, skip_series = 0, 0
            while True:
                params = {
                    "leaguesRequest": {
                        "tiers": TIERS,
                        "take": leagues_per_page,
                        "skip": skip_leagues,
                    },
                    "takeSeries": series_per_page,
                    "skipSeries": skip_series,
                }
                logging.debug("Leagues offset: %s | Series offset: %s.",
                              skip_leagues, skip_series)
                data = self.client.execute(gql(INIT_DATA_QUERY), variable_values=params)
                leagues = data.get("leagues")
                if not leagues:
                    logging.debug("No more leagues there.")
                    break
                has_more_series = []
                for league in leagues:
                    league_data = {
                        "league": league.get("displayName"),
                        "league_id": league.get("id"),
                        "league_tier": league.get("tier"),
                        "league_start_date_time": league.get("startDateTime"),
                        "league_end_date_time": league.get("endDateTime"),
                        "league_region": league.get("region"),
                    }
                    league_series = league.get("series", [])
                    has_more_series.append(len(league_series) == series_per_page)
                    for series in league_series:
                        series_data = {
                            "series_id": series.get("id"),
                            "series_type": series.get("type"),
                        }
                        for match in series.get("matches"):
                            match_data = league_data | series_data
                            match_data.update(self._process_match_data(match))
                            csv_writer.writerow(match_data.values())
                if any(has_more_series):
                    skip_series += series_per_page
                    continue
                skip_series = 0
                skip_leagues += leagues_per_page
            logging.info("Initial parsing was finished.")

    def get_date_starting_from_date(self, date: datetime.datetime) -> None:
        """Gets matches started after passed date.

        Parameters
        ----------
        date: datetime.datetime
            Starting date and time.
        """
        logging.info("Starting parsing matches starting from %s...",
                     date.strftime("%Y-%m-%d, %H:%M:%S"))
        file_name = self.DATA_FILE.format(date.strftime("%Y-%m-%d_%H-%M-%S"))
        with open(file_name, "w", encoding='utf-8') as file:
            csv.writer(file).writerow(self.DATA_FIELDS)
        with open(file_name, "a", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            leagues_per_page, matches_per_page = 10, 20
            skip_leagues, skip_matches = 0, 0
            while True:
                params = {
                    "leaguesRequest": {
                        "tiers": TIERS,
                        "take": leagues_per_page,
                        "skip": skip_leagues,
                    },
                    "matchesRequest": {
                        "startDateTime": int(time.mktime(date.timetuple())),
                        "take": matches_per_page,
                        "skip": skip_matches,
                    }
                }
                logging.debug("Leagues offset: %s | Matches offset: %s.",
                              skip_leagues, skip_matches)
                data = self.client.execute(gql(CUSTOM_DATA_QUERY), variable_values=params)
                leagues = data.get("leagues")
                if not leagues:
                    logging.debug("No more leagues there.")
                    break
                has_more_matches = []
                for league in leagues:
                    league_data = {
                        "league": league.get("displayName"),
                        "league_id": league.get("id"),
                        "league_tier": league.get("tier"),
                        "league_start_date_time": league.get("startDateTime"),
                        "league_end_date_time": league.get("endDateTime"),
                        "league_region": league.get("region"),
                    }
                    league_matches = league.get("matches", [])
                    has_more_matches.append(len(league_matches) == matches_per_page)
                    for match in league_matches:
                        series_data = {
                            "series_id": match.get("series").get("id"),
                            "series_type": match.get("series").get("type"),
                        }
                        match_data = league_data | series_data
                        match_data.update(self._process_match_data(match))
                        csv_writer.writerow(match_data.values())
                if any(has_more_matches):
                    skip_matches += matches_per_page
                    continue
                skip_matches = 0
                skip_leagues += leagues_per_page
            logging.info("Parsing was finished.")

    def _process_match_data(self, match: dict[str, Any]) -> dict[str, Any]:
        """Transforms match data from nested json to plain dictionary.

        Returns
        -------
        dict[str, Any]
            Match data as a plain dictionary.
        """
        radiant_team = match.get("radiantTeam") or {}
        radiant_team_id = radiant_team.get("id")
        dire_team = match.get("direTeam") or {}
        dire_team_id = dire_team.get("id")
        match_data = {
            "match_id": match.get("id"),
            "match_start_date_time": match.get("startDateTime"),
            "match_duration_seconds": match.get("durationSeconds"),
            "first_blood_time_seconds": match.get("firstBloodTime"),
            "radiant_team_id": radiant_team_id,
            "radiant_team_name": radiant_team.get("name"),
            "dire_team_id": dire_team_id,
            "dire_team_name": dire_team.get("name"),
            "winner_id": radiant_team_id if match.get("didRadiantWin") else dire_team_id,
            "radiant_kills": sum(match.get("radiantKills")) if match.get("radiantKills") else None,
            "dire_kills": sum(match.get("direKills")) if match.get("direKills") else None,
        }
        radiant_players = filter(lambda player: player.get("isRadiant"), match.get("players"))
        dire_players = filter(lambda player: not player.get("isRadiant"), match.get("players"))
        for faction, players in (("radiant", radiant_players), ("dire", dire_players)):
            for num, player in enumerate(players, start=1):
                prefix = f"{faction}_player_{num}"
                steam_account = player.get("steamAccount") or {}
                player_name = steam_account.get("proSteamAccount").get("name") \
                    if steam_account.get("proSteamAccount") \
                    else steam_account.get("name")
                match_data.update({
                    f"{prefix}_id": steam_account.get("id"),
                    f"{prefix}_name": player_name,
                    f"{prefix}_hero_id": player.get("hero", {}).get("id"),
                    f"{prefix}_hero": player.get("hero", {}).get("displayName"),
                    f"{prefix}_position": player.get("position"),
                    f"{prefix}_lane": player.get("lane"),
                    f"{prefix}_role": player.get("role"),
                    f"{prefix}_kills": player.get("kills"),
                    f"{prefix}_deaths": player.get("deaths"),
                    f"{prefix}_assists": player.get("assists"),
                    f"{prefix}_networth": player.get("networth"),
                })
        return match_data
