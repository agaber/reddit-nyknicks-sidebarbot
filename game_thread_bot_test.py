from constants import UTC
from datetime import datetime
from game_thread_bot import Action, GameThreadBot 
from services import nba_data_test
from unittest.mock import MagicMock, patch

from services import nba_data
import unittest


class GameThreadBotTest(unittest.TestCase):

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
  def test_run_createGameThread(self, mock_get, mock_praw):
    # 1 hour before tip-off.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
    mock_subreddit = self.mock_subreddit(mock_praw)
    mock_subreddit.search.return_value = [FakeThread(author='macdoogles')]
    mock_submit_mod = MagicMock(['distinguish', 'sticky', 'suggested_sort'])
    mock_subreddit.submit.return_value = MagicMock(mod=mock_submit_mod)

    # Execute.
    GameThreadBot(now, 'subname').run()

    # Verify.
    mock_subreddit.search.assert_called_once_with(
        '[Game Thread]',  sort='new', time_filter='day')

    expected_title = ('[Game Thread] The New York Knicks (2-1) @ The Cleveland '
        'Cavaliers (3-2) - (December 29, 2020)');
    
    mock_subreddit.submit.assert_called_once_with(
      expected_title,
      selftext=EXPECTED_GAMETHREAD_TEXT,
      send_replies=False)
    mock_submit_mod.distinguish.assert_called_once_with(how='yes')
    mock_submit_mod.sticky.assert_called_once()
    mock_submit_mod.suggested_sort.assert_called_once_with('new')

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_run_updateGameThread(self, mock_get, mock_praw):
    # 1 hour before tip-off.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
    mock_subreddit = self.mock_subreddit(mock_praw)

    shitpost = FakeThread(author='macdoogles', selftext='better shut up')
    gamethread = FakeThread(author='nyknicks-automod', selftext="we did it!")
    mock_subreddit.search.return_value = [shitpost, gamethread]

    # Execute.
    GameThreadBot(now, 'subname').run()

    # Verify.
    mock_subreddit.search.assert_called_once_with(
        '[Game Thread]',  sort='new', time_filter='day')
    mock_subreddit.submit.assert_not_called()
    self.assertEqual(gamethread.selftext, EXPECTED_GAMETHREAD_TEXT)
    self.assertEqual(shitpost.selftext, 'better shut up')

  def mock_subreddit(self, mock_praw):
    mock_subreddit = MagicMock(['search', 'submit'])
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    return mock_subreddit

  # $ python3 game_thread_bot_test.py GameThreadBotTest.test_run_gamethread_prodReddit
  # CAUTION: THIS WILL USE REAL REDDIT WITH FAKE NBA DATA!!!
  # @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  # def test_run_gamethread_prodReddit(self, mock_get):
  #   now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
  #   GameThreadBot(now, 'knicklejerk').run()


class FakeThread:
  def __init__(self, author, selftext=''):
    self.author = author
    self.selftext = selftext

  def edit(self, selftext):
    self.selftext = selftext


EXPECTED_GAMETHREAD_TEXT = """
##General Information
**TIME**|**BROADCAST**|**Location and Subreddit**|
:------------|:------------------------------------|:-------------------|
07:00 PM Eastern   | National Broadcast: N/A           | Cleveland, OH USA|
06:00 PM Central   | Knicks Broadcast: MSG               | Rocket Mortgage FieldHouse|
05:00 PM Mountain | Cavaliers Broadcast: Fox Sports Ohio | r/NYKnicks|
04:00 PM Pacific   |                                                      | r/clevelandcavs|
-----
[Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
"""


if __name__ == '__main__':
  unittest.main()