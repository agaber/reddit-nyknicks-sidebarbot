from dateutil import tz
from time import sleep

import dateutil.parser
import getpass
import json
import logging
import logging.config
import praw
import re
import requests
import sys

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('sidebarbot')

EASTERN_TIMEZONE = tz.gettz('America/New_York')
# SUBREDDIT_NAME = 'knicklejerk'
SUBREDDIT_NAME = 'nyknicks'

def build_schedule(teams):
  schedule = request_schedule()

  logger.info('Building schedule text.')
  # FYI: We want to show to a show a total of 12 games: last + 4 prior + 7 next.
  # Get the array index of the last game played.
  last_played_idx = schedule['league']['lastStandardGamePlayedIndex']
  # Get the next 7 games.
  end_idx = min(last_played_idx + 7, len(schedule['league']['standard']))
  # Show the previous 4 games or more if we're at the end of the season.
  start_idx = max(0, last_played_idx - (4 + (end_idx - last_played_idx) % 7))

  rows = ['Date|Team|Loc|Time/Outcome', ':--|:--:|:--|:--']
  for i in range(start_idx, end_idx):
    game = schedule['league']['standard'][i]
    d = dateutil.parser.parse(game['startTimeUTC']).astimezone(EASTERN_TIMEZONE)
    date = d.strftime('%b %d') 
    time = d.strftime('%I:%M %p').lstrip('0')
    is_home_team = game['isHomeTeam']
    knicks_score = game['hTeam' if is_home_team else 'vTeam']
    opp_score = game['vTeam' if is_home_team else 'hTeam']
    opp_team_name = teams[opp_score['teamId']]['nickname']
    time_or_score = (time if knicks_score['score'] == '' 
        else winloss(knicks_score, opp_score))
    row = ('%s | [](/#%s) | %s | %s' % 
        (date, opp_team_name, 'Home' if is_home_team else 'Away', time_or_score))
    rows.append(row)
  return '\n'.join(rows)

def build_standings(teams):
  standings = request_division_standings()
  logger.info('Building standings text.')
  division = standings['league']['standard']['conference']['east']['atlantic']
  rows = ['Team|W|L|Conf. Rank', ':--:|:--:|:--:|:--:']
  for d in division:
    team = teams[d['teamId']]['nickname']
    wins = d['win']
    loses = d['loss']
    conf_rank = d['confRank']
    row = '[](/#%s) | %s | %s | %s' % (team, wins, loses, conf_rank)
    rows.append(row)
  return '\n'.join(rows)

def request_division_standings():
  logger.info('Fetching division standings.')
  req = requests.get(
      'http://data.nba.net/10s/prod/v1/current/standings_division.json')
  sleep(.5)
  if not req.status_code == 200:
    raise Exception('Standings request failed with status %s' % req.status_code)
  return json.loads(req.content)

def request_schedule():
  logger.info('Fetching schedule information.')
  req = requests.get(
      'http://data.nba.net/data/10s/prod/v1/2017/teams/knicks/schedule.json')
  sleep(.5)
  if not req.status_code == 200:
    raise Exception('Schedule request failed with status %s' % req.status_code)
  return json.loads(req.content)

def request_teams():
  logger.info('Fetching team data.')
  req = requests.get('http://data.nba.net/10s/prod/v1/2017/teams.json')
  sleep(.5)
  if not req.status_code == 200:
    raise Exception('Teams request failed with status %s' % req.status_code)
  teams = json.loads(req.content)
  teams_map = dict()
  for team in teams['league']['standard']:
    teams_map[team['teamId']] = team
  return teams_map

def update_reddit_descr(descr, text, start_marker, end_marker):
  start, end = (descr.index(start_marker),
      descr.index(end_marker) + len(end_marker))
  return descr.replace(
      descr[start:end], 
      start_marker + '\n\n' + text + '\n\n' + end_marker)

def winloss(knicks_score, opp_score):
  kscore = int(knicks_score['score'])
  oscore = int(opp_score['score'])
  return 'Win' if kscore > oscore else 'Loss'

if __name__ == "__main__":
  password = getpass.getpass(prompt='Enter reddit password: ')
  client_secret = raw_input(
      'Enter client secret (It\'s here: https://www.reddit.com/prefs/apps/): ')

  logger.info('Logging in to reddit.')
  reddit = praw.Reddit(
      client_id='wJgBsaHZJ42LBg',
      client_secret=client_secret,
      password=password,
      user_agent='python-praw',
      username='macdoogles')

  while True:
    try:
      teams = request_teams()
      schedule = build_schedule(teams)
      standings = build_standings(teams)
      subreddit = reddit.subreddit(SUBREDDIT_NAME)

      logger.info('Querying reddit settings.')
      descr = subreddit.mod.settings()['description']

      logger.info('Updating reddit settings.')
      updated_descr = update_reddit_descr(
          descr, schedule, '[](#StartSchedule)', '[](#EndSchedule)')
      updated_descr = update_reddit_descr(
          updated_descr, standings, '[](#StartStandings)', '[](#EndStandings)')
      if updated_descr != descr:
        logger.info('Updating reddit settings.')
        subreddit.mod.update(description=updated_descr)  
      else:
        logger.info('No changes.')

      logger.info('All done. Sleeping for one hour.')
      # Stupid way to sleep for a long time without breaking ctrl+c.
      # https://stackoverflow.com/questions/5114292/break-interrupt-a-time-sleep-in-python
      for i in range(20):
        sleep(60)
    except KeyboardInterrupt:
      logger.info('Goodbye.')
      sys.exit(0)
    except Exception as ex:
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(ex).__name__, ex.args)
      logger.error(message)
      logger.info('Will resume shortly...')
      sleep(60)
