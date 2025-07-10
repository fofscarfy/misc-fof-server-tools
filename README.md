# Scarfy's Fof Server Tools

Hi! Hope you can find some use out of my janky server tools. Here's what's in this repo.

***NOTE**: This repo is meant to be just above your `fof` directory. While the standalone scripts still work, and there are config files where you can change file paths, it is recommended to place it so that `fof` is a subdirectory of the repo root.*
***NOTE**: There is a requirements.txt file. That is all.*

# Bot Randomizer
You can specify a set of bots to pull from, optionally turning them into boss bots. See [scripts/bots](scripts/bots/README.md) for more information.

You can [configure the parameters for bot randomization](configs/bot_randomizer.yml) and run the bot randomization with the following command:

```bash
python -m scripts.bots.botrandomizer
```


# Chest and Whiskey Randomizer
You can override the default placement of whiskey and chests, moving them to random locations. The number of chests/whiskey bottles and how far apart they're spread [can be configured](configs/remixer.yml), and randomization can be run with the following command:

```bash
python -m scripts.chest_whiskey_randomizer.remixer <map_name>
# To randomize chests on fistful, run the following
python scripts.chest_whiskey_randomizer.remixer fof_fistful
```

***NOTE** All available maps have [templates in the data folder](data/map-prop-templates/chest-whiskey-templates), so if you want to use any maps that aren't there you'll have to make templates yourself (I'd appreciate if you shared them!)*


# Log Parsing
I threw together [a ton of regular expression patterns](scripts/log_parsing/fof_regex.py) for scraping data from logs. I doubt this is a complete set to match everything but it at least matches every log file I've ever generated. More info in the [log_parsing directory](scripts/log_parsing).


# Python Plugins
I run my server out of a python script so that I can parse the log and run python scripts based off of them in real time. You can find more information on these in the [server](scripts/server) and [client](scripts/client) folders. The client is used to implement all of the plugins, while the server launches the actual Fistful of Frags server and handles the connections to running plugins.


# Category Randomization
My server's nominate list has category headers as well as filler maps. I [made a plugin](scripts/map_category_redirect/) that will choose randomly from a category if the headers or fillers are selected.


# Discord Verification
I use a [simple discord bot](scripts/discord_bot) that connects discord IDs to steam IDs. Admittedly I'm not too sure what the plan was, but seems like a good base for doing any discord integrations with the server. 