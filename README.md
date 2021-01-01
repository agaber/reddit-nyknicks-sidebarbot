# /r/nyknicks bots

Reddit bots that automate various things for 
[/r/nyknicks](https://www.reddit.com/r/NYKnicks/).

## Prerequisites

* [Set up your python environment](https://cloud.google.com/python/setup)

  On Mac, using [Homebrew](https://brew.sh/):

       $ brew upgrade
       $ brew install python3
       $ brew postinstall python3
       $ python3 -m pip install --upgrade pip

  The commands are similar on Linux with apt install.

* A praw.ini file (not submitted) with the following contents:

        [nyknicks-automod]
        client_id=(from reddit.com/prefs/apps)
        client_secret=(from reddit.com/prefs/apps)
        password=(mod password)
        username=nyknicks-automod
        user_agent=python-praw

## Running locally:

    $ pip install -r requirements.txt
    $ mkdir -p ~/.redditbot/logs
    $ python3 sidebarbot.py NYKnicks
    $ python3 game_thread_bot.py NYKnicks

## Unit tests

    $ python3 -m unittest discover -s ./ -p '*_test.py'

## Crontab

These bots are meant to be run from a command line terminal. They do something
once and then terminate. They are [cron jobs](https://en.wikipedia.org/wiki/Cron), 
not [daemons](https://en.wikipedia.org/wiki/Daemon_(computing) like a lot of
other bots; meaning they don't stay running forever in an infinite loop. So to 
make these programs consistently update Reddit, I use crontabs on Linux:

    $ crontab -e
    * * * * * cd /home/me/src/redditbots && python3 sidebarbot.py NYKnicks
    * * * * * cd /home/me/src/redditbots && python3 game_thread_bot.py NYKnicks

Crontab should also work on Mac and with Windows Task Scheduer on Microsoft 
Windows but I've never tried those things myself.

As an aside, I have a Windows PC at home, but I run an Ubuntu Server using 
[VirtualBox](https://www.virtualbox.org/) which is how I run these jobs. I used
to use AppEngine but as soon as my free trial ran out I realized that was way too
expensive to justify.

## NBA Data

\* Tip: Install [this](https://chrome.google.com/webstore/detail/json-viewer/gbmdgpbipfallnflgajpaliibnhdgobh/related?hl=en-US) JSON viewer Chrome Extension.

* Available APIs: http://data.nba.net/10s/prod/v1/today.json
* Other API info: https://github.com/kashav/nba.js/blob/master/docs/api/DATA.md

## Reddit PRAW

* https://praw.readthedocs.io/en/latest/
* https://github.com/praw-dev
* https://www.reddit.com/r/redditdev/

## Known Issues

* This is using an outdated version of praw because the newer version
(praw=7.1.0) doesn't seem to correctly update the sidebar. See 
https://github.com/praw-dev/praw/issues/1613.