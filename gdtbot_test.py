from datetime import datetime
from services import nba_data_test
from unittest.mock import MagicMock, patch

import gdtbot
import unittest

class GdtbotTest(unittest.TestCase):

  
  @patch('praw.Reddit')
  @patch('requests.get', side_effect=nba_data_test.mocked_requests_get)
  def test_execute(self, mock_get, mock_praw):  
    mock_subreddit = MagicMock()
    mock_reddit = MagicMock(['subreddit'])
    mock_reddit.subreddit.return_value = mock_subreddit
    mock_praw.return_value = mock_reddit
    now = datetime(2020, 12, 29, 17, 12, 52, 305157, gdtbot.UTC)

    # Execute.
    gdtbot.execute(now, 'subredditName')

    # Verify.
    # mock_reddit.subreddit.assert_called_with('subredditName')