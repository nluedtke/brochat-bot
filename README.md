# brochat-bot
A bot to enable friendship (and at times enforce it).

### Requires:
  - discord.py
  - asyncio
  - twython

### Installation (How to get your own brochat-bot)
Below are instructions to set up and run your own brochat-bot.

  1) Get the source code by either cloning this repo or downloading the 
  latest stable release at [Releases](../../releases/latest).
  2) Acquire a tokens.config file from the developers or create your own
   tokens. Currently brochat-bot uses tokens from Twitter, Twilio, and 
   Discord. This file should be placed in the same directory to which 
   you installed main.py.
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
docker run -d --restart=always --name <NAME OF CONTAINER> <NAME OF
IMAGE>
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