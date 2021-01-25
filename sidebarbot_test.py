"""
Verifies that the sidebarbot correctly updates the sidebar text by mocking
calls to the Reddit and NBA Data APIs.
"""

from datetime import datetime
from services import nba_service_test
from unittest.mock import MagicMock, patch

import logging.config
import sidebarbot
import unittest

INITIAL_DESCR = """
Lorem ipsum....

[](#StartSchedule)
junk
[](#EndSchedule)

---

## Eastern Conference Standings

[](#StartEastStandings)

[](#EndEastStandings)

___

## Western Conference Standings

[](#StartWestStandings)

[](#EndWestStandings)

___

[](#StartRoster)[](#EndRoster)

___

bye
"""

# To isolate testing just the standings logic.
INITIAL_EAST_STANDINGS_DESCR = '[](#StartEastStandings)[](#EndEastStandings)'

INITIAL_TANK_STANDINGS_DESCR = '[](#StartTankStandings)[](#EndTankStandings)'

# To isolate testing just the schedule logic.
INITIAL_SCHEDULE_DESCR = '[](#StartSchedule)[](#EndSchedule)'

EXPECTED_UPDATED_DESCR = """
Lorem ipsum....

[](#StartSchedule)

Date|Team|Loc|Time/Outcome
:--:|:--:|:--:|:--:
Dec 13|[](/r/DetroitPistons)|Away|L 99-91
Dec 16|[](/r/clevelandcavs)|Home|W 100-93
Dec 18|[](/r/clevelandcavs)|Home|W 119-83
Dec 23|[](/r/pacers)|Away|L 121-107
Dec 26|[](/r/sixers)|Home|L 109-89
Dec 27|[](/r/MkeBucks)|Home|W 130-110
Today|[](/r/clevelandcavs)|Away|7:00 PM
Dec 31|[](/r/torontoraptors)|Away|7:30 PM
Jan 02|[](/r/pacers)|Away|7:00 PM
Jan 04|[](/r/AtlantaHawks)|Away|7:30 PM
Jan 06|[](/r/UtahJazz)|Home|7:30 PM
Jan 08|[](/r/thunder)|Home|7:30 PM

[](#EndSchedule)

---

## Eastern Conference Standings

[](#StartEastStandings)

 | | |Record|GB
:--:|:--:|:--|:--:|:--:
1|[](/r/torontoraptors)|Raptors|49-17|-
2|[](/r/bostonceltics)|Celtics|46-20|3
3|[](/r/clevelandcavs)|Cavaliers|38-27|10.5
4|[](/r/pacers)|Pacers|38-28|11
5|[](/r/washingtonwizards)|Wizards|38-29|11.5
6|[](/r/sixers)|76ers|35-29|13
7|[](/r/heat)|Heat|36-31|13.5
8|[](/r/MkeBucks)|Bucks|35-31|14
9|[](/r/DetroitPistons)|Pistons|30-36|19
10|[](/r/CharlotteHornets)|Hornets|29-38|20.5
11|[](/r/NYKnicks)|Knicks|24-43|25.5
12|[](/r/chicagobulls)|Bulls|23-43|26
13|[](/r/GoNets)|Nets|21-45|28
14|[](/r/OrlandoMagic)|Magic|20-47|29.5
15|[](/r/AtlantaHawks)|Hawks|20-47|29.5

[](#EndEastStandings)

___

## Western Conference Standings

[](#StartWestStandings)

 | | |Record|GB
:--:|:--:|:--|:--:|:--:
1|[](/r/rockets)|Rockets|51-14|-
2|[](/r/warriors)|Warriors|51-16|1
3|[](/r/ripcity)|Trail Blazers|40-26|11.5
4|[](/r/NOLAPelicans)|Pelicans|38-28|13.5
5|[](/r/timberwolves)|Timberwolves|39-29|13.5
6|[](/r/thunder)|Thunder|39-29|13.5
7|[](/r/NBASpurs)|Spurs|37-29|14.5
8|[](/r/LAClippers)|Clippers|36-29|15
9|[](/r/denvernuggets)|Nuggets|37-30|15
10|[](/r/UtahJazz)|Jazz|37-30|15
11|[](/r/lakers)|Lakers|29-36|22
12|[](/r/mavericks)|Mavericks|21-45|30.5
13|[](/r/kings)|Kings|21-46|31
14|[](/r/suns)|Suns|19-49|33.5
15|[](/r/memphisgrizzlies)|Grizzlies|18-48|33.5

[](#EndWestStandings)

___

[](#StartRoster)

No.|Name|Position
:--:|:--|:--:
18|Alec Burks|G
17|Ignas Brazdeikis|F
9|RJ Barrett|F/G
25|Reggie Bullock|G/F

[](#EndRoster)

___

bye
"""


