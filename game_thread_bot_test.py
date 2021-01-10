from constants import UTC
from datetime import datetime, timedelta
from game_thread_bot import GAME_THREAD_PREFIX, POST_GAME_PREFIX
from game_thread_bot import Action, GameThreadBot
from services.fake_nba_service import FakeNbaService
from unittest.mock import MagicMock, patch

import logging.config
import unittest

EXPECTED_GAMETHREAD_TEXT = """##### General Information

**TIME**|**BROADCAST**|**Media**|**Location and Subreddit**|
:------------|:------------------------------------|:------------------------------------|:-------------------|
07:00 PM Eastern   | National Broadcast: N/A           |[Game Preview](https://www.nba.com/game/nyk-vs-cle-0022000046)| Cleveland, OH|
06:00 PM Central   | Knicks Broadcast: MSG               |[Play By Play](https://www.nba.com/game/nyk-vs-cle-0022000046/play-by-play)| Rocket Mortgage FieldHouse|
05:00 PM Mountain | Cavaliers Broadcast: Fox Sports Ohio |[Box Score](https://www.nba.com/game/nyk-vs-cle-0022000046/box-score#box-score)| r/NYKnicks|
04:00 PM Pacific   | [NBA League Pass](https://www.nba.com/game/nyk-vs-cle-0022000046?watch)                   || r/clevelandcavs|

##### Starting lineups

New York Knicks|Cleveland Cavaliers|
:--|:--|
Julius Randle (SF)|Cedi Osman (SF)|
Reggie Bullock (PF)|Larry Nance Jr. (PF)|
Mitchell Robinson (C)|Andre Drummond (C)|
RJ Barrett (SG)|Collin Sexton (SG)|
Elfrid Payton (PG)|Darius Garland (PG)|

##### Inactive

|New York Knicks|Cleveland Cavaliers|
|:--|:--|
||Matthew Dellavedova (G)|
||Kevin Love (F/C)|
||Isaac Okoro (F/G)|
||Kevin Porter Jr. (G/F)|
||Dylan Windler (G/F)|

##### Officials

||
|:--|
|Ed Malloy, Scott Twardoski, Ashley Moyer-Gleich|

##### Score

|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|
|:---|:--:|:--:|:--:|:--:|:--:|
|New York Knicks|29|24|18|24|95|
|Cleveland Cavaliers|15|31|18|22|86|

-----

[Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
"""

