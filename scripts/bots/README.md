# Bots

The scripts in this folder pertain to the custom bots on my server - they're randomly selected each round and have a chance of becoming a "boss" variant. Here's what I use to accomplish this:

## Custom Bot Scripting

Fistful of Frags keeps scripts for custom bots under `fof/fof_scripts/bots`. Here, specifications for each bot's behavior and loadout are defined.

In order to enable custom bots on a server, you'll have to modify `fof/cfg/server.cfg` and look for/add the following cvars:
```
// 6 specifies that you'll be using a custom script for bots
fof_bot_skill 6

// This is relative to "fof/fof_scripts/bots"
// If you just place the script directly in the folder, you just need the file name.
fof_bot_scriptname path/to/script
```

Custom bot scripts can be easily made by spinning up a local server and hitting F4 - there you should be able to modify bot names, loadouts, and behavior. They will appear in the same `fof/fof_scripts/bots` folder as whatever you named it.

Here's a sample bot specification:
```
"BotList"
{
    "preset"
	{
		"bot_rotation_speed"		"9"
		"bot_shoot_delay"		"6"
		"bot_aim_trailing"		"7"
		"bot_strafe"		"8"
		"bot_force_team"		"-1"
		"bot_aggression"		"10"
		"bot_name"		"BOT tttg"
		"bot_equipment"		"28,1,-1,-1"
	}
}
```

Here's more of an explanation for what the different fields mean:

### Teams
The *team* is just an index that corresponds to a different team for the bot. Here are the possible values:

| Number | Faction |
| ------ | ------- |
| -1 | auto-assigned |
| 0 | Console? |
| 1 | Spectator? |
| 2 | Vigilantes |
| 3 | Desperados |
| 4 | Bandidos |
| 5 | Rangers |
| 6 | Zombies |

### Stats
There's 5 stats you can play with that modify the bot behavior. You can find these while using the AI editor, but they do not exactly correspond to the variables set in the output file. Here's a table showing which in-game description maps to which variable:

| Stat | Variable |
| ---- | -------- |
| Awareness | bot_rotation_speed |
| Aim | bot_aim_trailing |
| Quickness | bot_strafe |
| Strafing | bot_shoot_delay |
| Aggression | bot_aggression |

***NOTE**: Look at Quickness and Strafing, they appear to be switched. I did this intentionally - if you generate a bot using the in-game AI editor the output of Quickness maps to bot_strafe and the output of Strafing maps to bot_shoot_delay.*

An in-game "Skill Average" is computed by averaging all stats except aggression.

### Equipment

The loadout of any bot is defined by a list of numbers corresponding to weapons. Below is a table of these IDs:

| Number | Weapon |
| ------ | ------ |
| -1  | auto |
| 0 | ??? |
| 1 | Knife |
| 2 | Colt Navy |
| 3 | Deringer |
| 4 | Yellowboy |
| 5 | Smith Carbine |
| 6 | Coachgun |
| 7 | Dynamite |
| 8 | ??? |
| 9 | ??? |
| 10 | ??? |
| 11 | Bow |
| 12 | Sharps Rifle |
| 13 | Sawed-off Shotgun |
| 14 | Handgun Throw |
| 15 | Jumpmaster |
| 16 | Portable Whiskey |
| 17 | Dynamite Belt |
| 18 | Spencer Carbine |
| 19 | Hatchet |
| 20 | Boots |
| 21 | Peacemaker |
| 22 | Hammerless (x2) |
| 23 | Slide |
| 24 | Black Bow |
| 25 | Heavy Loads |
| 26 | Machete |
| 27 | Black Dynamite |
| 28 | Volcanic Pistol |
| 29 | Pump Shotgun |
| 30 | Remington Army |
| 31 | Schofield |
| 32 | Colt Walker |
| 33 | Mare's Leg |
| 34 | Brass Knuckles |

***Note**: Untested, but 8, 9, and 10 may be Left Handed/Ambidextrous/Fanning. Unclear whether or not the bots use these.*

## Specifying Custom Bots (for use with `botrandomizer.py`)

I use a json-based approach to specifying bots for my own sanity.
We'll compare a bot script to my own file and see what the differences are:
**Bot Script**
```
"BotList"
{
    "preset"
	{
		"bot_rotation_speed"		"9"
		"bot_shoot_delay"		"6"
		"bot_aim_trailing"		"7"
		"bot_strafe"		"8"
		"bot_force_team"		"-1"
		"bot_aggression"		"10"
		"bot_name"		"BOT tttg"
		"bot_equipment"		"28,1,-1,-1"
	}
}
```

**My JSON**
```json
{
    "tttg": {
        "team": -1,
        "stats": [9, 6, 7, 8, 10],
        "equipment": [28, 1, -1, -1],
        "boss": {
            "stats": [10, 10, 10, 10, 10],
            "equipment": [32, 28, -1, -1]
        }
    }
}
```

You'll see a couple things comparing these:
- The name of a bot is they key to the dictionary. My script automatically appends "BOT " to the front.
- The *stats* are condensed into an array with the following correspondence: `[bot_rotation_speed, bot_shoot_delay, bot_aim_trailing, bot_strafe, bot_aggression]`.
- Equipment is now an array rather than a string.
- Team is the same.
- The "boss" subdictionary is a redefinition of the stats and equipment, to be used when a bot is selected to be a boss.

The specifications for the bots I use on my server can be found in [bot_specs.json](/data/bot-specs/bot_specs.json) - this is probably a good starting point.

## Bot Shuffling
If you specify too many custom bots, you'll notice only the first few show up every round, and the other ones never seem to get loaded in.

This is where `botrandomizer.py` comes in. It reads in the JSON file with your bot specifications and generate a new bot script that shuffles around the ordering of the bots - this way, you can get a different random assortment of bots whenever you run the script.

You can run the script with the following command:
```
python -m scripts.bots.botrandomizer
```

The script has a few [config parameters](/configs/bot_randomizer.yml) that you can use to change the behavior of the bot shuffling - things like forcing all the bots to be on one team or adjusting the boss chance, as well as **specifying paths for your input JSON and your output script.**

## Automated Bot Shuffling
Realistically you'll probably just want to run the script every 15 minutes or so to make sure the bots are shuffled when the map changes, but if you're using my python code for running the server then this can be done for you.

`autoshuffler.py` implements the FofClient, connecting to the existing server and listens for events indicating a map change, shuffling the bots when it receives a message.

This can be run similarly with the following command:
```
python -m scripts.bots.autoshuffler
```
I'd recommend running this in a screen instance so that it stays open in the background.