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
  def test_get_current_game_tooEarly_doNothing(self, mock_get, mock_praw):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 29, 12, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertIsNone(game)
    self.assertEqual(action, Action.DO_NOTHING)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_1HourBefore_doGameThread(self, mock_get, mock_praw):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertEqual(action, Action.DO_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201229/NYKCLE')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_gameStarted_doGameThread(self, mock_get, mock_praw):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 30, 1, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertEqual(action, Action.DO_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201229/NYKCLE')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_afterGame_postGameThread(self, mock_get, mock_praw):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertEqual(action, Action.DO_POST_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201227/MILNYK')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_tooLate_doNothing(self, mock_get, mock_praw):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 28, 7, 0, 0, 0, UTC)
    schedule = nba_data.schedule('knicks', '2020')
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertEqual(action, Action.DO_NOTHING)
    self.assertIsNone(game)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_get_current_game_seasonOver_doNothing(self, mock_get, mock_praw):
    now = datetime(2021, 2, 10, 12, 0, 0, 0, UTC)
    schedule = {
      "league": {
        "lastStandardGamePlayedIndex": 0,
        "standard": [
          {
            'gameUrlCode': '20201231/NYKTOR',
            'startTimeUTC': '2021-01-01T00:30:00.000Z',
            'statusNum': 3,
            'vTeam': {'score': '83'},
            'hTeam': {'score': '100'},
          },
        ],
      }
    }
    (action, game) = GameThreadBot(now, 'NYKnicks')._get_current_game(schedule)
    self.assertEqual(action, Action.DO_NOTHING)
    self.assertIsNone(game)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_build_game_thread_text(self, mock_get, mock_praw):
    self.maxDiff = None
    now = datetime(2020, 12, 31, 0, 0, 0, 0, UTC)
    boxscore = nba_data.boxscore('20201231', '0022000066')
    teams = nba_data.teams('2020')

    bot = GameThreadBot(now, 'sub')
    (title, body) = bot._build_game_thread_text(boxscore, teams)

    self.assertEqual(
      title, 
      '[Game Thread] The New York Knicks (2-3) @ The Toronto Raptors (0-2) '
      '- (December 30, 2020)')
    
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