from services import nba_data
from unittest.mock import patch

import os.path
import sidebarbot
import unittest

# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
  
  class MockResponse:
    
    def __init__(self, file_name, status_code):
      with open(file_name, 'r') as f:
        self.content = f.read().encode('utf-8')
      self.status_code = status_code
    
    def raise_for_status(self):
      pass

  requested_url = args[0]
  testdata_path = 'services/testdata/' + requested_url.split('/')[-1]
  if os.path.isfile(testdata_path):
    return MockResponse(testdata_path, 200)
  return MockResponse(None, 404)


class SidebarBotTest(unittest.TestCase):
  @patch('requests.get', side_effect=mocked_requests_get)
  def test_build_tank_standings(self, mock_get):
    teams = nba_data.teams('2018')
    standings = sidebarbot.build_tank_standings(teams)
    self.assertEqual(standings, """ | | |Record|GB
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


if __name__ == '__main__':
  unittest.main()
