# /r/nyknicks bots

A reddit bot that manages the [/r/nyknicks](https://www.reddit.com/r/NYKnicks/)
sidebar.

To run on Linux:

    $ sudo apt update
    $ sudo apt install python python-dev python3 python3-dev pip
    $ pip install --upgrade virtualenv
    $ cd your/project
    $ virtualenv --python python3 env
    $ source env/bin/activate
    $ gcloud app deploy cron.yaml
    $ gcloud app deploy [--no-promote] [--version=]
    $ deactivate # to end virtualenv

You also have to install gcloud. I don't remember how I did it. 

Not submitted but this requires a praw.ini file with the following contents:

    [nyknicks-sidebarbot]
    client_id=(from reddit.com/prefs/apps)
    client_secret=(from reddit.com/prefs/apps)
    password=(mod password)
    username=(mod username)
