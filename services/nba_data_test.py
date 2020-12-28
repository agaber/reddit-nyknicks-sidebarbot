from services import nba_data
from unittest.mock import patch

import os.path
import unittest


class MockResponse:

  def __init__(self, file_name, status_code):
    with open(file_name, 'r') as f:
      self.content = f.read().encode('utf-8')
    self.status_code = status_code

  def raise_for_status(self):
    pass


def mocked_requests_get(*args, **kwargs):
  requested_url = args[0]
  testdata_path = 'services/testdata/' + requested_url.split('/')[-1]
  if os.path.isfile(testdata_path):
    return MockResponse(testdata_path, 200)
  return MockResponse(None, 404)


class NbaDataTest(unittest.TestCase):

  @patch('requests.get', side_effect=mocked_requests_get)
  def test_current_year(self, mock_get):
    self.assertEqual(nba_data.current_year(), 2020)
    mock_get.assert_called_once_with(
        'http://data.nba.net/10s/prod/v1/today.json')

  @patch('requests.get', side_effect=mocked_requests_get)
  def test_players(self, mock_get):
    response = nba_data.players('2020')
    # Just verify a few properties instead of the entire large response.
    actual_names = list(
        map(lambda player: player['temporaryDisplayName'], response))
    expected_names = [
        'Achiuwa, Precious',
        'Adams, Jaylen',
        'Adams, Steven',
        'Adebayo, Bam',
        'Aldridge, LaMarcus',
    ]
    self.assertEqual(actual_names, expected_names)
    mock_get.assert_called_once_with(
        'http://data.nba.net/prod/v1/2020/players.json')

  @patch('requests.get', side_effect=mocked_requests_get)
  def test_roster(self, mock_get):
    response = nba_data.roster('knicks')
    expected = ['1629628', '1629649', '203493', '202692']
    self.assertEqual(response, expected)
    mock_get.assert_called_once_with(
        'http://data.nba.net/prod/v1/2020/teams/knicks/roster.json')

  @patch('requests.get', side_effect=mocked_requests_get)
  def test_schedule(self, mock_get):
    response = nba_data.schedule('knicks', '2020')
    # Just verify a few properties instead of the entire large response.
    actual = list(map(lambda s: s['gameId'], response['league']['standard']))
    expected = ['0012000002', '0012000015', '0012000028']
    self.assertEqual(actual, expected)
    mock_get.assert_called_once_with(
        'http://data.nba.net/data/10s/prod/v1/2020/teams/knicks/schedule.json')

  @patch('requests.get', side_effect=mocked_requests_get)
  def test_teams(self, mock_get):
    teams = nba_data.teams('2020')
    # Just spot check a few properties instead of the entire large response.
    self.assertEqual('Atlanta Hawks', teams['1610612737']['fullName'])
    self.assertEqual('Hawks', teams['1610612737']['nickname'])
    self.assertEqual('Boston Celtics', teams['1610612738']['fullName'])
    mock_get.assert_called_once_with(
        'http://data.nba.net/10s/prod/v1/2020/teams.json')


if __name__ == '__main__':
  unittest.main()
