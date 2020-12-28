# /r/nyknicks bots

A reddit bot that manages the [/r/nyknicks](https://www.reddit.com/r/NYKnicks/)
sidebar.

## Prerequisites
* [Set up your python environment](https://cloud.google.com/python/setup)

  On Mac, using [Homebrew](https://brew.sh/):

       $ brew upgrade
       $ brew install python3
       $ brew postinstall python3
       $ python3 -m pip install --upgrade pip

  The commands are similar on Linux with apt install.

* A praw.ini file (not submitted) with the following contents:

        [nyknicks-sidebarbot]
        client_id=(from reddit.com/prefs/apps)
        client_secret=(from reddit.com/prefs/apps)
        password=(mod password)
        username=(mod username)

## Running locally:

    $ pip install -r requirements.txt
    $ mkdir -p ~/.redditbot/logs
    $ python3 sidebarbot.py NYKnicks

## Unit tests

    $ python3 -m unittest discover -s ./ -p '*_test.py'

## NBA Data

\* Tip: Install [this](https://chrome.google.com/webstore/detail/json-viewer/gbmdgpbipfallnflgajpaliibnhdgobh/related?hl=en-US) JSON viewer Chrome Extension.

* Available APIs: http://data.nba.net/10s/prod/v1/today.json
* Other API info: https://github.com/kashav/nba.js/blob/master/docs/api/DATA.md