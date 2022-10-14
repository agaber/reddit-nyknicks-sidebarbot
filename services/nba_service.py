"""
Provides a facade class around the NBA Data APIs. It makes network calls to look
up NBA data and returns their responses. It encapsulates details around forming
the correct request URLs and marshalling JSON responses into python objects.
"""

import json
import logging.config
import requests


class NbaService:

  def __init__(self, logger=None):
    if logger is None:
      logging.config.fileConfig('logging.conf')
      self.logger = logging.getLogger(__name__)
    else:
      self.logger = logger

  def boxscore(self, start_date_est, game_id):
    """
    Fetches the box score from the NBA Data API.

    Parameters
    ----------
    start_date_est: str
      The "startDateEastern" field provided by the schedule API, which is also just
      the time of tip off in EST timezone in the format of yyyyMMdd.
    game_id: str
      Another string provided by the schedule API for the game in question.
    """
    self.logger.info(f'Fetching boxscore for {start_date_est} and {game_id}.')
    r = requests.get(
        f'http://data.nba.net/prod/v1/{start_date_est}/{game_id}_boxscore.json')
    r.raise_for_status()
    return json.loads(r.content.decode('utf-8'))

  def conference_standings(self):
    self.logger.info('Fetching conference standings.')
    r = requests.get(
        'http://data.nba.net/10s/prod/v1/current/standings_conference.json')
    r.raise_for_status()
    data = json.loads(r.content.decode('utf-8'))
    return data['league']['standard']

  def current_year(self):
    self.logger.info('Fetching current season schedule year.')
    r = requests.get('http://data.nba.net/10s/prod/v1/today.json')
    r.raise_for_status()
    data = json.loads(r.content.decode('utf-8'))
    return data['seasonScheduleYear']

  def players(self, year):
    self.logger.info(f'Fetching all player metadata for {year}.')
    r = requests.get(f'http://data.nba.net/prod/v1/{year}/players.json')
    r.raise_for_status()
    data = json.loads(r.content.decode('utf-8'))
    return data['league']['standard']

  def roster(self, team, year):
    self.logger.info(f'Fetching {team} roster.')
    r = requests.get(f'http://data.nba.net/prod/v1/{year}/teams/{team}/roster.json')
    r.raise_for_status()
    data = json.loads(r.content.decode('utf-8'))
    return set(
        map(lambda p: p['personId'], data['league']['standard']['players']))

  def schedule(self, team, year):
    base_url = f'http://data.nba.net/data/10s/prod/v1/{year}/teams/{team}'
    url = f'{base_url}/schedule.json'
    self.logger.info(f'Fetching {team} schedule information from {url}.')
    r = requests.get(url)
    r.raise_for_status()
    return json.loads(r.content.decode('utf-8'))

  def teams(self, year):
    self.logger.info(f'Fetching {year} team-level metadata for all teams.')
    r = requests.get(f'http://data.nba.net/10s/prod/v1/{year}/teams.json')
    r.raise_for_status()
    teams = json.loads(r.content.decode('utf-8'))
    teams_map = dict()
    for team in teams['league']['standard']:
      teams_map[team['teamId']] = team
    return teams_map
