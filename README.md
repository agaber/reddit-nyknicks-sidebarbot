# /r/nyknicks bots

A reddit bot that manages the [/r/nyknicks](https://www.reddit.com/r/NYKnicks/)
sidebar.

## Prerequisites

* [Set up your python environment](https://cloud.google.com/python/setup)

* Use Python3 (virtualenv --python python3 env)

* [Install gcloud tools](https://cloud.google.com/sdk/)

## Not submitted but this requires a praw.ini file with the following contents:

    [nyknicks-sidebarbot]
    client_id=(from reddit.com/prefs/apps)
    client_secret=(from reddit.com/prefs/apps)
    password=(mod password)
    username=(mod username)

## Running locally:

    $ pip install --user --upgrade virtualenv
    $ cd your/project
    $ virtualenv --python python3 env
    $ pip install -r requirements.txt
    $ python main.py # http://localhost:8080/healthz should print ok.
    $ deactivate     # to end virtualenv

## Deploy to appengine

    $ gcloud app deploy [--no-promote] [--version=]
    $ gcloud app deploy cron.yaml
