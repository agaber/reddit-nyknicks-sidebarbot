from datetime import datetime, timedelta
from pytz import timezone
from time import sleep

import dateutil.parser
import json
import logging
import logging.config
import praw
import pytz
import re
import requests

EASTERN_TIMEZONE = timezone('US/Eastern')
UTC = timezone('UTC')
SUBREDDIT_NAME = 'nyknicks'
# SUBREDDIT_NAME = 'knicklejerk'

TEAM_SUB_MAP = {
  '76ers': 'sixers',
  'Bucks': 'MkeBucks',
  'Bulls': 'chicagobulls',
  'Cavaliers': 'clevelandcavs',
  'Celtics': 'bostonceltics',
  'Clippers': 'LAClippers',
  'Grizzlies': 'memphisgrizzlies',
  'Hawks': 'AtlantaHawks',
  'Heat': 'heat',
  'Hornets': 'CharlotteHornets',
  'Jazz': 'UtahJazz',
  'Kings': 'kings',
  'Knicks': 'NYKnicks',
  'Lakers': 'lakers',
  'Magic': 'OrlandoMagic',
  'Mavericks': 'mavericks',
  'Nets': 'GoNets',
  'Nuggets': 'denvernuggets',
  'Pacers': 'pacers',
  'Pelicans': 'NOLAPelicans',
  'Pistons': 'DetroitPistons',
  'Raptors': 'torontoraptors',
  'Rockets': 'rockets',
  'Spurs': 'NBASpurs',
  'Suns': 'suns',
  'Thunder': 'thunder',
  'Timberwolves': 'timberwolves',
  'Trail Blazers': 'ripcity',
  'Warriors': 'warriors',
  'Wizards': 'washingtonwizards',
}

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('sidebarbot')

def build_schedule(teams):
  schedule = request_schedule()

  logger.info('Building schedule text.')
  # FYI: We want to show to a show a total of 12 games: most recent + 4 prior + 7 next.
  # Get the array index of the last game played.
  last_played_idx = schedule['league']['lastStandardGamePlayedIndex']

  # Get the next 7 games.
  end_idx = min(last_played_idx + 7, len(schedule['league']['standard']))

  # Show the previous 4 games or more if we're at the end of the season.
  start_idx = max(0, last_played_idx - (4 + (7 - (end_idx - last_played_idx - 1))))

  rows = ['Date|Team|Loc|Time/Outcome', ':--:|:--:|:--:|:--:']
  for i in range(start_idx, end_idx):
    game = schedule['league']['standard'][i]
    is_home_team = game['isHomeTeam']
    knicks_score = game['hTeam' if is_home_team else 'vTeam']
    opp_score = game['vTeam' if is_home_team else 'hTeam']
    opp_team_name = teams[opp_score['teamId']]['nickname']
    opp_team_sub = TEAM_SUB_MAP[opp_team_name]

    gametime = dateutil.parser.parse(game['startTimeUTC'])
    today = datetime.now(UTC).date()
    if gametime.date() == today:
      date = 'Today'
    elif gametime.date() == today - timedelta(days=1):
      date = 'Yesterday'
    elif gametime.date() == today + timedelta(days=1):
      date = 'Tomorrow'
    else:
      date = gametime.astimezone(EASTERN_TIMEZONE).strftime('%b %d')

    time = gametime.strftime('%I:%M %p').lstrip('0')
    time_or_score = (time if knicks_score['score'] == ''
        else winloss(knicks_score, opp_score))

    row = ('%s|[](/r/%s)|%s|%s' %
        (date, opp_team_sub, 'Home' if is_home_team else 'Away', time_or_score))
    rows.append(row)
  return '\n'.join(rows)

def build_standings(teams):
  standings = request_conf_standings()
  logger.info('Building standings text.')
  division = standings['league']['standard']['conference']['east']
  return print_standings(teams, division)

def build_tank_standings(teams):
  standings = request_conf_standings()
  logger.info('Building tank standings text.')
  rows = standings['league']['standard']['conference']['east']
  rows = rows + standings['league']['standard']['conference']['west']
  rows = sorted(rows, key=lambda team: float(team['lossPct']), reverse=True)
  worst_wins = int(rows[0]['win'])
  worst_loss = int(rows[0]['loss'])
  for row in rows:
     gb = (abs(worst_wins - int(row['win'])) + abs(worst_loss - int(row['loss']))) / 2
     row['gamesBehind'] = ('%.1f' % gb).replace('.0', '')
  return print_standings(teams, rows[:10])

def print_standings(teams, standings):
  rows = [' | | |Record|GB', ':--:|:--:|:--|:--:|:--:']
  for i, d in enumerate(standings):
    team = teams[d['teamId']]['nickname']
    teamsub = TEAM_SUB_MAP[team]
    wins = d['win']
    loses = d['loss']
    games_behind = d['gamesBehind']
    games_behind = '-' if games_behind == '0' else games_behind
    row = ('%s|[](/r/%s)|%s|%s-%s|%s' %
        (i + 1, teamsub, team, wins, loses, games_behind))
    rows.append(row)
  return '\n'.join(rows)

def request_conf_standings():
  logger.info('Fetching conference standings.')
  r = requests.get(
      'http://data.nba.net/10s/prod/v1/current/standings_conference.json')
  r.raise_for_status()
  return json.loads(r.content.decode('utf-8'))

def request_schedule():
  logger.info('Fetching schedule information.')
  r = requests.get(
      'http://data.nba.net/data/10s/prod/v1/2018/teams/knicks/schedule.json')
  r.raise_for_status()
  return json.loads(r.content.decode('utf-8'))

def request_teams():
  logger.info('Fetching team data.')
  r = requests.get('http://data.nba.net/10s/prod/v1/2018/teams.json')
  r.raise_for_status()
  teams = json.loads(r.content.decode('utf-8'))
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

def execute():
  logger.info('Logging in to reddit.')
  reddit = praw.Reddit('nyknicks-sidebarbot', user_agent='python-praw')

  teams = request_teams()
  schedule = build_schedule(teams)
  standings = build_standings(teams)
  # standings = build_tank_standings(teams)
  subreddit = reddit.subreddit(SUBREDDIT_NAME)

  logger.info('Querying reddit settings.')
  descr = subreddit.mod.settings()['description']

  updated_descr = update_reddit_descr(
      descr, schedule, '[](#StartSchedule)', '[](#EndSchedule)')
  updated_descr = update_reddit_descr(
      updated_descr, standings, '[](#StartStandings)', '[](#EndStandings)')
  if updated_descr != descr:
    logger.info('Updating reddit settings.')
    subreddit.mod.update(description=updated_descr)
  else:
    logger.info('No changes.')

  logger.info('All done.')

if __name__ == "__main__":
  execute()
