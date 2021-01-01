from constants import CENTRAL_TIMEZONE, EASTERN_TIMEZONE, MOUNTAIN_TIMEZONE, PACIFIC_TIMEZONE, TEAM_SUB_MAP, UTC
from datetime import date, timedelta, datetime
from enum import Enum, unique
from optparse import OptionParser
from pytz import timezone
from services import nba_data

import dateutil.parser
import logging
import logging.config
import praw
import traceback

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("gdtbot")


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


class GameThreadBot:

  def __init__(self, now: datetime, subreddit_name: str):
    self.now = now
    self.reddit = praw.Reddit('nyknicks-automod')
    self.subreddit_name = subreddit_name

  def run(self):
    season_year = nba_data.current_year()
    schedule = nba_data.schedule('knicks', season_year)
    game = self._get_current_game(schedule)
    action = self._get_action(game)
    
    if action == Action.DO_NOTHING:
      logger.info('Nothing to do. Goodbye.')
      return

    boxscore = _get_boxscore(game)
    teams = nba_data.teams(season_year)
    title, body = _build_game_thread_text(boxscore, teams) \
        if action == Action.DO_GAME_THREAD \
        else _build_postgame_thread_text(boxscore, teams)

    _create_or_update_game_thread(action, title, body)

  def _get_boxscore(self, game):
    game_start = game['startDateEastern']
    game_id = game['gameId']
    return nba_data.boxscore(game_start, game_id)
    
  def _get_current_game(self, schedule):
    """Returns the nba_data game object we want to focus on right now.
    This implementation searches for a game that looks like it might be on the
    same day (within X number of hours because technically night games can spill
    over into the next day). This solution won't work for double-headers.

    This implementation also relies heavily on NBA's lastStandardGamePlayedIndex
    field to tell us where to start looking, rather than scanning the entire
    schedule.
    """
    last_played_idx = schedule['league']['lastStandardGamePlayedIndex']
    games = schedule['league']['standard']

    # If the previous game was less than 6 hours ago, then use that.
    # It assumes that two games will never be closer than six hours apart.
    previous_game = games[last_played_idx]
    previous_gametime = dateutil.parser.parse(previous_game['startTimeUTC'])
    if previous_gametime + timedelta(hours=6) >= self.now:
      return previous_game

    # Season is over.
    if len(games) < last_played_idx + 1:
      return None

    # If the next game starts in an hour then use that
    next_game = games[last_played_idx + 1]
    next_gametime = dateutil.parser.parse(next_game['startTimeUTC'])
    if next_gametime - timedelta(hours=1) <= self.now:
      return next_game
    
    # Should never get this far.
    return None

  def _get_action(self, game):
    gametime = dateutil.parser.parse(game['startTimeUTC'])
    has_score = bool(game['vTeam']['score'] + game['hTeam']['score'])
    if gametime - timedelta(hours=1) <= self.now and not has_score:
      return Action.DO_GAME_THREAD
    elif gametime + timedelta(hours=6) >= self.now and has_score:
      return Action.DO_POST_GAME_THREAD
    else:
      return Action.DO_NOTHING

  def _build_game_thread_text(self, boxscore, teams):
    basicGameData = boxscore['basicGameData']

    if basicGameData['hTeam']['triCode'] == "NYK":
      us = 'hTeam'
      them = 'vTeam'
      homeAwaySign = "vs"
    else:
      us = 'vTeam'
      them = 'hTeam'
      homeAwaySign = "@"

    broadcasters = basicGameData['watch']['broadcast']['broadcasters']
    nationalBroadcaster = "-" if len(broadcasters['national']) == 0 \
        else broadcasters['national'][0]['longName']
    knicksBroadcaster = broadcasters[us][0]['longName']
    otherBroadcaster = broadcasters[them][0]['longName']

    knicksWinLossRecord = f"({basicGameData[us]['win']}-{basicGameData['hTeam']['loss']})"
    otherWinLossRecord = f"({basicGameData[them]['win']}-{basicGameData['vTeam']['loss']})"
    otherSubreddit = TEAM_SUB_MAP[teams[basicGameData[them]['teamId']]['nickname']]
    otherTeamName = teams[basicGameData[them]['teamId']]['fullName']
    otherTeamNickname = teams[basicGameData[them]['teamId']]['nickname']
    location = (f'{basicGameData["arena"]["city"]}, '
        + f'{basicGameData["arena"]["stateAbbr"]} '
        + f'{basicGameData["arena"]["country"]}')
    arena = basicGameData['arena']['name']
    
    start_time_utc = dateutil.parser.parse(basicGameData['startTimeUTC'])
    eastern = start_time_utc.astimezone(EASTERN_TIMEZONE).strftime("%I:%M %p")
    central = start_time_utc.astimezone(CENTRAL_TIMEZONE).strftime("%I:%M %p")
    mountain = start_time_utc.astimezone(MOUNTAIN_TIMEZONE).strftime("%I:%M %p")
    pacific = start_time_utc.astimezone(PACIFIC_TIMEZONE).strftime("%I:%M %p")

    body = f"""
##General Information
**TIME**|**BROADCAST**|**Location and Subreddit**|
:------------|:------------------------------------|:-------------------|
{eastern} Eastern   |Knicks Broadcast: {knicksBroadcaster}            |{location}|
{central} Central   |{otherTeamNickname} Broadcast: {otherBroadcaster}|{arena}|
{mountain} Mountain |National Broadcast: {nationalBroadcaster}        |r/NYKnicks|
{pacific} Pacific   |                                                 |r/{otherSubreddit}|
-----
[Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
"""

    # TODO: Add in-game stats:
    # https://github.com/HokageEzio/nbaspurs-bot/blob/master/sidebar-nbaspurs.py#L393

    dateTitle = self.now.astimezone(EASTERN_TIMEZONE).strftime("%B %d, %Y")
    title = (f'[Game Thread] The New York Knicks {knicksWinLossRecord} '
        + f'{homeAwaySign} The {otherTeamName} {otherWinLossRecord} - '
        + f'({dateTitle})')

    return (title, body)

  def _build_postgame_thread_text(self, boxscore, teams):
    pass

  def _create_or_update_game_thread(action, title, body):
    pass

   
if __name__ == "__main__":
  parser = OptionParser()
  (options, args) = parser.parse_args()

  if len(args) != 1:
    logger.error(f'Invalid command line arguments: {args}')
    raise SystemExit(f'Usage: {sys.argv[0]} subreddit')

  subreddit_name = args[0]
  logger.info(f'Using subreddit: {subreddit_name}')

  try:
    bot = GameThreadBot(datetime.now(UTC), subreddit_name)
    bot.run()
  except:
    logger.error(traceback.format_exc())
  
