import json
from random import random, shuffle, randint
from time import sleep

STATS = ["bot_rotation_speed", "bot_shoot_delay", 
            "bot_aim_trailing", "bot_strafe", 
            "bot_aggression"]

KEY_ORDER = ["bot_rotation_speed", "bot_shoot_delay",
                "bot_aim_trailing", "bot_strafe",
                "bot_force_team", "bot_aggression",
                "bot_name", "bot_equipment"]

def shuffle_bots(data_file, output_file, boss_chance=0.05, same_team=False, same_team_no=-1):
    with open(data_file, "r") as fp:
        data = json.load(fp)

    namelist = list(data.keys())
    shuffle(namelist)

    full_str = '"BotList"\n{'
    for name in namelist:
        full_str += '\tpreset\n\t{\n\t'
        boss = random() < boss_chance

        stat_idx = 0
        for key in KEY_ORDER:
            if key == "bot_force_team": val = str(same_team_no) if same_team else str(data[name]["team"])
            elif key == "bot_name": val = "BOT " + name + (" (Boss)" if boss else "")
            elif key == "bot_equipment": val = ",".join(str(x) for x in (data[name]["boss"]["equipment"] if boss else data[name]["equipment"]))
            else: 
                val = str((data[name]["boss"]["stats"] if boss else data[name]["stats"])[stat_idx])
                stat_idx += 1

            full_str += '\t"' + key + '"\t\t"' + val + '"\n\t'

        full_str += '}\n'

    full_str += '}'

    with open(output_file, "w") as fp:
        fp.write(full_str)

if __name__ == "__main__":
    import yaml

    with open("configs/bot_randomizer.yml", "r") as fp:
        config = yaml.safe_load(fp)

    boss_chance: float = config.get("bots_boss_chance", 0.05)
    same_team: bool = config.get("bots_same_team", False)
    same_team_no: int = config.get("bots_same_team_no", 3)

    bot_data_file: str = config.get("bots_data_file", "data/bot-specs/bot_specs.json")
    output_bot_script: str = config.get("bots_output_script", "fof/fof_scripts/bots/generated.txt")

    shuffle_bots(bot_data_file, output_bot_script, boss_chance, same_team, same_team_no)