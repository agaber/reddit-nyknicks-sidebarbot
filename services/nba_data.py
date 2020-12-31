import json
import logging
import logging.config
import requests

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('sidebarbot')


def conference_standings():
  logger.info('Fetching conference standings.')
  r = requests.get(
      'http://data.nba.net/10s/prod/v1/current/standings_conference.json')
  r.raise_for_status()
  data = json.loads(r.content.decode('utf-8'))
  return data['league']['standard']


def current_year():
  logger.info('Fetching current season schedule year.')
  r = requests.get('http://data.nba.net/10s/prod/v1/today.json')
  r.raise_for_status()
  data = json.loads(r.content.decode('utf-8'))
  return data['seasonScheduleYear']


def players(year):
  logger.info(f'Fetching all player metadata for {year}.')
  r = requests.get(f'http://data.nba.net/prod/v1/{year}/players.json')
  r.raise_for_status()
  data = json.loads(r.content.decode('utf-8'))
  return data['league']['standard']


def roster(team, year):
  logger.info(f'Fetching {team} roster.')
  r = requests.get(f'http://data.nba.net/prod/v1/{year}/teams/{team}/roster.json')
  r.raise_for_status()
  data = json.loads(r.content.decode('utf-8'))
  return set(
      map(lambda p: p['personId'], data['league']['standard']['players']))


def schedule(team, year):
  logger.info(f'Fetching {team} schedule information.')
  base_url = f'http://data.nba.net/data/10s/prod/v1/{year}/teams/{team}'
  r = requests.get(f'{base_url}/schedule.json')
  r.raise_for_status()
  return json.loads(r.content.decode('utf-8'))


def teams(year):
  logger.info(f'Fetching {year} team-level metadata for all teams.')
  r = requests.get(f'http://data.nba.net/10s/prod/v1/{year}/teams.json')
  r.raise_for_status()
  teams = json.loads(r.content.decode('utf-8'))
  teams_map = dict()
  for team in teams['league']['standard']:
    teams_map[team['teamId']] = team
  return teams_map
