# /r/nyknicks bots

Reddit bots that automate various things for 
[/r/nyknicks](https://www.reddit.com/r/NYKnicks/).

## Running locally

#### Prerequisites

* [Set up your python environment](https://cloud.google.com/python/setup)

  On Mac, using [Homebrew](https://brew.sh/):

       $ brew upgrade
       $ brew install python3
       $ brew postinstall python3
       $ python3 -m pip install --upgrade pip

  The commands are similar on Linux with apt install.

* Add a praw.ini file (not submitted) with the following contents:

        [nyknicks-automod]
        client_id=(from reddit.com/prefs/apps)
        client_secret=(from reddit.com/prefs/apps)
        password=(mod password)
        username=nyknicks-automod
        user_agent=python-praw

* Add dependencies and log directory:

        $ pip install -r requirements.txt    
        $ mkdir -p ~/.redditbot/logs
    
#### Running it manually

    $ python3 sidebarbot.py NYKnicks
    $ python3 game_thread_bot.py NYKnicks

#### Unit tests

    $ python3 -m unittest discover -s ./ -p '*_test.py'

#### Running it automatically with crontab

These bots are meant to be run from a command line terminal. They do something
once and then terminate. They are [cron jobs](https://en.wikipedia.org/wiki/Cron), 
not [daemons](https://en.wikipedia.org/wiki/Daemon_(computing)) like a lot of
other bots; meaning they don't stay running forever in an infinite loop. So to 
make these programs consistently update Reddit, I use crontabs on Linux:

    $ crontab -e
    * * * * * cd /home/me/src/redditbots && python3 sidebarbot.py NYKnicks
    * * * * * cd /home/me/src/redditbots && python3 game_thread_bot.py NYKnicks

Crontab should also work on Mac and with Windows Task Scheduler on Microsoft 
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

## Known issues

* This is using an outdated version of praw because the newer version
(praw=7.1.0) doesn't seem to correctly update the sidebar. See 
https://github.com/praw-dev/praw/issues/1613.

## Contributing code changes

#### Prerequisites

You need to install git and have some familiarity with executing
commands from a terminal.

#### Instructions

Just in general, to edit stuff on github there are 4 steps (there are other ways
but this is one way I know how to do it):

1. Fork

   Go [here](https://github.com/agaber/reddit-nyknicks-sidebarbot) and click
   "Fork" near the top left:
   
   ![Fork](https://i.imgur.com/TvuVRKp.png) 
   
1. Clone

   Click Clone and copy the URL. 
   
   ![Clone](https://i.imgur.com/taHxmrx.png)
   
   On your computer, open a command line terminal and run these commands:
   
       $ mkdir src
       $ cd src
       $ git clone [url you copied]
       $ cd reddit-nyknicks-sidebarbot
        
1. Branch

    Create a new branch (give it a descriptive name).
    
       $ git checkout -b my_cool_change

1. Commit and push

    Make some edits and then commit.
    
        $ git add -A .
        $ git commit
    
    Enter a helpful description of your change. The first line should be a brief
    high-level summary (it will be displayed in a bunch of places) but feel free
    to add more paragraphs with useful information.
    
    Then push
    
        $ git push
    
    This will probably fail on the first try but it will tell you what to do in
    the error message. It will be something like this:
    
        $ git push --set-upstream origin test_branch
    
1. Create a pull request

    Go back to your forked repo on github. Click into the "Pull requests" tab and
    then click "New pull request".
    
    ![Pull request](https://i.imgur.com/IIJ9twX.png)
    
    After that select the options for merging your change into the original and
    click "Create pull request".
    
    Your change will either be accepted or you will get some kind of feedback.
    
#### Requirements

1. Please, please, please make sure the unit tests still work with your new change
(instructions for running tests are above) and please add new tests for new logic
that you're adding.

2. Please try to stick with two space indentation with white space
(no tab chars).
