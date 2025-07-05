# How to Format bot_specs.json

Here's a sample specification of `bot_specs.json`
```json
{
    "Scarfy": {
        "team": -1,
        "stats": [10, 8, 5, 7, 9],
        "equipment": [2, -1, -1, -1],
        "boss": {
            "stats": [10, 10, 10, 10, 10],
            "equipment": [2, -1, -1, -1]
        }
    },
    "ras": {
        "team": 5,
        "stats": [8, 10, 8, 7, 10],
        "equipment": [13, 1, 20, -1],
        "boss": {
            "stats": [10, 10, 10, 10, 10],
            "equipment": [29, 1, 20, -1]
        }
    }
}
```
Here's what everything means:

### Naming
The *key* for each entry becomes the name, so the entry for `"Scarfy"` will become `BOT Scarfy` in game.

### Teams
The *team* corresponds to a different team. Here's the teams by ID number:

| Number | Faction |
| ------ | ------- |
| -1 | auto-assigned |
| 0 | ??? |
| 1 | ??? |
| 2 | Vigilantes |
| 3 | Desperados |
| 4 | Bandidos |
| 5 | Rangers |
| 6 | Zombies |

### Stats
The `stats` field houses the 5 stats you can change per bot, and are integer values from 0 (lowest) to 10 (highest). Each index corresponds to the following stats:
| Index | Stat | Variable |
| ----- | ---- | -------- |
| 0 | Awareness | bot_rotation_speed |
| 1 | Aim | bot_aim_trailing |
| 2 | Quickness | bot_strafe |
| 3 | Strafing | bot_shoot_delay |
| 4 | Aggression | bot_aggression |

***NOTE**: Look at Quickness and Strafing, they appear to be switched. I did this intentionally - if you generate a bot using the in-game AI editor the output of Quickness maps to bot_strafe and the output of Strafing maps to bot_shoot_delay. This is corrected in the code.*

So if you wanted a bot with 8 awareness, 2 aim, 4 quickness, 1 strafing, and 10 aggression, you would use `"stats": [8, 2, 4, 1, 10]`. Keep in mind that the code follows the stat names and not the variable names - the above example illustrates this, and applies the 1 strafing to `bot_strafe` and the 4 quickness to `bot_shoot_delay`.

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

If you wanted to give someone a loadout of Mare's Leg and Brass Knuckles, you would do `"equipment": [33, 34]` or `"equipment": [33, 34, -1, -1]`.

### Boss
**Bosses** are special bots that have different stats and a different loadout. Whenever bots are randomized, there is a variable chance of them becoming a boss (this can be controlled with the BOTS_BOSS_CHANCE variable in `configs/bot_randomizer.env`).

Everything under the "boss" subfield is applied in the event that a bot succeeds the boss roll.