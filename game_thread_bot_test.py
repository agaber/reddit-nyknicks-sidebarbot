from datetime import datetime
from services import nba_data_test
from unittest.mock import MagicMock, patch

from game_thread_bot import Action, GameThreadBot, UTC
import unittest


class GameThreadBotTest(unittest.TestCase):
  mock_reddit = MagicMock(['subreddit'])

  def setUp(self):
    self.mock_reddit.reset_mock()

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_oneHourBeforeTipoff(self, mock_get, mock_praw):  
    now = datetime(2020, 12, 30, 11, 0, 0, 0, UTC)
    bot = GameThreadBot(now, 'subredditName')
    current_game = bot._get_current_game()
    self.assertEqual(current_game['gameUrlCode'], '20201229/NYKCLE')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_gameStarted(self, mock_get, mock_praw):  
    now = datetime(2020, 12, 30, 1, 0, 0, 0, UTC)
    bot = GameThreadBot(now, 'subredditName')
    current_game = bot._get_current_game()
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

  def mock_praw(*args, **kwargs):
    mock_praw.return_value = mock_reddit


if __name__ == '__main__':
  unittest.main()