EXPECTED_POSTGAME_TEXT = """##### Game Summary

|||
|:--|:--|
|**Score**|[](/r/MkeBucks) **110 -  130** [](/r/NYKnicks)|
|**Box Score**|[NBA](https://www.nba.com/game/MIL-vs-NYK-0022000036), [Yahoo](http://sports.yahoo.com/nba/milwaukee-bucks-new-york-knicks-2020122718)|
|**Location**|New York, NY|
|**Arena**|Madison Square Garden|
|**Attendance**|No in-person attendance|
|**Start Time**|December 27, 2020 7:30 PM EST|
|**Game Duration**|2 hours and 19 minutes|
|**Officials**|Scott Wall, Zach Zarba, Evan Scott|

##### Line Score

|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|
|:---|:--:|:--:|:--:|:--:|:--:|
|Milwaukee Bucks|27|18|30|35|110|
|New York Knicks|30|31|35|34|130|

##### Team Stats

|**Team**|**PTS**|**FG**|**FG%**|**3P**|**3P%**|**FT**|**FT%**|**OREB**|**TREB**|**AST**|**PF**|**STL**|**TO**|**BLK**|
|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
|Milwaukee Bucks|110|41-95|43.2%|7-38|18.4%|21-29|72.4%|17|44|24|21|7|11|5|
|New York Knicks|130|46-85|54.1%|16-27|59.3%|22-27|81.5%|8|46|27|23|5|15|4|

|**Team**|**Biggest Lead**|**Longest Run**|**PTS: In Paint**|**PTS: Off TOs**|**PTS: Fastbreak**|
|:--|:--:|:--:|:--:|:--:|:--:|
|Milwaukee Bucks|+2|8|60|20|12|
|New York Knicks|+28|11|48|15|5|
  
##### Team Leaders

|**Team**|**Points**|**Rebounds**|**Assists**|
|:--|:--|:--|:--|
|Milwaukee Bucks|**27** Giannis Antetokounmpo|**13** Giannis Antetokounmpo|**5** Giannis Antetokounmpo|
|New York Knicks|**29** Julius Randle|**14** Julius Randle|**7** Julius Randle|

##### Player Stats

**BUCKS**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
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

**KNICKS**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
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


class GameThreadBotTest(unittest.TestCase):

  @patch('praw.Reddit')
  def setUp(self, mock_praw):
    logging.basicConfig(level=logging.ERROR)
    self.logger = logging.getLogger(__name__)
    self.fake_nba_service = FakeNbaService()
    self.mock_praw = mock_praw
    self.mock_reddit = MagicMock(['subreddit', 'user'])
    self.mock_reddit.user = FakeUser('nyknicks-automod')
    self.mock_praw.return_value = self.mock_reddit
    self.mock_subreddit = MagicMock(['new', 'search', 'submit'])
    self.mock_reddit.subreddit.return_value = self.mock_subreddit

  def bot(self, now: datetime):
    return GameThreadBot(
      logger=self.logger,
      nba_service=self.fake_nba_service,
      now=now,
      reddit=self.mock_reddit,
      subreddit_name='test_NYKnicks')

  def test_run_createGameThread(self):
    # 1 hour before tip-off.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
    self.mock_subreddit.new.return_value = [
      FakeThread(author='macdoogles', title="shitpost", created_utc=now),
      FakeThread(author='nyknicks-automod', title="nope", created_utc=now),
    ]
    mock_submit_mod = MagicMock(['sticky'])
    self.mock_subreddit.submit.return_value = MagicMock(
      mod=mock_submit_mod, title='game thread')

    # Execute.
    self.bot(now).run()

    # Verify.
    self.mock_subreddit.new.assert_called_once()

    expected_title = ('[Game Thread] The New York Knicks (2-2) @ The Cleveland '
                      'Cavaliers (3-1) - (December 29, 2020)');

    self.mock_subreddit.submit.assert_called_once_with(
      expected_title,
      selftext=EXPECTED_GAMETHREAD_TEXT,
      send_replies=False)
    mock_submit_mod.sticky.assert_called_once()

  def test_run_updateGameThread(self):
    # 1 hour before tip-off.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)

    shitpost = FakeThread(
      author='macdoogles',
      created_utc=now,
      selftext='better shut up',
      title='no u')
    otherthread = FakeThread(
      author='nyknicks-automod',
      created_utc=now,
      selftext="it's happening!",
      title="This is not the thread you're looking for")
    gamethread = FakeThread(
      author='nyknicks-automod',
      created_utc=now,
      selftext='we did it!',
      title=f'{GAME_THREAD_PREFIX} A classic match of Good vs. Evil')
    self.mock_subreddit.new.return_value = [shitpost, otherthread, gamethread]

    # Execute.
    self.bot(now).run()

    # Verify.
    self.mock_subreddit.new.assert_called_once()
    self.mock_subreddit.submit.assert_not_called()
    self.assertEqual(gamethread.selftext, EXPECTED_GAMETHREAD_TEXT)
    self.assertEqual(shitpost.selftext, 'better shut up')
    self.assertEqual(otherthread.selftext, "it's happening!")

  @patch('random.choice')
  def test_run_createPostGameThread(self, mock_random):
    # 3.5 hours after tip-off.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    mock_random.return_value = 'defeat'

    self.mock_subreddit.new.return_value = [
      FakeThread(author='macdoogles', created_utc=now)
    ]
    mock_submit_mod = MagicMock(['sticky'])
    self.mock_subreddit.submit.return_value = MagicMock(
      mod=mock_submit_mod, title='post game thread')

    # Execute.
    self.bot(now).run()

    # Verify.
    self.mock_subreddit.new.assert_called_once()

    expected_title = ('[Post Game Thread] The New York Knicks (1-2) defeat the '
                      'Milwaukee Bucks (1-2), 130-110');

    self.mock_subreddit.submit.assert_called_once_with(
      expected_title,
      selftext=EXPECTED_POSTGAME_TEXT,
      send_replies=False)
    mock_submit_mod.sticky.assert_called_once()

  @patch('random.choice')
  def test_run_updatePostGameThread(self, mock_random):
    # 3.5 hours after tip-off.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    mock_random.return_value = 'defeat'

    shitpost = FakeThread(
      author='macdoogles',
      created_utc=now,
      selftext='better shut up',
      title='u mad bro?')
    otherthread = FakeThread(
      author='nyknicks-automod',
      created_utc=now,
      selftext="it's happening!",
      title="This is not the thread you're looking for")
    gamethread = FakeThread(
      author='nyknicks-automod',
      created_utc=now,
      selftext='we did it!',
      title=f'{POST_GAME_PREFIX} Knicks win!')
    self.mock_subreddit.new.return_value = [shitpost, otherthread, gamethread]

    # Execute.
    self.bot(now).run()

    # Verify.
    self.mock_subreddit.new.assert_called_once()
    self.mock_subreddit.submit.assert_not_called()
    self.assertEqual(gamethread.selftext, EXPECTED_POSTGAME_TEXT)
    self.assertEqual(shitpost.selftext, 'better shut up')
    self.assertEqual(otherthread.selftext, "it's happening!")

  @patch('random.choice')
  def test_run_withObsoletePost_createNewPostGameThread(self, mock_random):
    # 3.5 hours after tip-off.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)
    mock_random.return_value = 'defeat'
    shitpost = FakeThread(
      author='macdoogles',
      created_utc=now,
      selftext='better shut up',
      title='u mad bro?')
    otherthread = FakeThread(
      author='nyknicks-automod',
      created_utc=now,
      selftext="it's happening!",
      title="This is not the thread you're looking for")
    # This thread would otherwise match but it is too old and should be ignored.
    gamethread = FakeThread(
      author='nyknicks-automod',
      created_utc=now - timedelta(hours=10),
      selftext='we did it!',
      title=f'{POST_GAME_PREFIX} Knicks win!')
    self.mock_subreddit.new.return_value = [shitpost, otherthread, gamethread]
    mock_submit_mod = MagicMock(['sticky'])
    self.mock_subreddit.submit.return_value = MagicMock(
      mod=mock_submit_mod, title='post game thread')

    # Execute.
    self.bot(now).run()

    # Verify.
    expected_title = ('[Post Game Thread] The New York Knicks (1-2) defeat the '
                      'Milwaukee Bucks (1-2), 130-110');
    self.mock_subreddit.submit.assert_called_once_with(
      expected_title,
      selftext=EXPECTED_POSTGAME_TEXT,
      send_replies=False)
    mock_submit_mod.sticky.assert_called_once()

  # TODO: More tests needed for post game title generation:
  # - with 1 OT
  # - with many OTs
  # - road team wins
  # - home team wins
  # - will most likely need to call _build_postgame_thread_text directly for that
  #   in order to mock out the nba data API calls

  def test_get_current_game_tooEarly_doNothing(self):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 29, 12, 0, 0, 0, UTC)
    schedule = self.fake_nba_service.schedule('knicks', '2020')
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertIsNone(game)
    self.assertEqual(action, Action.DO_NOTHING)

  def test_get_current_game_1HourBefore_doGameThread(self):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 29, 23, 0, 0, 0, UTC)
    schedule = self.fake_nba_service.schedule('knicks', '2020')
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertEqual(action, Action.DO_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201229/NYKCLE')

  def test_get_current_game_gameStarted_doGameThread(self):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 30, 1, 0, 0, 0, UTC)
    schedule = self.fake_nba_service.schedule('knicks', '2020')
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertEqual(action, Action.DO_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201229/NYKCLE')

  def test_get_current_game_afterGame_postGameThread(self):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)
    schedule = self.fake_nba_service.schedule('knicks', '2020')
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertEqual(action, Action.DO_POST_GAME_THREAD)
    self.assertEqual(game['gameUrlCode'], '20201227/MILNYK')

  def test_get_current_game_tooLate_doNothing(self):
    # Previous game (20201227/MILNYK) started at 2020-12-28T00:30:00.000Z.
    # Next game (20201229/NYKCLE) starts at 2020-12-30T00:00:00.000Z.
    now = datetime(2020, 12, 28, 7, 0, 0, 0, UTC)
    schedule = self.fake_nba_service.schedule('knicks', '2020')
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertEqual(action, Action.DO_NOTHING)
    self.assertIsNone(game)

  def test_get_current_game_seasonOver_doNothing(self):
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
    (action, game) = self.bot(now)._get_current_game(schedule)
    self.assertEqual(action, Action.DO_NOTHING)
    self.assertIsNone(game)

  def test_build_linescore_withNoData_returnNone(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore['basicGameData']['vTeam']['linescore'] = []
    boxscore['basicGameData']['hTeam']['linescore'] = []

    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertIsNone(linescore)

  def test_build_linescore_withOneQuarter(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore = self.update_boxscore(boxscore, [27, 0, 0, 0], [30, 0, 0, 0], 1)

    # Execute
    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertEqual(
      linescore,
      ('|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|\n'
       '|:---|:--:|:--:|:--:|:--:|:--:|\n'
       '|Milwaukee Bucks|27|-|-|-|27|\n'
       '|New York Knicks|30|-|-|-|30|'))

  def test_build_linescore_withTwoQuarters(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore = self.update_boxscore(boxscore, [27, 18, 0, 0], [30, 31, 0, 0], 2)

    # Execute
    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertEqual(
      linescore,
      ('|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|\n'
       '|:---|:--:|:--:|:--:|:--:|:--:|\n'
       '|Milwaukee Bucks|27|18|-|-|45|\n'
       '|New York Knicks|30|31|-|-|61|'))

  def test_build_linescore_withThreeQuarters(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore = self.update_boxscore(
      boxscore, [27, 18, 30, 0], [30, 31, 35, 0], 3)

    # Execute
    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertEqual(
      linescore,
      ('|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**Total**|\n'
       '|:---|:--:|:--:|:--:|:--:|:--:|\n'
       '|Milwaukee Bucks|27|18|30|-|75|\n'
       '|New York Knicks|30|31|35|-|96|'))

  def test_build_linescore_withOneOvertime(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore = self.update_boxscore(
      boxscore,
      home_scores=[27, 18, 30, 40, 15],
      road_scores=[30, 31, 35, 19, 16],
      period=4)  # I don't actually know what this value will be for OT.

    # Execute
    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertEqual(
      linescore,
      ('|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**OT1**|**Total**|\n'
       '|:---|:--:|:--:|:--:|:--:|:--:|:--:|\n'
       '|Milwaukee Bucks|27|18|30|40|15|130|\n'
       '|New York Knicks|30|31|35|19|16|131|'))

  def test_build_linescore_withTwoOvertimes(self):
    teams = self.fake_nba_service.teams('2020')
    now = datetime(2020, 12, 27, 3, 0, 0, 0, UTC)

    # Read a real boxscore response and modify it for our test case.
    boxscore = self.fake_nba_service.boxscore('20201227', '0022000036')
    boxscore = self.update_boxscore(
      boxscore,
      home_scores=[27, 18, 30, 40, 15, 10],
      road_scores=[30, 31, 35, 19, 15, 13],
      period=4)

    # Execute
    linescore = self.bot(now)._build_linescore(boxscore, teams)

    self.assertEqual(
      linescore,
      ('|**Team**|**Q1**|**Q2**|**Q3**|**Q4**|**OT1**|**OT2**|**Total**|\n'
       '|:---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|\n'
       '|Milwaukee Bucks|27|18|30|40|15|10|140|\n'
       '|New York Knicks|30|31|35|19|15|13|143|'))

  @staticmethod
  def update_boxscore(boxscore, home_scores, road_scores, period):
    def score(scores):
      return [{'score': str(s)} for s in scores]
    boxscore['basicGameData']['vTeam']['linescore'] = score(home_scores)
    boxscore['basicGameData']['hTeam']['linescore'] = score(road_scores)
    boxscore['basicGameData']['vTeam']['score'] = str(sum(home_scores))
    boxscore['basicGameData']['hTeam']['score'] = str(sum(road_scores))
    boxscore['basicGameData']['period']['current'] = period
    return boxscore


class FakeThread:
  def __init__(self, author, created_utc: datetime, selftext='', title=''):
    self.author = author
    self.created_utc = created_utc.timestamp()
    self.selftext = selftext
    self.title = title

  def edit(self, selftext):
    self.selftext = selftext


class FakeMe:
  def __init__(self, name):
    self.name = name


class FakeUser:
  def __init__(self, name):
    self._me = FakeMe(name)

  def me(self, use_cache=True):
    return self._me if not use_cache else None


if __name__ == '__main__':
  unittest.main()
