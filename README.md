# brochat-bot
A Discord bot to enable friendship (and at times enforce it).

[![Build Status](https://travis-ci.org/nluedtke/brochat-bot.svg?branch=master)](https://travis-ci.org/nluedtke/brochat-bot.svg?branch=master)

List of commands (!help):
````
A bot to enforce friendship.

DrinkBank:
  drankbank    See your *assets and liabilities* with the bank of drank
  drink        Log a drink taken
  shot-lottery Runs a shot-lottery
Duels:
  duel         Duel someone
  accept       Accept a challenge
  unequip      Unequips an item in use
  use          Use an item
Gametime:
  vote         Vote in a poll
  gametime     Handles gametime actions
  in           Marks you as in for a gametime
  late         Marks you as going to be late for a gametime
  out          Removes you from a gametime
  poll         Handles Polls actions
  possible     Marks you as possible for a gametime
  clear-record Clears the session record.
  draw         Add a draw to the record books
  get-record   Get the current record.
  loss         Add a loss to the record books
  win          Add a win to the record books
  whosin       See who is in for a gametime
Puby:
  getmap       Gets the Map of your last PUBG Match
Reddit:
  bertstrip    Ruin your childhood
  dankmeme     Get a succulent dank may-may
Texting:
  text         Get a fool in the loop
Twitter:
  news         Grab a news story
  trump        Get Trump's latest Yuge success!
​No Category:
  help         Shows this message.
  seen         Get last seen time for a player
  battletag    Get your battletag to share!
  set          Add some info to the db about you
  clear        Clears Bot chat history
  summary      Gets a summary of a url
  me           Tell me about myself

Type !help command for more info on a command.
You can also type !help category for more info on a category.
````
### Requires:
  - discord.py
  - asyncio
  - twython
  - pubg-python

### Installation (How to get your own brochat-bot)
Below are instructions to set up and run your own brochat-bot.

  1) Get the source code by either cloning this repo or downloading the 
  latest stable release at [Releases](../../releases/latest).
  2) Create a tokens.config file using the tokens.config.example file as
   a template. Currently brochat-bot uses tokens from Summary, Twitter,
   Twilio, and Discord. However, as of v3.3.0 only the Discord token is
   required. This file should be placed in the same directory to which you
   installed main.py. Alternatively, you can place the Discord token in
   the $DISCORD_BOT_TOKEN environment variable on the host if that's the
   only token you wish to use. Use of just the Discord token will
   disable some functionality.
  3) Run main.py. This will set up a blank database (a lightweight json 
   file) to hold the persistent database.
  4) If the tokens are set up correctly a brochat-bot should appear.
  Type !help to get a list of commands that brochat-bot can handle.

#### Docker Container
With docker running in the top level git dir:
```
docker build -t <NAME OF IMAGE> .
```
will build the container
```
docker run -d -v <host directory with db and config>:/data --restart=always --name <NAME OF CONTAINER> <NAME OF IMAGE>
```
will run the container

### Development (How to help)
Currently development is done on the master branch and stable releases 
are released and deployed through tags. This will change as the code 
base becomes larger which will require us to lock the master branch and 
allow new code only through pull requests. 
#### Style
All code should follow the usual best coding practices attempting to 
adhere to Python Standards where able. Below are points of emphasis to 
insure the code is usable, readable, and sound nature.
  
  - Wrap Lines at 80 chars
  - Use header blocks to define functions including all parameters, 
  return variables, and return types
  - Code should be written for Python3 (ie be careful with Python2 
  strings)
  - Try/Catch blocks should be tailored to catch specific errors and 
  not 'catchalls'
  - Comment code that isn't immediately understandable
  - Comment all input/output code with at least basic information
  - Avoid dropping into shells as much as possible
  - Code should be able to released on the current license
  - Individual commits do not have to be signed. Stable releases/tags 
  **should be** signed.
#### Bug Reporting and Feature Requests
All bug reporting and requests for features should be done on the 
[issues](../../issues/) page.
