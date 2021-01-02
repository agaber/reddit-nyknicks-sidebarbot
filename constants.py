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
