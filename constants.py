from pytz import timezone

EASTERN_TIMEZONE = timezone('US/Eastern')
CENTRAL_TIMEZONE = timezone('US/Central')
MOUNTAIN_TIMEZONE = timezone('US/Mountain')
PACIFIC_TIMEZONE = timezone('US/Pacific')
UTC = timezone('UTC')

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

GAME_THREAD_PREFIX = '[Game Thread]'
POST_GAME_PREFIX = '[Post Game Thread]'

DEFEAT_SYNONYMS = [
  'defeat',
  'beat',
  'triumph over',
  'blow out',
  'level out',
  'destroy',
  'crush',
  'walk all over',
  'exterminate',
  'slaughter',
  'massacre'
  'obliterate',
  'eviscerate',
  'annihilate',
  'edge out',
  'steal one against',
  'hang on to defeat',
  'snap',
]

YAHOO_TEAM_CODES = {
  'ATL': '01',
  'BKN': '17',
  'BOS': '02',
  'CHA': '30',
  'CHI': '04',
  'CLE': '05',
  'DAL': '06',
  'DEN': '07',
  'DET': '08',
  'GSW': '09',
  'HOU': '10',
  'IND': '11',
  'LAC': '12',
  'LAL': '13',
  'MEM': '29',
  'MIA': '14',
  'MIL': '15',
  'MIN': '16',
  'NOP': '03',
  'NYK': '18',
  'OKC': '25',
  'ORL': '19',
  'PHI': '20',
  'PHX': '21',
  'POR': '22',
  'SAC': '23',
  'SAS': '24',
  'TOR': '28',
  'UTA': '26',
  'WAS': '27',
}
