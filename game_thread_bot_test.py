from constants import GAME_THREAD_PREFIX, POST_GAME_PREFIX, UTC
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
        GAME_THREAD_PREFIX,  sort='new', time_filter='day')

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
        GAME_THREAD_PREFIX,  sort='new', time_filter='day')
    mock_subreddit.submit.assert_not_called()
    self.assertEqual(gamethread.selftext, EXPECTED_GAMETHREAD_TEXT)
    self.assertEqual(shitpost.selftext, 'better shut up')

  @patch('praw.Reddit')
  @patch('random.choice')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_run_createPostGameThread(
        self, mock_get, mock_random, mock_praw):
    # 3.5 hours before tip-off.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    mock_random.return_value = 'defeat'

    mock_subreddit = self.mock_subreddit(mock_praw)
    mock_subreddit.search.return_value = [FakeThread(author='macdoogles')]
    mock_submit_mod = MagicMock(['distinguish', 'sticky', 'suggested_sort'])
    mock_subreddit.submit.return_value = MagicMock(mod=mock_submit_mod)

    # Execute.
    GameThreadBot(now, 'subname').run()

    # Verify.
    mock_subreddit.search.assert_called_once_with(
        POST_GAME_PREFIX,  sort='new', time_filter='day')

    expected_title = ('[Post Game Thread] The New York Knicks (1-2) defeat the '
                      'Milwaukee Bucks (1-2), 130-110');

    expected_selftext = ''

    mock_subreddit.submit.assert_called_once_with(
        expected_title,
        selftext=EXPECTED_POSTGAME_TEXT,
        send_replies=False)
    mock_submit_mod.distinguish.assert_called_once_with(how='yes')
    mock_submit_mod.sticky.assert_called_once()
    mock_submit_mod.suggested_sort.assert_called_once_with('new')

  # TODO: many more tests needed for the title generation
  # - with 1 OT
  # - with many OTs
  # - road team wins
  # - will most likely need to call _build_postgame_thread_text directly for that
  #   in order to mock out the nba data API calls

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

