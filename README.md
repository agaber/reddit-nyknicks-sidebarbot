# /r/nyknicks bots

A reddit bot that manages the [/r/nyknicks](https://www.reddit.com/r/NYKnicks/)
sidebar.

## Prerequisites
* [Set up your python environment](https://cloud.google.com/python/setup)
* Use Python3 (virtualenv --python python3 env)
* [Install gcloud tools (deprecated)](https://cloud.google.com/sdk/)
* A praw.ini file (not submitted) with the following contents:

        [nyknicks-sidebarbot]
        client_id=(from reddit.com/prefs/apps)
        client_secret=(from reddit.com/prefs/apps)
        password=(mod password)
        username=(mod username)

On Mac, using [Homebrew](https://brew.sh/)

     $ brew upgrade
     $ brew install python3
     $ brew postinstall python3
     $ python3 -m pip install --upgrade pip

The commands are similar on linux with apt install.

## Running locally:

    $ pip install -r requirements.txt
    $ python3 sidebarbot.py

## Running a local server for AppEngine with virtualenv (deprecated):

    $ pip install --user --upgrade virtualenv
    $ cd your/project
    $ virtualenv --python python3 env
    $ source env/bin/activate
    $ pip install -r requirements.txt
    $ python main.py # http://localhost:8080/healthz should print ok.
    $ deactivate     # to end virtualenv

## Deploy to AppEngine (deprecated):

    $ gcloud app deploy [--no-promote] [--version=]
    $ gcloud app deploy cron.yaml

## NBA Data

\* Tip: Install [this](https://chrome.google.com/webstore/detail/json-viewer/gbmdgpbipfallnflgajpaliibnhdgobh/related?hl=en-US) JSON viewer chrome extension.

* Available APIs: http://data.nba.net/10s/prod/v1/today.json
* Players: http://data.nba.net/prod/v1/2020/players.json
* Other API info: https://github.com/kashav/nba.js/blob/master/docs/api/DATA.md

Do not submit:
http://data.nba.net/10s/prod/v1/2020/teams/knicks/roster.json