"""
Runs Knicks bots every minute. This is the main entry point for the heroku app.

See https://devcenter.heroku.com/articles/clock-processes-python.
See https://able.bio/rhett/how-to-set-and-get-environment-variables-in-python--274rgt5.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from constants import UTC
from datetime import datetime
from decouple import config
from game_thread_bot import GameThreadBot
from services.nba_service import NbaService
import logging.config
import os
import praw
import sidebarbot


sched = BlockingScheduler()
logging.config.fileConfig('logging_heroku.conf')
logger = logging.getLogger('heroku_logger')
nba_service = NbaService(logger)

class Config:
  """Container for reddit environment variables."""

  def __init__(
      self,
      client_id,
      client_secret,
      password,
      subreddit_name='nyknicks',
      username='nyknicks-automod',
      user_agent='python-praw'):
    self.client_id = client_id
    self.client_secret = client_secret
    self.password = password
    self.subreddit_name = subreddit_name
    self.username = username
    self.user_agent = user_agent

  @staticmethod
  def from_env_vars():
    return Config(
        client_id=config('client_id'),
        client_secret=config('client_secret'),
        password=config('password'),
        subreddit_name=config('subreddit_name', 'nyknicks'),
        username=config('username', 'nyknicks-automod'),
        user_agent=config('user_agent', 'python-praw'))

  def reddit(self):
    return praw.Reddit(
        client_id=self.client_id,
        client_secret=self.client_secret,
        password=self.password,
        username=self.username,
        user_agent=self.user_agent)


@sched.scheduled_job('interval', seconds=10)
def every_minute():
  config = Config.from_env_vars()
  now = datetime.now(UTC)
  logger.info(
      f'Using subreddit "{config.subreddit_name}" and user "{config.username}".')

  # Run the sidebar bot.
  sidebarbot.execute(logger, now, config.subreddit_name, config.username)

  # Run the game thread bot.
  gtbot = GameThreadBot(
      logger, nba_service, now, config.reddit(), config.subreddit_name, 0)
  gtbot.run()

  logger.info('Done.')

sched.start()