# Scarfy's Fof Server Tools

Hi! Hope you can find some use out of my janky server tools. Here's what's in this repo.

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
