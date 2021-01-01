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

EASTERN_TIMEZONE = timezone('US/Eastern')
UTC = timezone('UTC')

logging.config.fileConfig("logging.conf")


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


class GameThreadBot:
  _logger = logging.getLogger("gdtbot")

  def __init__(self, now: datetime, subreddit_name: str):
    self.now = now
    self.reddit = praw.Reddit('nyknicks-automod')
    self.subreddit_name = subreddit_name

  def run(self):
    game = self._get_current_game()
    action = self._get_action(game)
    
    if action == Action.DO_NOTHING:
      _logger.info('Nothing to do. Bye.')
      return

    boxscore = _get_boxscore(game)
    title, body = _build_thread_text(action, boxscore, game)
    _create_or_update_game_thread(title, body)

  def _get_boxscore(self, game):
    game_start = game['startDateEastern']
    game_id = game['gameId']
    return nba_data.boxscore(game_start, game_id)
    
  def _get_current_game(self):
    """Returns the nba_data game object we want to focus on right now.
    This implementation searches for a game that looks like it might be on the
    same day (within X number of hours because technically night games can spill
    over into the next day). This solution won't work for double-headers.

    This implementation also relies heavily on NBA's lastStandardGamePlayedIndex
    field to tell us where to start looking, rather than scanning the entire
    schedule."""

    season_year = nba_data.current_year()
    schedule = nba_data.schedule('knicks', season_year)
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

    # If the next game starts in an hour or was over less than 6 hours ago, then
    # use that (it doesn't really make sense for the next game to be over but 
    # handle that situation just in case).
    next_game = games[last_played_idx + 1]
    next_gametime = dateutil.parser.parse(next_game['startTimeUTC'])
    if next_gametime - timedelta(hours=1) <= self.now:
      return next_game
    elif next_gametime + timedelta(hours=6) >= self.now:
      return next_game

  def _get_action(self, game):
    gametime = dateutil.parser.parse(game['startTimeUTC'])
    has_score = bool(game['vTeam']['score'] + game['hTeam']['score'])
    if gametime - timedelta(hours=1) <= self.now and not has_score:
      return Action.DO_GAME_THREAD
    elif gametime + timedelta(hours=6) >= self.now and has_score:
      return Action.DO_POST_GAME_THREAD
    else:
      return Action.DO_NOTHING

  def _build_thread_text(self, action, boxscore, game):
    basicGameData = boxscore['basicGameData']

    timeEasternRaw = basicGameData["startTimeEastern"]
    timeOnlyEastern = timeEasternRaw[:5]
    if timeOnlyEastern[:2].isdigit():
      timeEasternHour = int(timeOnlyEastern[:2])
      timeMinute = timeOnlyEastern[3:]
    else:
      timeEasternHour = int(timeOnlyEastern[:1])
      timeMinute = timeOnlyEastern[2:]
    timeCentralHourFinal = timeEasternHour - 1
    timeMountainHourFinal = timeCentralHourFinal - 1

    broadcasters = basicGameData['watch']['broadcast']['broadcasters']
    if broadcasters['national']==[]:
      nationalBroadcaster = "-"
    else:
      nationalBroadcaster = broadcasters['national'][0]['shortName']

    if basicGameData['hTeam']['triCode'] == "NYK":
      us = 'hTeam'
      them = 'vTeam'
      homeAwaySign = "vs"
    else:
      us = 'vTeam'
      them = 'hTeam'
      homeAwaySign = "@"

    knicksBroadcaster = broadcasters[us][0]['shortName']
    otherBroadcaster = broadcasters[them][0]['shortName']
    otherSubreddit = TEAM_DICT[basicGameData[them]["triCode"]][3]
    knicksWinLossRecord = f"({basicGameData[us]['win']}-{basicGameData['hTeam']['loss']})"
    otherWinLossRecord = f"({basicGameData[them]['win']}-{basicGameData['vTeam']['loss']})"
    otherTeamName = TEAM_DICT[basicGameData[them]["triCode"]][0]
    
    dateTitle = self.now.astimezone(EASTERN_TIMEZONE).strftime("%B %d, %Y")
    title = f'[Game Thread] The New York Knicks {knicksWinLossRecord} '
        + f'{homeAwaySign} The {otherTeamName} {otherWinLossRecord} - '
        + f'({dateTitle})'
    return (title, body)

  def _create_or_update_game_thread(title, body):
    pass


