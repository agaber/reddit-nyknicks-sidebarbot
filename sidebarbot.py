from constants import EASTERN_TIMEZONE, TEAM_SUB_MAP, UTC
from datetime import datetime, timedelta
from optparse import OptionParser
from services.nba_service import NbaService

import copy
import dateutil.parser
import logging.config
import praw
import sys
import traceback

def build_roster(nba_service, year):
  players = nba_service.players(year)
  roster = nba_service.roster('knicks', year)
  team_players = filter(lambda player: player['personId'] in roster, players)

  rows = []
  for player in team_players:
    name = f'{player["firstName"]} {player["lastName"]}'
    jersey = player['jersey']
    position = player['pos'].replace('-', '/') if player['pos'] else ''
    rows.append(f'{jersey}|{name}|{position}')

  # Sort players by first name.
  rows.sort(key = lambda r: r.split('|')[1])

  rows.insert(0, ':--:|:--|:--:')
  rows.insert(0, 'No.|Name|Position')
  return '\n'.join(rows)


def build_schedule(logger, nba_service, now, teams, year):
  today = now.astimezone(EASTERN_TIMEZONE).date()
  schedule = nba_service.schedule('knicks', year)

  logger.info('Building schedule text.')
  # FYI: We want to show to a show a total of 12 games: 
  #    most recent + 4 prior + 7 next.
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

    gametime = dateutil.parser \
        .parse(game['startTimeUTC']) \
        .astimezone(EASTERN_TIMEZONE)
    
    if gametime.date() == today:
      date = 'Today'
    elif gametime.date() == today - timedelta(days=1):
      date = 'Yesterday'
    elif gametime.date() == today + timedelta(days=1):
      date = 'Tomorrow'
    else:
      date = gametime.strftime('%b %d')

    time = gametime.strftime('%I:%M %p').lstrip('0')
    time_or_score = (time if knicks_score['score'] == ''
        else winloss(knicks_score, opp_score))

    row = ('%s|[](/r/%s)|%s|%s' %
        (date, opp_team_sub, 
            'Home' if is_home_team else 'Away', time_or_score))
    rows.append(row)
  return '\n'.join(rows)


def build_standings(standings, teams):
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


def build_tank_standings(standings, teams):
  s2 = copy.deepcopy(standings)
  rows = s2['conference']['east'] + s2['conference']['west']
  rows = sorted(rows, key=lambda team: float(team['lossPct']), reverse=True)
  worst_wins = int(rows[0]['win'])
  worst_loss = int(rows[0]['loss'])
  for row in rows:
     gb = (abs(worst_wins - int(row['win'])) + abs(worst_loss - int(row['loss']))) / 2
     row['gamesBehind'] = ('%.1f' % gb).replace('.0', '')
  return build_standings(rows[:10], teams)


def update_reddit_descr(descr, text, marker):
  start_marker = f'[](#Start{marker})'
  start = descr.find(start_marker)
  end_marker = f'[](#End{marker})'
  end = descr.find(end_marker)
  if start == -1 or end == -1:
    return descr
  new_text = f'{start_marker}\n\n{text}\n\n{end_marker}'
  return descr.replace(descr[start:end + len(end_marker)], new_text)


def winloss(knicks_score, opp_score):
  kscore = int(knicks_score['score'])
  oscore = int(opp_score['score'])
  return ('W %s-%s' % (kscore, oscore) 
      if kscore > oscore else 'L %s-%s' % (oscore, kscore))


def execute(logger, now, subreddit_name, user='nyknicks-automod'):
  """
    The main starting point (after command line args are parsed) that initiates
    all of the work this bot will do. It intereacts with reddit and the NBA Data
    APIs to build roster, schedule and standings strings and posts them to
    reddit.

    Parameters
    ----------
    logger : logging.Logger
    now : datetime
      The current time, preferably in UTC.
    subreddit_name : string
      The name of the subreddit to modify. The bot must have permissions to edit
      in this sub.
    user: str
      The Reddit account username for the bot to run as. This praw.ini config
      file should also have an entry for this username.
  """
  nba_service = NbaService(logger)

  current_year = nba_service.current_year()
  roster = build_roster(nba_service, current_year)
  teams = nba_service.teams(current_year)
  schedule = build_schedule(logger, nba_service, now, teams, current_year)

  logger.info('Building standings text.')
  nba_standings = nba_service.conference_standings()
  tank_standings = build_tank_standings(nba_standings, teams)
  east_standings = build_standings(nba_standings['conference']['east'], teams)
  west_standings = build_standings(nba_standings['conference']['west'], teams)

  logger.info('Logging in to reddit.')
  reddit = praw.Reddit(user)

  logger.info('Querying reddit settings.')
  subreddit = reddit.subreddit(subreddit_name)
  descr = subreddit.mod.settings()['description']
  updated_descr = update_reddit_descr(descr, schedule, 'Schedule')
  updated_descr = update_reddit_descr(updated_descr, tank_standings, 'TankStandings')
  updated_descr = update_reddit_descr(updated_descr, east_standings, 'EastStandings')
  updated_descr = update_reddit_descr(updated_descr, west_standings, 'WestStandings')
  updated_descr = update_reddit_descr(updated_descr, roster, 'Roster')

  if updated_descr != descr:
    logger.info('Updating reddit settings.')
    subreddit.mod.update(description=updated_descr)
  else:
    logger.info('No changes.')

  logger.info('All done.')


if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option(
      "-u",
      "--user",
      dest="username",
      help="Reddit account for the bot to run as.",
      metavar='[username]')
  (options, args) = parser.parse_args()

  logging.config.fileConfig('logging.conf')
  logger = logging.getLogger('sidebarbot')

  if len(args) != 1:
    logger.error(f'Invalid command line arguments: {args}')
    raise SystemExit(f'Usage: {sys.argv[0]} subreddit')

  subreddit_name = args[0]
  username = options.username if options.username else 'nyknicks-automod'
  logger.info(f'Using subreddit "{subreddit_name}" and user "{username}".')

  try:
    execute(logger, datetime.now(UTC), subreddit_name, username)
  except:
    logger.error(traceback.format_exc())
