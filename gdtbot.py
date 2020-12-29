from datetime import date, timedelta, datetime
from enum import Enum
from optparse import OptionParser
from pytz import timezone
from services import nba_data

import logging
import logging.config
import praw
import traceback

# https://github.com/HokageEzio/KnicksGDT/blob/main/Knicks%20Bot.py

EASTERN_TIMEZONE = timezone('US/Eastern')
UTC = timezone('UTC')

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("gdtbot")


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


def execute(now, subreddit_name):
  season_year = nba_data.current_year()
  schedule = nba_data.schedule('knicks', season_year)
  last_played_idx = schedule['league']['lastStandardGamePlayedIndex']
  games = schedule['league']['standard']

  previous_game = games[last_played_idx]
  next_game = games[last_played_idx + 1] \
      if len(games) >= last_played_idx + 1 else None

  reddit = praw.Reddit('nyknicks-sidebarbot', user_agent='python-praw')

  # This first step needs to decide if it should make a game or post game thread.
  # It then needs to decide if it should create a new thread or update an existing one.
  # The former involves creating a new sticky thread and returning a reference to that.
  # The latter involves finding an existing thread with the expected title (?) and returning
  # a reference to that.

  # That's the hard part, the rest is just building up the text and I can 
  # probably reuse HokageEzio's code for that.

  # gametime = dateutil.parser \
  #     .parse(game['startTimeUTC']) \
  #     .astimezone(EASTERN_TIMEZONE)

  # check schedule["league"]["lastStandardGamePlayedIndex"]
  # that will give you the next game (if any)
  # compare the next game time to today's timestamp:
  #   if the game is within X minutes, update or create a game thread
  #   if the game is over within X hours, update or create a post game thread

   
if __name__ == "__main__":
  parser = OptionParser()
  (options, args) = parser.parse_args()

  if len(args) != 1:
    logger.error(f'Invalid command line arguments: {args}')
    raise SystemExit(f'Usage: {sys.argv[0]} subreddit')

  subreddit_name = args[0]
  logger.info(f'Using subreddit: {subreddit_name}')

  try:
    execute(datetime.now(UTC), subreddit_name)
  except:
    logger.error(traceback.format_exc())
  