TEAM_DICT = {
    "ATL": [
        "Atlanta Hawks",
        "01",
        "atlanta-hawks-",
        "/r/AtlantaHawks",
        "1610612737",
        "Hawks",
    ],
    "BKN": [
        "Brooklyn Nets",
        "17",
        "brooklyn-nets-",
        "/r/GoNets",
        "1610612751",
        "Nets",
    ],
    "BOS": [
        "Boston Celtics",
        "02",
        "boston-celtics-",
        "/r/bostonceltics",
        "1610612738",
        "Celtics",
    ],
    "CHA": [
        "Charlotte Hornets",
        "30",
        "charlotte-hornets-",
        "/r/charlottehornets",
        "1610612766",
        "Hornets",
    ],
    "CHI": [
        "Chicago Bulls",
        "04",
        "chicago-bulls-",
        "/r/chicagobulls",
        "1610612741",
        "Bulls",
    ],
    "CLE": [
        "Cleveland Cavaliers",
        "05",
        "cleveland-cavaliers-",
        "/r/clevelandcavs",
        "1610612739",
        "Cavaliers",
    ],
    "DAL": [
        "Dallas Mavericks",
        "06",
        "dallas-mavericks-",
        "/r/mavericks",
        "1610612742",
        "Mavericks",
    ],
    "DEN": [
        "Denver Nuggets",
        "07",
        "denver-nuggets-",
        "/r/denvernuggets",
        "1610612743",
        "Nuggets",
    ],
    "DET": [
        "Detroit Pistons",
        "08",
        "detroit-pistons-",
        "/r/DetroitPistons",
        "1610612765",
        "Pistons",
    ],
    "GSW": [
        "Golden State Warriors",
        "09",
        "golden-state-warriors-",
        "/r/warriors",
        "1610612744",
        "Warriors",
    ],
    "HOU": [
        "Houston Rockets",
        "10",
        "houston-rockets-",
        "/r/rockets",
        "1610612745",
        "Rockets",
    ],
    "IND": [
        "Indiana Pacers",
        "11",
        "indiana-pacers-",
        "/r/pacers",
        "1610612754",
        "Pacers",
    ],
    "LAC": [
        "Los Angeles Clippers",
        "12",
        "los-angeles-clippers-",
        "/r/LAClippers",
        "1610612746",
        "Clippers",
    ],
    "LAL": [
        "Los Angeles Lakers",
        "13",
        "los-angeles-lakers-",
        "/r/lakers",
        "1610612747",
        "Lakers",
    ],
    "MEM": [
        "Memphis Grizzlies",
        "29",
        "memphis-grizzlies-",
        "/r/memphisgrizzlies",
        "1610612763",
        "Grizzlies",
    ],
    "MIA": [
        "Miami Heat",
        "14",
        "miami-heat-",
        "/r/heat",
        "1610612748",
        "Heat",
    ],
    "MIL": [
        "Milwaukee Bucks",
        "15",
        "milwaukee-bucks-",
        "/r/MkeBucks",
        "1610612749",
        "Bucks",
    ],
    "MIN": [
        "Minnesota Timberwolves",
        "16",
        "minnesota-timberwolves-",
        "/r/timberwolves",
        "1610612750",
        "Timberwolves",
    ],
    "NOP": [
        "New Orleans Pelicans",
        "03",
        "new-orleans-pelicans-",
        "/r/NOLAPelicans",
        "1610612740",
        "Pelicans",
    ],
    "NYK": [
        "New York Knicks",
        "18",
        "new-york-knicks-",
        "/r/NYKnicks",
        "1610612752",
        "Knicks",
    ],
    "OKC": [
        "Oklahoma City Thunder",
        "25",
        "oklahoma-city-thunder-",
        "/r/thunder",
        "1610612760",
        "Thunder",
    ],
    "ORL": [
        "Orlando Magic",
        "19",
        "orlando-magic-",
        "/r/OrlandoMagic",
        "1610612753",
        "Magic",
    ],
    "PHI": [
        "Philadelphia 76ers",
        "20",
        "philadelphia-76ers-",
        "/r/sixers",
        "1610612755",
        "76ers",
    ],
    "PHX": [
        "Phoenix Suns",
        "21",
        "phoenix-suns-",
        "/r/suns",
        "1610612756",
        "Suns",
    ],
    "POR": [
        "Portland Trail Blazers",
        "22",
        "portland-trail-blazers-",
        "/r/ripcity",
        "1610612757",
        "Trail Blazers",
    ],
    "SAC": [
        "Sacramento Kings",
        "23",
        "sacramento-kings-",
        "/r/kings",
        "1610612758",
        "Kings",
    ],
    "SAS": [
        "San Antonio Spurs",
        "24",
        "san-antonio-spurs-",
        "/r/NBASpurs",
        "1610612759",
        "Spurs",
    ],
    "TOR": [
        "Toronto Raptors",
        "28",
        "toronto-raptors-",
        "/r/torontoraptors",
        "1610612761",
        "Raptors",
    ],
    "UTA": [
        "Utah Jazz",
        "26",
        "utah-jazz-",
        "/r/UtahJazz",
        "1610612762",
        "Jazz",
    ],
    "WAS": [
        "Washington Wizards",
        "27",
        "washington-wizards-",
        "/r/washingtonwizards",
        "1610612764, ",
        "Wizards",
    ],
    "ADL": [
        "Adelaide 36ers",
        "00",
        "adelaide-36ers",
        "/r/nba",
        "15019",
    ],
    "SLA": [
        "Buenos Aires San Lorenzo",
        "00",
        "buenos-aires-san-lorenzo",
        "/r/nba",
        "12330",
    ],
    "FRA": [
        "Franca Franca",
        "00",
        "franca-franca",
        "/r/nba",
        "12332",
    ],
    "GUA": [
        "Guangzhou Long-Lions",
        "00",
        "guangzhou-long-lions",
        "/r/nba",
        "15018",
    ],
    "MAC": [
        "Haifa Maccabi Haifa",
        "00",
        "haifa-maccabi-haifa",
        "/r/nba",
        "93",
    ],
    "MEL": [
        "Melbourne United",
        "00",
        "melbourne-united",
        "/r/nba",
        "15016",
    ],
    "NZB": [
        "New Zealand Breakers",
        "00",
        "new-zealand-breakers",
        "/r/nba",
        "15020",
    ],
    "SDS": [
        "Shanghai Sharks",
        "00",
        "shanghai-sharks",
        "/r/nba",
        "12329",
    ]
}
   
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
  
