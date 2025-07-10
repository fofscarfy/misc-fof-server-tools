import os
import asyncio

from scripts.client import FofClient
from scripts.chest_whiskey_randomizer.remixer import FofRemixer

class FofAutoRemixer:
    def __init__(self, templates_folder, output_folder):
        self.remixer = FofRemixer()
        self.templates_folder = templates_folder
        self.output_folder = output_folder

    async def start(self):
        self.fofclient = FofClient()

        @self.fofclient.on_event("on_mapchange")
        async def randomize(message_data):
            template_name = os.path.join(self.templates_folder, message_data["data"].split(" ")[3] + "-shootout-template.ai")
            print(f"Looking for template at {template_name}")
            if os.path.exists(template_name):
                print("Shuffling chest and whiskey locations!")
                script_name = os.path.join(self.output_folder, message_data["data"].split(" ")[3] + "-shootout.ai")
                self.remixer.import_ai_script(template_name)
                self.remixer.create_randomized_locations()
                self.remixer.export_to_script(script_name)

        async def on_connect(client):
           await client.register_event("on_mapchange", startswith='-------- Mapchange to ', exclude='say')

        self.fofclient.on_connect(on_connect)
        await self.fofclient.run()

if __name__ == "__main__":

    async def main():
        import yaml
        CONFIG_FILE = "configs/remixer.yml"
        
        with open(CONFIG_FILE, "r") as fp:
            config = yaml.safe_load(fp)

        templates_folder = config.get("templates_folder", "data/map-prop-templates/chest-whiskey-templates")
        output_folder = config.get("output_folder", "fof/fof_scripts/ai_editor")

        auto_remixer = FofAutoRemixer(templates_folder, output_folder)
        await auto_remixer.start()

    asyncio.run(main())