class SidebarBotTest(unittest.TestCase):

  def setUp(self):
    logging.basicConfig(level=logging.ERROR)
    self.logger = logging.getLogger(__name__)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_service_test.mocked_requests_get)
  def test_execute_newChanges_updatesDescription(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': INITIAL_DESCR}
    mock_wiki = MagicMock(['edit'])
    mock_subreddit = MagicMock(mod=mock_mod, wiki={'config/sidebar': mock_wiki})
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    now = datetime(2020, 12, 29, 17, 12, 52, 305157, sidebarbot.UTC)

    # Execute.
    sidebarbot.execute(self.logger, now, 'subredditName', False)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_wiki.edit.assert_called_with(EXPECTED_UPDATED_DESCR)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_service_test.mocked_requests_get)
  def test_execute_noChanges_doesNotUpdateDescrip(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': EXPECTED_UPDATED_DESCR}
    mock_subreddit = MagicMock(mod=mock_mod)
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    now = datetime(2020, 12, 29, 17, 12, 52, 305157, sidebarbot.UTC)

    # Execute.
    sidebarbot.execute(self.logger, now, 'subredditName', False)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_mod.update.assert_not_called()

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_service_test.mocked_requests_get)
  def test_execute_tankChanges_updatesDescription(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': INITIAL_TANK_STANDINGS_DESCR}
    mock_wiki = MagicMock(['edit'])
    mock_subreddit = MagicMock(mod=mock_mod, wiki={'config/sidebar': mock_wiki})
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    now = datetime(2020, 12, 29, 17, 12, 52, 305157, sidebarbot.UTC)

    # Execute.
    sidebarbot.execute(self.logger, now, 'subredditName', True)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_wiki.edit.assert_called_with("""[](#StartTankStandings)

 | | |Record|GB
:--:|:--:|:--|:--:|:--:
1|[](/r/memphisgrizzlies)|Grizzlies|18-48|-
2|[](/r/suns)|Suns|19-49|1
3|[](/r/OrlandoMagic)|Magic|20-47|1.5
4|[](/r/AtlantaHawks)|Hawks|20-47|1.5
5|[](/r/kings)|Kings|21-46|2.5
6|[](/r/GoNets)|Nets|21-45|3
7|[](/r/mavericks)|Mavericks|21-45|3
8|[](/r/chicagobulls)|Bulls|23-43|5
9|[](/r/NYKnicks)|Knicks|24-43|5.5
10|[](/r/CharlotteHornets)|Hornets|29-38|10.5

[](#EndTankStandings)""")

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_service_test.mocked_requests_get)
  def test_execute_scheduleWithYesterdayTomorrow(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': INITIAL_SCHEDULE_DESCR}
    mock_wiki = MagicMock(['edit'])
    mock_subreddit = MagicMock(mod=mock_mod, wiki={'config/sidebar': mock_wiki})
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    now = datetime(2020, 12, 28, 10, 00, 00, 00, sidebarbot.UTC)

    # Execute.
    sidebarbot.execute(self.logger, now, 'subredditName', False)

    # Verify.
    mock_wiki.edit.assert_called_with("""[](#StartSchedule)

Date|Team|Loc|Time/Outcome
:--:|:--:|:--:|:--:
Dec 13|[](/r/DetroitPistons)|Away|L 99-91
Dec 16|[](/r/clevelandcavs)|Home|W 100-93
Dec 18|[](/r/clevelandcavs)|Home|W 119-83
Dec 23|[](/r/pacers)|Away|L 121-107
Dec 26|[](/r/sixers)|Home|L 109-89
Yesterday|[](/r/MkeBucks)|Home|W 130-110
Tomorrow|[](/r/clevelandcavs)|Away|7:00 PM
Dec 31|[](/r/torontoraptors)|Away|7:30 PM
Jan 02|[](/r/pacers)|Away|7:00 PM
Jan 04|[](/r/AtlantaHawks)|Away|7:30 PM
Jan 06|[](/r/UtahJazz)|Home|7:30 PM
Jan 08|[](/r/thunder)|Home|7:30 PM

[](#EndSchedule)""")


if __name__ == '__main__':
  unittest.main()
