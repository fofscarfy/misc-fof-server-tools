import os
import asyncio
from random import choices
import json

from scripts.client import FofClient

class MapSelector:
    '''
    Handles when people pick category names or _ as the map
    '''
    def __init__(self, nomlist, rotlist, local_addr="127.0.0.1", local_port=9000, debug=False):
        '''
        nomlist: the nominate list (could be the same as the rotation list)
        rotlist: the standard rotation list
        '''
        self.nomlist = nomlist
        self.rotlist = rotlist
        self.debug = debug
        if not self.nomlist: print("Error - no nominate list!")

        with open(self.rotlist, "r") as fp:
            self.rotation_maps = [x.strip() for x in fp if x.strip()]

        with open(self.nomlist, "r") as fp:
            data = [x.strip() for x in fp if x.strip()]

        self.nextmap = ""

        key = ""
        self.maps = {}
        for item in data:
            if item == item.upper():
                if item == key or item == "_": continue
                self.maps[item] = []
                key = item
            else:
                self.maps[key].append(item)

        print(f"Maps:\n{json.dumps(self.maps, indent=4)}")

        self.fofclient = FofClient(host=local_addr, port=local_port, debug=debug)

    async def start(self):
        @self.fofclient.on_event("on_mapchange_fast")
        async def pick_map(message_data):
            choice = message_data["data"].split(" ")[2].replace('"', '').strip()
            if self.debug:
                print(f"Here's the choice: {choice}")
            if choice in self.maps or choice == "_":
                if self.debug:
                    print("Randomized choice selected!")
                nextmap = choices(self.rotation_maps if choice == "_" else self.maps[choice], k=1)[0]
                await self.fofclient.command(f"changelevel {nextmap}")

        # @self.fofclient.on_event("on_votefinish")
        # async def pick_map(message_data):
        #     choice = message_data["data"].split(" ")[8][:-1]
        #     if self.debug:
        #         print(f"Here's the choice: {choice}")
        #     if choice in self.maps or choice.split(".")[0] == "_":
        #         if choice.split(".")[0] == "_":
        #             self.nextmap = choices(self.rotation_maps, k=1)[0]
        #         else:
        #             self.nextmap = choices(self.maps[choice], k=1)[0]
        #         print(f"Received category vote! Chose {self.nextmap}!")
        #         await self.fofclient.register_event("on_mapchange", startswith='[META] Loaded 0 plugins (1 already loaded)', exclude='say')

        # @self.fofclient.on_event("on_mapchange")
        # async def rtv_pickmap(message_data):
        #     await self.fofclient.unregister_event("on_mapchange")
        #     if self.nextmap:
        #         await asyncio.sleep(1)
        #         print(f"Changing map to {self.nextmap}!")
        #         await self.fofclient.command(f"changelevel {self.nextmap}")
        #         self.nextmap = ""

        async def on_connect(client):
            await client.register_event("on_mapchange_fast", startswith='Loading map "')

        self.fofclient.on_connect(on_connect)
        await self.fofclient.run()

if __name__ == "__main__":
    async def main():
        import yaml
        config = {}
        with open("configs/maplists.yml", "r") as fp:
            config.update(yaml.safe_load(fp))
        with open("configs/server-wrapper.yml", "r") as fp:
            config.update(yaml.safe_load(fp))

        nomlist = config.get("nominate_maplist_file", "fof/maplists/team_shootout_nominate_list.txt")
        rotlist = config.get("rotation_maplist_file", "fof/mapcycle.txt")

        local_addr = config.get("fof_local_host", "127.0.0.1")
        local_port = config.get("fof_local_port", 9000)

        selector = MapSelector(nomlist, rotlist, local_addr, local_port, debug=True)
        await selector.start()

    asyncio.run(main())