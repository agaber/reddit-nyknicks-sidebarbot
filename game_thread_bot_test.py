from constants import UTC
from datetime import datetime
from game_thread_bot import Action, GameThreadBot 
from services import nba_data_test
from unittest.mock import MagicMock, patch

from services import nba_data
import unittest

class GameThreadBotTest(unittest.TestCase):
  mock_reddit = MagicMock(['subreddit'])

  def setUp(self):
    self.mock_reddit.reset_mock()

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_oneHourBeforeTipoff(self, mock_get, mock_praw):  
    now = datetime(2020, 12, 30, 11, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')

    bot = GameThreadBot(now, 'subredditName')
    current_game = bot._get_current_game(schedule)
    
    self.assertEqual(current_game['gameUrlCode'], '20201229/NYKCLE')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_gameStarted(self, mock_get, mock_praw):  
    now = datetime(2020, 12, 30, 1, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')

    bot = GameThreadBot(now, 'subredditName')
    current_game = bot._get_current_game(schedule)
    
    self.assertEqual(current_game['gameUrlCode'], '20201229/NYKCLE')

  # TODO: Mock post game (get post game data and figure out how to override test data)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_action_tooEarly_doNothing(self, mock_get, mock_praw):
    now = datetime(2020, 12, 30, 1, 0, 0, 0, UTC)
    game = {
      'startTimeUTC': '2020-12-30T04:30:00.000Z',
      'statusNum': 1,
      'vTeam': {'score': ''},
      'hTeam': {'score': ''},
    }
    action = GameThreadBot(now, 'subredditName')._get_action(game)
    self.assertEqual(action, Action.DO_NOTHING)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_action_beforeGame_gameThread(self, mock_get, mock_praw):
    now = datetime(2020, 12, 30, 3, 30, 0, 0, UTC)
    game = {
      'startTimeUTC': '2020-12-30T04:30:00.000Z',
      'statusNum': 1,
      'vTeam': {'score': ''},
      'hTeam': {'score': ''},
    }
    action = GameThreadBot(now, 'subredditName')._get_action(game)
    self.assertEqual(action, Action.DO_GAME_THREAD)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_action_duringGame_gameThread(self, mock_get, mock_praw):
    now = datetime(2020, 12, 30, 6, 0, 0, 0, UTC)
    game = {
      'startTimeUTC': '2020-12-30T04:30:00.000Z',
      'statusNum': 1,
      'vTeam': {'score': ''},
      'hTeam': {'score': ''},
    }
    action = GameThreadBot(now, 'subredditName')._get_action(game)
    self.assertEqual(action, Action.DO_GAME_THREAD)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_action_afterGame_postGameThread(self, mock_get, mock_praw):
    now = datetime(2020, 12, 30, 8, 0, 0, 0, UTC)
    game = {
      'startTimeUTC': '2020-12-30T04:30:00.000Z',
      'statusNum': 3,
      'vTeam': {'score': '100'},
      'hTeam': {'score': '101'},
    }
    action = GameThreadBot(now, 'subredditName')._get_action(game)
    self.assertEqual(action, Action.DO_POST_GAME_THREAD)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_action_tooLate_doNothing(self, mock_get, mock_praw):
    now = datetime(2020, 12, 31, 0, 0, 0, 0, UTC)
    game = {
      'startTimeUTC': '2020-12-30T04:30:00.000Z',
      'statusNum': 3,
      'vTeam': {'score': '100'},
      'hTeam': {'score': '101'},
    }
    action = GameThreadBot(now, 'subredditName')._get_action(game)
    self.assertEqual(action, Action.DO_NOTHING)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_build_game_thread_text(self, mock_get, mock_praw):
    self.maxDiff = None
    now = datetime(2020, 12, 31, 0, 0, 0, 0, UTC)
    boxscore = nba_data.boxscore('20201231', '0022000066')
    teams = nba_data.teams('2020')

    bot = GameThreadBot(now, 'sub')
    (title, body) = bot._build_game_thread_text(boxscore, teams)

    self.assertEqual(title, '[Game Thread] The New York Knicks (2-3) @ The Toronto Raptors (0-2) - (December 30, 2020)')
    self.assertEqual(body, """
##General Information
**TIME**|**BROADCAST**|**Location and Subreddit**|
:------------|:------------------------------------|:-------------------|
07:30 PM Eastern   |Knicks Broadcast: MSG            |Tampa, FL USA|
06:30 PM Central   |Raptors Broadcast: Sportsnet|Amalie Arena|
05:30 PM Mountain |National Broadcast: -        |r/NYKnicks|
04:30 PM Pacific   |                                                 |r/torontoraptors|
-----
[Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
""")

  def mock_praw(*args, **kwargs):
    mock_praw.return_value = mock_reddit


if __name__ == '__main__':
  unittest.main()