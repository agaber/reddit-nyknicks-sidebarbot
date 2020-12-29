from services import nba_data
from services import nba_data_test
from unittest.mock import patch

import os.path
import sidebarbot
import unittest


class SidebarBotTest(unittest.TestCase):

  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_build_tank_standings(self, mock_get):
    teams = nba_data.teams('2018')
    standings = sidebarbot.build_tank_standings(teams)
    self.assertEqual(
        standings, """ | | |Record|GB
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
10|[](/r/CharlotteHornets)|Hornets|29-38|10.5""")

  # @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  # def test_execute(self, mock_get):
  #   sidebar_markdown = sidebarbot.execute('NYKnicks')
  #   self.assertEqual(sidebar_markdown, 'wrong')


if __name__ == '__main__':
  unittest.main()
