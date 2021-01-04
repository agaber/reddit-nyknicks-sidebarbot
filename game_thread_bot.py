"""
A command line tool that manages game threads on the New York Knicks subreddit.

The tool is meant to be run as a cron job, but it also contains a reusable class
that can be used in other contexts (i.e., an AppEngine/GCE web server). The tool
will run once and then terminate. In many cases it will have nothing to do. To
run this on a continuous basis, try using crontab (see the README.md).
"""

from constants import CENTRAL_TIMEZONE, DEFEAT_SYNONYMS, EASTERN_TIMEZONE
from constants import GAME_THREAD_PREFIX, MOUNTAIN_TIMEZONE, PACIFIC_TIMEZONE
from constants import POST_GAME_PREFIX, TEAM_SUB_MAP, UTC, YAHOO_TEAM_CODES
from datetime import datetime, timedelta
from enum import Enum
from optparse import OptionParser
from services import nba_data

import dateutil.parser
import logging.config
import praw
import random
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
    if gametime + timedelta(hours=MAX_POST_AGE_HOURS) >= self.now and has_score:
      return Action.DO_POST_GAME_THREAD, game

    return Action.DO_NOTHING, None

  def _build_game_thread_text(self, boxscore, teams):
    """Builds the title and selftext for a game thread (not post game). This just
    builds strings and it doesn't actually interact with Reddit.

    This is heavily inspired by https://bit.ly/3hBwfmC.
    """
    basic_game_data = boxscore['basicGameData']
    hteam = basic_game_data['hTeam']
    vteam = basic_game_data['vTeam']

    if hteam['triCode'] == 'NYK':
      us = 'hTeam'
      them = 'vteam'
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

    knicks_record = f"({basic_game_data[us]['win']}-{hteam['loss']})"
    other_record = f"({basic_game_data[them]['win']}-{vteam['loss']})"
    other_subreddit = TEAM_SUB_MAP[teams[basic_game_data[them]['teamId']]['nickname']]
    other_team_name = teams[basic_game_data[them]['teamId']]['fullName']
    other_team_nickname = teams[basic_game_data[them]['teamId']]['nickname']
    location = self._build_location_string(basic_game_data)
    arena = basic_game_data['arena']['name']
    start_time_utc = dateutil.parser.parse(basic_game_data['startTimeUTC'])

    def time_str(timezone):
      return start_time_utc.astimezone(timezone).strftime('%I:%M %p')

    eastern = time_str(EASTERN_TIMEZONE)
    central = time_str(CENTRAL_TIMEZONE)
    mountain = time_str(MOUNTAIN_TIMEZONE)
    pacific = time_str(PACIFIC_TIMEZONE)

    urlpart = (
        f'{vteam["triCode"].lower()}-vs-{hteam["triCode"].lower()}-'
        f'{basic_game_data["gameId"]}')
    nba_pass_link = f'https://www.nba.com/game/{urlpart}?watch'
    preview_link = f'https://www.nba.com/game/{urlpart}'
    play_link = f'https://www.nba.com/game/{urlpart}/play-by-play'
    box_link = f'https://www.nba.com/game/{urlpart}/box-score#box-score'

    body = '##### General Information\n\n'
    body += '**TIME**|**BROADCAST**|**Media**|**Location and Subreddit**|\n'
    body += ':------------|:------------------------------------|:------------------------------------|:-------------------|\n'
    body += f'{eastern} Eastern   | National Broadcast: {national_broadcaster}           |[Game Preview]({preview_link})| {location}|\n'
    body += f'{central} Central   | Knicks Broadcast: {knicks_broadcaster}               |[Play By Play]({play_link})| {arena}|\n'
    body += f'{mountain} Mountain | {other_team_nickname} Broadcast: {other_broadcaster} |[Box Score]({box_link})| r/NYKnicks|\n'
    body += f'{pacific} Pacific   | [NBA League Pass]({nba_pass_link})                   || r/{other_subreddit}|\n'

    linescore = self._build_linescore(boxscore, teams)
    if linescore is not None:
      body += '\n##### Score\n\n'
      body += f'{linescore}\n'

    body += '\n-----\n\n'
    body += '[Reddit Stream](https://reddit-stream.com/comments/auto) '
    body += '(You must click this link from the comment page.)\n'

    title = (f'{GAME_THREAD_PREFIX} The New York Knicks {knicks_record} ' +
             f'{home_away_sign} The {other_team_name} {other_record} - ' +
             f'({self.now.astimezone(EASTERN_TIMEZONE).strftime("%B %d, %Y")})')

    return title, body

  @staticmethod
  def _build_location_string(basic_game_data):
    city = basic_game_data["arena"]["city"]
    state = basic_game_data["arena"]["stateAbbr"]
    location = f'{city}, {state}'
    country = basic_game_data["arena"]["country"]
    return location if country == 'USA' else f'{location} {country}'

  def _build_postgame_thread_text(self, boxscore, teams):
    title = self._build_postgame_title(boxscore, teams)
    body = self._build_boxscore_text(boxscore, teams)
    return title, body

  def _build_postgame_title(self, boxscore, teams):
    """Builds a title for the post game thread.

    Ported from https://bit.ly/3rOmvdd.
    """
    basic_game_data = boxscore['basicGameData']
    home_team = basic_game_data["hTeam"]
    road_team = basic_game_data["vTeam"]
    defeat = self._build_defeat_synonym(basic_game_data, teams)

    home_team_score = int(home_team["score"])
    road_team_score = int(road_team["score"])
    score = (f'{max(road_team_score, home_team_score)}-'
             f'{min(road_team_score, home_team_score)}')

    home_team_name = teams[home_team["teamId"]]['fullName']
    home_team_record = f'{home_team["win"]}-{home_team["loss"]}'
    road_team_name = teams[road_team["teamId"]]['fullName']
    road_team_record = f'{road_team["win"]}-{road_team["loss"]}'
    if home_team_score > road_team_score:
      winners = f'{home_team_name} ({home_team_record})'
      losers = f'{road_team_name} ({road_team_record})'
    else:
      losers = f'{home_team_name} ({home_team_record})'
      winners = f'{road_team_name} ({road_team_record})'

    quarters = len(basic_game_data['vTeam']['linescore'])
    maybe_overtime = ''
    if quarters == 5:
      maybe_overtime = ' in OT'
    elif quarters > 5:
      maybe_overtime = f' in {quarters - 4}OTs'

    title = f'The {winners} {defeat} the {losers}{maybe_overtime}, {score}'
    return f'{POST_GAME_PREFIX} {title}'

  @staticmethod
  def _build_defeat_synonym(basic_game_data, teams):
    """Says 'defeated' in creative and random ways.

    Ported from https://bit.ly/3o6QvPB."""

    home_team_name = teams[basic_game_data['hTeam']['teamId']]['fullName']
    if home_team_name == "knicks":
      us_score = int(basic_game_data["hTeam"]["score"])
      them_score = int(basic_game_data["vTeam"]["score"])
    else:
      us_score = int(basic_game_data["vTeam"]["score"])
      them_score = int(basic_game_data["hTeam"]["score"])

    if us_score > them_score:
      if them_score - us_score < 3:
        return random.choice(DEFEAT_SYNONYMS[14:16])
      elif them_score - us_score < 6:
        return random.choice(DEFEAT_SYNONYMS[16:])
      elif them_score - us_score > 20:
        return random.choice(DEFEAT_SYNONYMS[3:9])
      elif them_score - us_score > 40:
        return random.choice(DEFEAT_SYNONYMS[9:14])
      else:
        return random.choice(DEFEAT_SYNONYMS[:3])

    return random.choice(DEFEAT_SYNONYMS[:2])

  def _build_boxscore_text(self, boxscore, teams):
    """Builds up the post game selftext.

     Ported over from the Spurs bot (https://bit.ly/3n8HYdA).
    """

    basicGameData = boxscore["basicGameData"]

    # Header
    hTeamBasicData = basicGameData["hTeam"]
    hTeamFullName = teams[hTeamBasicData['teamId']]['fullName']
    hTeamLogo = TEAM_SUB_MAP[teams[basicGameData['hTeam']['teamId']]['nickname']]
    hTeamScore = hTeamBasicData["score"]
    vTeamBasicData = basicGameData["vTeam"]
    vTeamFullName = teams[vTeamBasicData['teamId']]['fullName']
    vTeamLogo = TEAM_SUB_MAP[teams[basicGameData['vTeam']['teamId']]['nickname']]
    vTeamScore = vTeamBasicData["score"]
    nbaUrl = (f'https://www.nba.com/game/{vTeamBasicData["triCode"]}-vs-'
              f'{hTeamBasicData["triCode"]}-{basicGameData["gameId"]}')
    yahooUrl = ('http://sports.yahoo.com/nba/'
                f'{vTeamFullName.lower().replace(" ", "-")}-'
                f'{hTeamFullName.lower().replace(" ", "-")}-'
                f'{basicGameData["startDateEastern"]}'
                f'{YAHOO_TEAM_CODES[hTeamBasicData["triCode"]]}')
    arena = basicGameData["arena"]["name"]
    attendance = basicGameData["attendance"]
    officials = ', '.join([o["firstNameLastName"] for o in basicGameData["officials"]["formatted"]])

    # Game summary
    body = f"""##### Game Summary

|||
|:--|:--|
|**Score**|[](/r/{vTeamLogo}) **{vTeamScore} -  {hTeamScore}** [](/r/{hTeamLogo})|
|**Box Score**|[NBA]({nbaUrl}), [Yahoo]({yahooUrl})|
|**Location**|{self._build_location_string(basicGameData)}|
|**Arena**|{arena}|
|**Attendance**|{attendance if attendance != '0' else 'No in-person attendance'}|
|**Officials**|{officials}|
"""

    # Line score
    body += '\n##### Line Score\n'
    body += f'\n{self._build_linescore(boxscore, teams)}\n'

    # Team stats
    allStats = boxscore["stats"]
    playerStats = allStats["activePlayers"]
    body += """
##### Team Stats

|**Team**|**PTS**|**FG**|**FG%**|**3P**|**3P%**|**FT**|**FT%**|**OREB**|**TREB**|**AST**|**PF**|**STL**|**TO**|**BLK**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
|{vTeamName}|{vpts}|{vfgm}-{vfga}|{vfgp}%|{vtpm}-{vtpa}|{vtpp}%|{vftm}-{vfta}|{vftp}%|{voreb}|{vtreb}|{vast}|{vpf}|{vstl}|{vto}|{vblk}|
|{hTeamName}|{hpts}|{hfgm}-{hfga}|{hfgp}%|{htpm}-{htpa}|{htpp}%|{hftm}-{hfta}|{hftp}%|{horeb}|{htreb}|{hast}|{hpf}|{hstl}|{hto}|{hblk}|

|**Team**|**Biggest Lead**|**Longest Run**|**PTS: In Paint**|**PTS: Off TOs**|**PTS: Fastbreak**|
|:--|:--|:--|:--|:--|:--|
|{vTeamName}|{vlead}|{vrun}|{vpaint}|{vpto}|{vfb}|
|{hTeamName}|{hlead}|{hrun}|{hpaint}|{hpto}|{hfb}|
  """.format(
      vTeamName=vTeamFullName,
      vpts=allStats["vTeam"]["totals"]["points"],
      vfgm=allStats["vTeam"]["totals"]["fgm"],
      vfga=allStats["vTeam"]["totals"]["fga"],
      vfgp=allStats["vTeam"]["totals"]["fgp"],
      vtpm=allStats["vTeam"]["totals"]["tpm"],
      vtpa=allStats["vTeam"]["totals"]["tpa"],
      vtpp=allStats["vTeam"]["totals"]["tpp"],
      vftm=allStats["vTeam"]["totals"]["ftm"],
      vfta=allStats["vTeam"]["totals"]["fta"],
      vftp=allStats["vTeam"]["totals"]["ftp"],
      voreb=allStats["vTeam"]["totals"]["offReb"],
      vtreb=allStats["vTeam"]["totals"]["totReb"],
      vast=allStats["vTeam"]["totals"]["assists"],
      vpf=allStats["vTeam"]["totals"]["pFouls"],
      vstl=allStats["vTeam"]["totals"]["steals"],
      vto=allStats["vTeam"]["totals"]["turnovers"],
      vblk=allStats["vTeam"]["totals"]["blocks"],
      hTeamName=hTeamFullName,
      hpts=allStats["hTeam"]["totals"]["points"],
      hfgm=allStats["hTeam"]["totals"]["fgm"],
      hfga=allStats["hTeam"]["totals"]["fga"],
      hfgp=allStats["hTeam"]["totals"]["fgp"],
      htpm=allStats["hTeam"]["totals"]["tpm"],
      htpa=allStats["hTeam"]["totals"]["tpa"],
      htpp=allStats["hTeam"]["totals"]["tpp"],
      hftm=allStats["hTeam"]["totals"]["ftm"],
      hfta=allStats["hTeam"]["totals"]["fta"],
      hftp=allStats["hTeam"]["totals"]["ftp"],
      horeb=allStats["hTeam"]["totals"]["offReb"],
      htreb=allStats["hTeam"]["totals"]["totReb"],
      hast=allStats["hTeam"]["totals"]["assists"],
      hpf=allStats["hTeam"]["totals"]["pFouls"],
      hstl=allStats["hTeam"]["totals"]["steals"],
      hto=allStats["hTeam"]["totals"]["turnovers"],
      hblk=allStats["hTeam"]["totals"]["blocks"],
      vlead=self._plusminus(allStats["vTeam"]["biggestLead"]),
      vrun=allStats["vTeam"]["longestRun"],
      vpaint=allStats["vTeam"]["pointsInPaint"],
      vpto=allStats["vTeam"]["pointsOffTurnovers"],
      vfb=allStats["vTeam"]["fastBreakPoints"],
      hlead=self._plusminus(allStats["hTeam"]["biggestLead"]),
      hrun=allStats["hTeam"]["longestRun"],
      hpaint=allStats["hTeam"]["pointsInPaint"],
      hpto=allStats["hTeam"]["pointsOffTurnovers"],
      hfb=allStats["hTeam"]["fastBreakPoints"]
    )

    body += """
##### Team Leaders

|**Team**|**Points**|**Rebounds**|**Assists**|
|:--|:--|:--|:--|
|{vTeam}|**{vpts}** {vply1}|**{vreb}** {vply2}|**{vast}** {vply3}|
|{hTeam}|**{hpts}** {hply1}|**{hreb}** {hply2}|**{hast}** {hply3}|
""".format(
      vTeam=vTeamFullName,
      vpts=allStats["vTeam"]["leaders"]["points"]["value"],
      vply1=allStats["vTeam"]["leaders"]["points"]["players"][0]["firstName"] + " " +
            allStats["vTeam"]["leaders"]["points"]["players"][0]["lastName"],
      vreb=allStats["vTeam"]["leaders"]["rebounds"]["value"],
      vply2=allStats["vTeam"]["leaders"]["rebounds"]["players"][0]["firstName"] + " " +
            allStats["vTeam"]["leaders"]["rebounds"]["players"][0]["lastName"],
      vast=allStats["vTeam"]["leaders"]["assists"]["value"],
      vply3=allStats["vTeam"]["leaders"]["assists"]["players"][0]["firstName"] + " " +
            allStats["vTeam"]["leaders"]["assists"]["players"][0]["lastName"],
      hTeam=hTeamFullName,
      hpts=allStats["hTeam"]["leaders"]["points"]["value"],
      hply1=allStats["hTeam"]["leaders"]["points"]["players"][0]["firstName"] + " " +
            allStats["hTeam"]["leaders"]["points"]["players"][0]["lastName"],
      hreb=allStats["hTeam"]["leaders"]["rebounds"]["value"],
      hply2=allStats["hTeam"]["leaders"]["rebounds"]["players"][0]["firstName"] + " " +
            allStats["hTeam"]["leaders"]["rebounds"]["players"][0]["lastName"],
      hast=allStats["hTeam"]["leaders"]["assists"]["value"],
      hply3=allStats["hTeam"]["leaders"]["assists"]["players"][0]["firstName"] + " " +
            allStats["hTeam"]["leaders"]["assists"]["players"][0]["lastName"]
    )

    body += """
##### Player Stats

**[](/{vTeamLogo}) {vTeamName}**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
""".format(
      vTeamLogo=vTeamBasicData["triCode"],
      vTeamName=vTeamFullName.rsplit(None, 1)[-1].upper()
    )

    # players stats are filled here, only starters have "pos" property (away team)
    for i in range(len(playerStats)):
      stats = playerStats[i]
      if stats["teamId"] == vTeamBasicData["teamId"] and stats["pos"] != "":
        body += "|{pname}^{pos}|{min}|{fgm}-{fga}|{tpm}-{tpa}|{ftm}-{fta}|{oreb}|{dreb}|{treb}|{ast}|{stl}|{blk}|{to}|{pf}|{pm}|{pts}|\n".format(
          pname=stats["firstName"] + " " + stats["lastName"],
          pos=stats["pos"],
          min=stats["min"],
          fgm=stats["fgm"],
          fga=stats["fga"],
          tpm=stats["tpm"],
          tpa=stats["tpa"],
          ftm=stats["ftm"],
          fta=stats["fta"],
          oreb=stats["offReb"],
          dreb=stats["defReb"],
          treb=stats["totReb"],
          ast=stats["assists"],
          stl=stats["steals"],
          blk=stats["blocks"],
          to=stats["turnovers"],
          pf=stats["pFouls"],
          pm=self._plusminus(stats["plusMinus"]),
          pts=stats["points"]
        )
      elif stats["teamId"] == vTeamBasicData["teamId"]:
        body += "|{pname}|{min}|{fgm}-{fga}|{tpm}-{tpa}|{ftm}-{fta}|{oreb}|{dreb}|{treb}|{ast}|{stl}|{blk}|{to}|{pf}|{pm}|{pts}|\n".format(
          pname=stats["firstName"] + " " + stats["lastName"],
          min=stats["min"],
          fgm=stats["fgm"],
          fga=stats["fga"],
          tpm=stats["tpm"],
          tpa=stats["tpa"],
          ftm=stats["ftm"],
          fta=stats["fta"],
          oreb=stats["offReb"],
          dreb=stats["defReb"],
          treb=stats["totReb"],
          ast=stats["assists"],
          stl=stats["steals"],
          blk=stats["blocks"],
          to=stats["turnovers"],
          pf=stats["pFouls"],
          pm=self._plusminus(stats["plusMinus"]),
          pts=stats["points"]
        )
    body += """\n**[](/{hTeamLogo}) {hTeamName}**|**MIN**|**FGM-A**|**3PM-A**|**FTM-A**|**ORB**|**DRB**|**REB**|**AST**|**STL**|**BLK**|**TO**|**PF**|**+/-**|**PTS**|
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
""".format(
      hTeamLogo=hTeamBasicData["triCode"],
      hTeamName=hTeamFullName.rsplit(None, 1)[-1].upper()
    )
    # home team players
    for i in range(len(playerStats)):
      stats = playerStats[i]
      if stats["teamId"] != vTeamBasicData["teamId"] and stats["pos"] != "":
        body += "|{pname}^{pos}|{min}|{fgm}-{fga}|{tpm}-{tpa}|{ftm}-{fta}|{oreb}|{dreb}|{treb}|{ast}|{stl}|{blk}|{to}|{pf}|{pm}|{pts}|\n".format(
          pname=stats["firstName"] + " " + stats["lastName"],
          pos=stats["pos"],
          min=stats["min"],
          fgm=stats["fgm"],
          fga=stats["fga"],
          tpm=stats["tpm"],
          tpa=stats["tpa"],
          ftm=stats["ftm"],
          fta=stats["fta"],
          oreb=stats["offReb"],
          dreb=stats["defReb"],
          treb=stats["totReb"],
          ast=stats["assists"],
          stl=stats["steals"],
          blk=stats["blocks"],
          to=stats["turnovers"],
          pf=stats["pFouls"],
          pm=self._plusminus(stats["plusMinus"]),
          pts=stats["points"]
        )
      elif playerStats[i]["teamId"] != vTeamBasicData["teamId"] and playerStats[i]["pos"] == "":
        body += "|{pname}|{min}|{fgm}-{fga}|{tpm}-{tpa}|{ftm}-{fta}|{oreb}|{dreb}|{treb}|{ast}|{stl}|{blk}|{to}|{pf}|{pm}|{pts}|\n".format(
          pname=stats["firstName"] + " " + stats["lastName"],
          min=stats["min"],
          fgm=stats["fgm"],
          fga=stats["fga"],
          tpm=stats["tpm"],
          tpa=stats["tpa"],
          ftm=stats["ftm"],
          fta=stats["fta"],
          oreb=stats["offReb"],
          dreb=stats["defReb"],
          treb=stats["totReb"],
          ast=stats["assists"],
          stl=stats["steals"],
          blk=stats["blocks"],
          to=stats["turnovers"],
          pf=stats["pFouls"],
          pm=self._plusminus(stats["plusMinus"]),
          pts=stats["points"]
        )
    return body

  def _build_linescore(self, boxscore, teams):
    """Builds a table of points scored in each quarter, including overtime.

    Will return None if there's no data, otherwise it will always print a table
    with at least 4 quarters even if some columns are blank."""

    basic_game_data = boxscore["basicGameData"]
    current_period = int(basic_game_data['period']['current'])

    home_team = basic_game_data["hTeam"]
    home_score = home_team["linescore"]
    home_team_name = teams[home_team['teamId']]['fullName']

    road_team = basic_game_data["vTeam"]
    road_score = road_team["linescore"]
    road_team_name = teams[road_team['teamId']]['fullName']

    assert len(home_score) == len(road_score)
    num_periods = len(home_score)
    if num_periods == 0:
      return None

    header1 = """|**Team**|"""
    header2 = '|:---|'
    home_team_line = f'|{home_team_name}|'
    road_team_line = f'|{road_team_name}|'
    for i in range(0, max(4, num_periods)):
      period = i + 1
      header1 += f'**Q{period}**|' if period < 5 else f'**OT{period - 4}**|'
      header2 += ':--:|'
      home_team_line += f'{self._points(home_score, current_period, period)}|'
      road_team_line += f'{self._points(road_score, current_period, period)}|'

    # Totals
    header1 += '**Total**|'
    header2 += ':--:|'
    home_team_line += f'{home_team["score"]}|'
    road_team_line += f'{road_team["score"]}|'

    return f'{header1}\n{header2}\n{road_team_line}\n{home_team_line}'

  @staticmethod
  def _plusminus(someStat):
    if someStat.isdigit() and int(someStat) > 0:
      return "+" + str(someStat)
    return str(someStat)

  @staticmethod
  def _points(linescore, current_period, requested_period):
    """Returns a string for the number of points in a quarter, or '-' if the
    quarter hasn't started yet.

    Parameters
    ----------
    linescore: object
      NBA data object for the linescore.
    current_period: int
      The period/quarter NBA says the game is currently in.
    requested_period: int
      The period the caller wants to display.
    """
    points = linescore[(requested_period - 1)]['score'] \
      if len(linescore) > requested_period - 1 else '-'
    # Display a hyphen for quarters that haven't started yet even though they
    # report it with a score of 0. Always display overtime data if present.
    if (points == '0'
            and requested_period > current_period
            and current_period <= 4):
      points = '-'
    return points

  def _create_or_update_game_thread(self, act, title, body):
    thread = None

    # Unfortunately subreddit.search sometimes lags by as much as 2-3 minutes.
    # This introduces a risk of spamming the sub with autogenerated posts because
    # this algorithm will create a new thread if doesn't find an already existing
    # one. Instead it's using subreddit.new() which seems to work better but does
    # does return a lot of extraneous results.
    q = GAME_THREAD_PREFIX if act == Action.DO_GAME_THREAD else POST_GAME_PREFIX
    for submission in self.subreddit.new(limit=50):
      # Need to make sure that we don't incorrectly update an old/obsolete post.
      created_utc = datetime.fromtimestamp(submission.created_utc, UTC)
      is_obsolete = created_utc + timedelta(hours=MAX_POST_AGE_HOURS) < self.now
      is_bot_post = submission.author == 'nyknicks-automod'
      if submission.title.startswith(q) and is_bot_post and not is_obsolete:
        thread = submission
        break

    if thread is None:
      thread = self.subreddit.submit(title, selftext=body, send_replies=False)
      thread.mod.distinguish(how="yes")
      thread.mod.sticky()
      thread.mod.suggested_sort('new')
      logger.info(f'Created a new thread with title "{thread.title}".')
    elif thread.selftext.strip() == body.strip():
      logger.info(f'Text of "{thread.title}" did not change. Not updating.')
    else:
      thread.edit(body)
      logger.info(f'Updated "{thread.title}".')


# Will ignore posts older than this many hours
MAX_POST_AGE_HOURS = 6


class Action(Enum):
  DO_GAME_THREAD = 1
  DO_POST_GAME_THREAD = 2
  DO_NOTHING = 3


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