EXPECTED_POSTGAME_TEXT = """
||    
|:-:|   
|[](/r/MkeBucks) **110 -  130** [](/r/NYKnicks)|
|**Box Scores: [NBA](https://www.nba.com/game/MIL-vs-NYK-0022000036) & [Yahoo](http://sports.yahoo.com/nba/milwaukee-bucks-new-york-knicks-2020122718)**|

||
|:-:|
|**GAME SUMMARY**|
|**Location:** Madison Square Garden(0), **Clock:** |
|**Officials:** Scott Wall, Zach Zarba and Evan Scott|


|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|
|:---|:--|:--|:--|:--|:--|
|Milwaukee Bucks|27|18|30|35|110|
|New York Knicks|30|31|35|34|130|

**TEAM STATS**

|**Team**|**PTS**|**FG**|**FG%**|**3P**|**3P%**|**FT**|**FT%**|**OREB**|**TREB**|**AST**|**PF**|**STL**|**TO**|**BLK**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
|Milwaukee Bucks|110|41-95|43.2%|7-38|18.4%|21-29|72.4%|17|44|24|21|7|11|5|
|New York Knicks|130|46-85|54.1%|16-27|59.3%|22-27|81.5%|8|46|27|23|5|15|4|

|**Team**|**Biggest Lead**|**Longest Run**|**PTS: In Paint**|**PTS: Off TOs**|**PTS: Fastbreak**|
|:--|:--|:--|:--|:--|:--|
|Milwaukee Bucks|+2|8|60|20|12|
|New York Knicks|+28|11|48|15|5|
    
**TEAM LEADERS**

|**Team**|**Points**|**Rebounds**|**Assists**|
|:--|:--|:--|:--|
|Milwaukee Bucks|**27** Giannis Antetokounmpo|**13** Giannis Antetokounmpo|**5** Giannis Antetokounmpo|
|New York Knicks|**29** Julius Randle|**14** Julius Randle|**7** Julius Randle|

**PLAYER STATS**

**[](/MIL) BUCKS**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
|Giannis Antetokounmpo^SF|31:59|9-15|1-5|8-13|2|11|13|5|3|0|3|3|-13|27|
|Khris Middleton^PF|32:46|8-18|1-6|5-5|1|3|4|5|0|0|0|1|-23|22|
|Brook Lopez^C|20:50|2-7|0-4|2-2|2|0|2|0|1|2|0|3|-25|6|
|Donte DiVincenzo^SG|23:30|4-7|2-4|0-1|0|2|2|1|0|0|1|0|-11|10|
|Jrue Holiday^PG|27:55|4-10|0-4|0-0|2|2|4|5|2|0|3|0|-9|8|
|Bobby Portis|26:07|7-12|1-2|2-2|5|2|7|2|1|1|1|5|+6|17|
|Pat Connaughton|15:57|2-8|0-5|0-0|1|2|3|1|0|1|0|2|-6|4|
|D.J. Wilson|6:54|0-0|0-0|1-2|1|0|1|0|0|0|0|2|-6|1|
|Bryn Forbes|17:38|0-4|0-1|1-2|0|0|0|0|0|0|0|2|-9|1|
|D.J. Augustin|13:44|0-6|0-4|2-2|0|1|1|1|0|0|1|0|-19|2|
|Torrey Craig|2:44|0-0|0-0|0-0|0|0|0|2|0|1|0|0|+3|0|
|Jordan Nwora|7:27|4-6|1-2|0-0|0|2|2|0|0|0|2|0|+6|9|
|Sam Merrill|7:27|1-2|1-1|0-0|1|2|3|2|0|0|0|1|+6|3|
|Thanasis Antetokounmpo|4:59|0-0|0-0|0-0|2|0|2|0|0|0|0|2|0|0|
|Jaylen Adams|0:00|0-0|0-0|0-0|0|0|0|0|0|0|0|0|0|0|
|Mamadi Diakite|0:00|0-0|0-0|0-0|0|0|0|0|0|0|0|0|0|0|

**[](/NYK) KNICKS**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
|Reggie Bullock^SF|16:53|2-5|1-2|2-2|0|3|3|1|0|0|1|2|+1|7|
|Julius Randle^PF|37:07|8-17|3-5|10-11|3|11|14|7|0|1|2|4|+12|29|
|Mitchell Robinson^C|34:40|4-6|0-0|1-1|0|6|6|1|2|1|1|2|+16|9|
|RJ Barrett^SG|38:15|7-17|0-4|3-4|2|6|8|4|1|0|2|4|+21|17|
|Elfrid Payton^PG|29:18|12-16|3-3|0-2|1|2|3|7|1|0|3|2|+15|27|
|Alec Burks|20:29|5-7|4-5|4-5|0|2|2|5|0|0|1|3|+21|18|
|Nerlens Noel|13:20|1-1|0-0|0-0|1|3|4|0|0|1|3|1|+4|2|
|Kevin Knox II||-|-|-|||||||||||
|Frank Ntilikina|18:42|4-6|4-4|0-0|0|1|1|0|0|0|1|4|+5|12|
|Jared Harper|1:52|0-1|0-0|0-0|0|0|0|0|0|0|0|0|-4|0|
|Theo Pinson|1:52|0-0|0-0|0-0|0|0|0|0|0|0|0|0|-4|0|
|Ignas Brazdeikis|1:16|0-1|0-0|2-2|1|0|1|0|0|0|0|0|-4|2|
|Immanuel Quickley||-|-|-|||||||||||
|Austin Rivers||-|-|-|||||||||||
|Dennis Smith Jr.||-|-|-|||||||||||
|Omari Spellman||-|-|-|||||||||||
|Obi Toppin||-|-|-|||||||||||
"""


if __name__ == '__main__':
  unittest.main()