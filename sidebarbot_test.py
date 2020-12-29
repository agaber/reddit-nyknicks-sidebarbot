"""
Verifies that the sidebarbot correctly updates the sidebar text by mocking
calls to the Reddit and NBA Data APIs.
"""

from services import nba_data_test
from unittest.mock import MagicMock, patch

import sidebarbot
import unittest

INITIAL_DESCR = """
Lorem ipsum....

[](#StartSchedule)
junk
[](#EndSchedule)

---

[](#StartStandings)

[](#EndStandings)

___

[](#StartRoster)[](#EndRoster)

___

bye
"""

EXPECTED_UPDATED_DESCR = """
Lorem ipsum....

[](#StartSchedule)

Date|Team|Loc|Time/Outcome
:--:|:--:|:--:|:--:
Dec 11|[](/r/DetroitPistons)|Away|W 90-84
Dec 13|[](/r/DetroitPistons)|Away|L 99-91
Dec 16|[](/r/clevelandcavs)|Home|W 100-93

[](#EndSchedule)

---

[](#StartStandings)

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

[](#EndStandings)

___

[](#StartRoster)

Name|No.|Position
:--|:--:|:--:
Alec Burks|18|G
Ignas Brazdeikis|17|F
RJ Barrett|9|F/G
Reggie Bullock|25|G/F

[](#EndRoster)

___

bye
"""

EXPECTED_UPDATED_TANKING_DESCR = """
Lorem ipsum....

[](#StartSchedule)

Date|Team|Loc|Time/Outcome
:--:|:--:|:--:|:--:
Dec 11|[](/r/DetroitPistons)|Away|W 90-84
Dec 13|[](/r/DetroitPistons)|Away|L 99-91
Dec 16|[](/r/clevelandcavs)|Home|W 100-93

[](#EndSchedule)

---

[](#StartStandings)

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

[](#EndStandings)

___

[](#StartRoster)

Name|No.|Position
:--|:--:|:--:
Alec Burks|18|G
Ignas Brazdeikis|17|F
RJ Barrett|9|F/G
Reggie Bullock|25|G/F

[](#EndRoster)

___

bye
"""


class SidebarBotTest(unittest.TestCase):

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_execute_newChanges_updatesDescription(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': INITIAL_DESCR}
    mock_subreddit = MagicMock(mod=mock_mod)
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit

    # Execute.
    sidebarbot.execute('subredditName', False)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_mod.update.assert_called_with(description=EXPECTED_UPDATED_DESCR)

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_execute_noChanges_doesNotUpdateDescrip(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': EXPECTED_UPDATED_DESCR}
    mock_subreddit = MagicMock(mod=mock_mod)
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit

    # Execute.
    sidebarbot.execute('subredditName', False)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_mod.update.assert_not_called()

  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_execute_tankChanges_updatesDescription(self, mock_get, mock_praw):
    # Expect it to lookup the initial description from the reddit API.
    mock_mod = MagicMock()
    mock_mod.settings.return_value = {'description': INITIAL_DESCR}
    mock_subreddit = MagicMock(mod=mock_mod)
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit

    # Execute.
    sidebarbot.execute('subredditName', True)

    # Verify.
    mock_reddit.subreddit.assert_called_with('subredditName')
    mock_mod.update.assert_called_with(
        description=EXPECTED_UPDATED_TANKING_DESCR)


if __name__ == '__main__':
  unittest.main()
