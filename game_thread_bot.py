"""
A command line tool that manages game threads on the New York Knicks subreddit.

The tool is meant to be run as a cron job, but it also contains a reusable class
that can be used in other contexts (i.e., an AppEngine/GCE web server). The tool
will run once and then terminate. In many cases it will have nothing to do. To
run this on a continuous basis, try using crontab (see the README.md).
"""

from constants import CENTRAL_TIMEZONE, EASTERN_TIMEZONE, MOUNTAIN_TIMEZONE, PACIFIC_TIMEZONE, TEAM_SUB_MAP, UTC
from datetime import timedelta, datetime
from enum import Enum
from optparse import OptionParser
from services import nba_data

import dateutil.parser
import logging.config
import praw
import sys
import traceback

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('gdtbot')


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


class GameThreadBot:

  def __init__(self, now: datetime, subreddit_name: str):
    self.now = now
    self.reddit = praw.Reddit('nyknicks-automod')
    self.subreddit = self.reddit.subreddit(subreddit_name)

  def run(self):
    season_year = nba_data.current_year()
    schedule = nba_data.schedule('knicks', season_year)
    (action, game) = self._get_current_game(schedule)

    if action == Action.DO_NOTHING:
      logger.info('Nothing to do. Goodbye.')
      return

    boxscore = self._get_boxscore(game)
    teams = nba_data.teams(season_year)
    title, body = self._build_game_thread_text(boxscore, teams) \
        if action == Action.DO_GAME_THREAD \
        else self._build_postgame_thread_text(boxscore, teams)
    self._create_or_update_game_thread(action, title, body)

  def _get_boxscore(self, game):
    game_start = game['startDateEastern']
    game_id = game['gameId']
    return nba_data.boxscore(game_start, game_id)

  def _get_current_game(self, schedule):
    """Returns the nba_data game object we want to focus on right now (or None)
    and an enum describing what we should do with it (create a game thread or
    post game thread or do nothing).

    This implementation searches for a game that looks like it might be on the
    same day. It relies heavily on NBA's lastStandardGamePlayedIndex field to
    tell us  where to start looking, rather than scanning the entire schedule.
    """
    last_played_idx = schedule['league']['lastStandardGamePlayedIndex']
    games = schedule['league']['standard']

    # Check the game after lastStandardGamePlayedIndex. If we are an hour before
    # tip-off or later and there's no score, then we want to make a game thread.
    if len(games) > last_played_idx + 1:
      game = games[last_played_idx + 1]
      gametime = dateutil.parser.parse(game['startTimeUTC'])
      has_score = bool(game['vTeam']['score'] + game['hTeam']['score'])
      if gametime - timedelta(hours=1) <= self.now and not has_score:
        return (Action.DO_GAME_THREAD, game)

    # If the previous game was finished 6 hours ago or less, then use that to
    # make a post game thread.
    game = games[last_played_idx]
    gametime = dateutil.parser.parse(game['startTimeUTC'])
    has_score = bool(game['vTeam']['score'] + game['hTeam']['score'])
    if gametime + timedelta(hours=6) >= self.now and has_score:
      return (Action.DO_POST_GAME_THREAD, game)

    return (Action.DO_NOTHING, None)

  def _build_game_thread_text(self, boxscore, teams):
    basicGameData = boxscore['basicGameData']

    if basicGameData['hTeam']['triCode'] == 'NYK':
      us = 'hTeam'
      them = 'vTeam'
      homeAwaySign = 'vs'
    else:
      us = 'vTeam'
      them = 'hTeam'
      homeAwaySign = '@'

    broadcasters = basicGameData['watch']['broadcast']['broadcasters']
    nationalBroadcaster = '-' if len(broadcasters['national']) == 0 \
        else broadcasters['national'][0]['longName']
    knicksBroadcaster = broadcasters[us][0]['longName']
    otherBroadcaster = broadcasters[them][0]['longName']

    knicksWinLossRecord = f"({basicGameData[us]['win']}-{basicGameData['hTeam']['loss']})"
    otherWinLossRecord = f"({basicGameData[them]['win']}-{basicGameData['vTeam']['loss']})"
    otherSubreddit = TEAM_SUB_MAP[teams[basicGameData[them]['teamId']]['nickname']]
    otherTeamName = teams[basicGameData[them]['teamId']]['fullName']
    otherTeamNickname = teams[basicGameData[them]['teamId']]['nickname']
    location = (f'{basicGameData["arena"]["city"]}, ' +
        f'{basicGameData["arena"]["stateAbbr"]} ' +
        f'{basicGameData["arena"]["country"]}')
    arena = basicGameData['arena']['name']

    start_time_utc = dateutil.parser.parse(basicGameData['startTimeUTC'])
    eastern = start_time_utc.astimezone(EASTERN_TIMEZONE).strftime('%I:%M %p')
    central = start_time_utc.astimezone(CENTRAL_TIMEZONE).strftime('%I:%M %p')
    mountain = start_time_utc.astimezone(MOUNTAIN_TIMEZONE).strftime('%I:%M %p')
    pacific = start_time_utc.astimezone(PACIFIC_TIMEZONE).strftime('%I:%M %p')

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

    dateTitle = self.now.astimezone(EASTERN_TIMEZONE).strftime('%B %d, %Y')
    title = (f'[Game Thread] The New York Knicks {knicksWinLossRecord} ' +
        f'{homeAwaySign} The {otherTeamName} {otherWinLossRecord} - ' +
        f'({dateTitle})')

    return (title, body)

  def _build_postgame_thread_text(self, boxscore, teams):
    # TODO: implement post game threads
    pass

  def _create_or_update_game_thread(self, act, title, body):
    thread = None

    q = '[Game Thread]' if act == Action.DO_GAME_THREAD else '[Post-Game Thread]'
    found = self.subreddit.search(q, sort='new', time_filter='day')
    for submission in found:
      if submission.author == 'nyknicks-automod':
        thread = submission
        break

    if thread == None:
      thread = self.subreddit.submit(title, selftext=body, send_replies=False)
      thread.mod.distinguish(how="yes")
      thread.mod.sticky()
      thread.mod.suggested_sort('new')
    else:
      if thread.selftext == body:
        logger.info('Game thread text did not change. Not updating.')
      thread.edit(body)


if __name__ == '__main__':
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
