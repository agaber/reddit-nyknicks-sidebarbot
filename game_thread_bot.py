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
      has_score = bool(game['vTeam']['score']) or bool(game['hTeam']['score'])
      if gametime - timedelta(hours=1) <= self.now and not has_score:
        return Action.DO_GAME_THREAD, game

    # If the previous game was finished 6 hours ago or less, then use that to
    # make a post game thread.
    game = games[last_played_idx]
    gametime = dateutil.parser.parse(game['startTimeUTC'])
    has_score = bool(game['vTeam']['score'] + game['hTeam']['score'])
    if gametime + timedelta(hours=6) >= self.now and has_score:
      return Action.DO_POST_GAME_THREAD, game

    return Action.DO_NOTHING, None

  def _build_game_thread_text(self, boxscore, teams):
    """Builds the title and selftext for a game thread (not post game). This just
    builds strings and it doesn't actually interact with Reddit.

    This is heavily inspired by
    https://github.com/HokageEzio/KnicksGDT/blob/9f90e04e88047cb25d3bfd1c36fb08757b4ccea6/Knicks%20Bot.py#L132.
    """
    basic_game_data = boxscore['basicGameData']

    if basic_game_data['hTeam']['triCode'] == 'NYK':
      us = 'hTeam'
      them = 'vTeam'
      home_away_sign = 'vs'
    else:
      us = 'vTeam'
      them = 'hTeam'
      home_away_sign = '@'

    broadcasters = basic_game_data['watch']['broadcast']['broadcasters']
    national_broadcaster = 'N/A' if len(broadcasters['national']) == 0 \
        else broadcasters['national'][0]['longName']
    knicks_broadcaster = broadcasters[us][0]['longName']
    other_broadcaster = broadcasters[them][0]['longName']

    knicks_record = f"({basic_game_data[us]['win']}-{basic_game_data['hTeam']['loss']})"
    other_record = f"({basic_game_data[them]['win']}-{basic_game_data['vTeam']['loss']})"
    other_subreddit = TEAM_SUB_MAP[teams[basic_game_data[them]['teamId']]['nickname']]
    other_team_name = teams[basic_game_data[them]['teamId']]['fullName']
    other_team_nickname = teams[basic_game_data[them]['teamId']]['nickname']
    location = (f'{basic_game_data["arena"]["city"]}, ' +
        f'{basic_game_data["arena"]["stateAbbr"]} ' +
        basic_game_data["arena"]["country"])
    arena = basic_game_data['arena']['name']

    start_time_utc = dateutil.parser.parse(basic_game_data['startTimeUTC'])
    eastern = _time_str(start_time_utc, EASTERN_TIMEZONE)
    central = _time_str(start_time_utc, CENTRAL_TIMEZONE)
    mountain = _time_str(start_time_utc, MOUNTAIN_TIMEZONE)
    pacific = _time_str(start_time_utc, PACIFIC_TIMEZONE)

    body = f"""
##General Information
**TIME**|**BROADCAST**|**Location and Subreddit**|
:------------|:------------------------------------|:-------------------|
{eastern} Eastern   | National Broadcast: {national_broadcaster}           | {location}|
{central} Central   | Knicks Broadcast: {knicks_broadcaster}               | {arena}|
{mountain} Mountain | {other_team_nickname} Broadcast: {other_broadcaster} | r/NYKnicks|
{pacific} Pacific   |                                                      | r/{other_subreddit}|
-----
[Reddit Stream](https://reddit-stream.com/comments/auto) (You must click this link from the comment page.)
"""

    title = (f'[Game Thread] The New York Knicks {knicks_record} ' +
        f'{home_away_sign} The {other_team_name} {other_record} - ' +
        f'({self.now.astimezone(EASTERN_TIMEZONE).strftime("%B %d, %Y")})')

    return title, body

  def _build_postgame_thread_text(self, boxscore, teams):
    # TODO: implement post game threads
    pass

  def _create_or_update_game_thread(self, act, title, body):
    thread = None

    q = '[Game Thread]' if act == Action.DO_GAME_THREAD else '[Post-Game Thread]'
    for submission in self.subreddit.search(q, sort='new', time_filter='day'):
      if submission.author == 'nyknicks-automod':
        thread = submission
        break

    if thread is None:
      thread = self.subreddit.submit(title, selftext=body, send_replies=False)
      thread.mod.distinguish(how="yes")
      thread.mod.sticky()
      thread.mod.suggested_sort('new')
    elif thread.selftext == body:
      logger.info('Game thread text did not change. Not updating.')
    else:
      thread.edit(body)


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


def _time_str(time_utc, timezone):
  return time_utc.astimezone(timezone).strftime('%I:%M %p')


if __name__ == '__main__':
  parser = OptionParser()
  (options, args) = parser.parse_args()

  if len(args) != 1:
    logger.error(f'Invalid command line arguments: {args}')
    raise SystemExit(f'Usage: {sys.argv[0]} subreddit')

  subreddit_name = args[0]
  logger.info(f'Using subreddit: {subreddit_name}')

  try:
    # TODO: Make the username configurable too.
    bot = GameThreadBot(datetime.now(UTC), subreddit_name)
    bot.run()
  except:
    logger.error(traceback.format_exc())
