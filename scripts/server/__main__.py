import os
import asyncio

import yaml
from dotenv import load_dotenv

from scripts.server.fof_server_wrapper import FofServerWrapper
from scripts.server.fof_server_event_handler import FofServerEventHandler

with open("configs/server-wrapper.yml", "r") as fp:
    config = yaml.safe_load(fp)
load_dotenv("configs/server-wrapper.env")

local_host = config.get("fof_local_host", "127.0.0.1")
local_port = config.get("fof_local_port", "9000")

starting_map = config.get("starting_map", "fof_fistful")
max_players = str(config.get("max_players", "20"))
server_port = str(config.get("server_port", "27015"))

launch_cmd = [
    './srcds_run',
    '-game', 'fof',
    '+map', starting_map,
    '+maxplayers', max_players,
    '-debug',
    '-port', server_port
]

fof_server = FofServerWrapper(
    launch_cmd=launch_cmd,
    debug=True
)

event_handler = FofServerEventHandler(
    fof_server,
    host=local_host,
    port=local_port,
    debug=True
)

asyncio.run(event_handler.start())