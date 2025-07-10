import os
import asyncio

from scripts.client.fofclient import FofClient
from scripts.bots.botrandomizer import shuffle_bots

class BotGenerator:
    def __init__(self, data_file=None, output_file=None, boss_chance=None, same_team=None, same_team_no=None):
        self.data_file = data_file if data_file is not None else os.environ.get("BOTS_DATA_FILE", None)
        self.output_file = output_file if output_file is not None else os.environ.get("BOTS_OUTPUT_SCRIPT", None)
        self.boss_chance = boss_chance if boss_chance is not None else float(os.environ.get("BOTS_BOSS_CHANCE", 0.05))
        self.same_team = same_team if same_team is not None else bool(int(os.environ.get("BOTS_SAME_TEAM", True)))
        self.same_team_no = same_team_no if same_team_no is not None else int(os.environ.get("BOTS_SAME_TEAM_NO", 3))

    async def start(self, config_file=None):
        self.fofclient = FofClient()
        self.config_file = config_file

        @self.fofclient.on_event("on_mapchange")
        async def randomize(message_data):
            print("Map Changing! Shuffling bots.")
            shuffle_bots(self.data_file, self.output_file, self.boss_chance, self.same_team, self.same_team_no)


        async def register_on_connect(client):
            await client.register_event("on_mapchange", startswith="-------- Mapchange to ", exclude='say')

        self.fofclient.on_connect(register_on_connect)
        await self.fofclient.run()

if __name__ == "__main__":
    import yaml
    with open("configs/bot_randomizer.yml", "r") as fp:
        config = yaml.safe_load(fp)

    boss_chance: float = config.get("bots_boss_chance", 0.05)
    same_team: bool = config.get("bots_same_team", False)
    same_team_no: int = config.get("bots_same_team_no", 3)

    bot_data_file: str = config.get("bots_data_file", "data/bot-specs/bot_specs.json")
    output_bot_script: str = config.get("bots_output_script", "fof/fof_scripts/bots/generated.txt")

    from dotenv import load_dotenv
    load_dotenv("configs/bot_randomizer.env")

    async def main():
        generator = BotGenerator(
                        bot_data_file, 
                        output_bot_script, 
                        boss_chance, 
                        same_team, 
                        same_team_no)
    
        await generator.start()

    asyncio.run(main())
