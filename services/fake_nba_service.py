"""
An implementation of NbaService that returns fake data.
"""

from services.nba_service import NbaService

import json


class FakeNbaService(NbaService):

  def __init__(self, logger=None):
    pass

  def boxscore(self, start_date_est, game_id):
    return self._json(f'{game_id}_boxscore.json')

  def conference_standings(self):
    return self._json('standings_conference.json')['league']['standard']

  def current_year(self):
    return '2020'

  def players(self, year):
    return self._json('all_players.json')['league']['standard']

  def roster(self, team, year):
    data = self._json(f'{team}_roster.json')
    return set(
      map(lambda p: p['personId'], data['league']['standard']['players']))

  def schedule(self, team, year):
    return self._json('schedule.json')

  def teams(self, year):
    teams = self._json('teams.json')
    teams_map = dict()
    for team in teams['league']['standard']:
      teams_map[team['teamId']] = team
    return teams_map

  @staticmethod
  def _json(file_name):
    with open(f'services/testdata/{file_name}', 'r') as f:
      return json.loads(f.read().encode('utf-8'))
