import asyncio
import os
import sys
import signal
import json

from scripts.server.fof_server_wrapper import FofServerWrapper
from scripts.server.event_engine import EventEngine
from scripts.server.data_store import DataStore
from scripts.server.protocol import FofServerProtocol

class FofServerEventHandler:
    def __init__(self, fof_server, host, port, debug=False):
        self.server = fof_server
        self.event_engine = EventEngine(debug=debug)
        self.data_store = DataStore()
        self.protocol = FofServerProtocol(self.event_engine, self.data_store, self.server, debug=debug)
        self.host = host
        self.port = port
        self.debug = debug
        self.stop_event = None

    async def start(self):
        await self.server.start()
        self.server_proc = await asyncio.start_server(self.protocol.handle_client, self.host, self.port)
        print(f"[EventHandler listening on {self.host}:{self.port}]")

        log_task = asyncio.create_task(self.dispatch_log_events())
        cli_task = asyncio.create_task(self.handle_cli_input())

        self.stop_event = asyncio.Event()

        def on_shutdown():
            self.stop_event.set()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, on_shutdown)
        loop.add_signal_handler(signal.SIGTERM, on_shutdown)

        try:
            async with self.server_proc:
                await self.stop_event.wait()
        finally:
            if self.debug:
                print("[EventHandler] Shutting down...")
            log_task.cancel()
            cli_task.cancel()
            try: await log_task
            except (asyncio.CancelledError, KeyboardInterrupt): pass
            try: await cli_task
            except (asyncio.CancelledError, KeyboardInterrupt): pass

            await self.server.shutdown()
            for writer in list(self.protocol.clients.values()):
                writer.close()
                await writer.wait_closed()
            self.server_proc.close()
            await self.server_proc.wait_closed()

    async def dispatch_log_events(self):
        try:
            async for raw_line in self.server.read_lines():
                if self.debug:
                    print(raw_line)
                text, loginfo, triggered = self.event_engine.process_line(raw_line)

                # Group events by client
                staged_callbacks = {}
                for addr, event_name in triggered:
                    if addr not in staged_callbacks:
                        staged_callbacks[addr] = {
                            "type": "event",
                            "data": text,
                            "loginfo": loginfo,
                            "triggered": []
                        }
                    staged_callbacks[addr]["triggered"].append(event_name)

                for addr, payload in staged_callbacks.items():
                    writer = self.protocol.clients.get(addr)
                    if writer is None:
                        continue
                    try:
                        writer.write((json.dumps(payload) + "\n").encode())
                        await writer.drain()
                    except Exception:
                        self.event_engine.unregister_all_for_addr(addr)
                        writer.close()
                        await writer.wait_closed()
                        del self.protocol.clients[addr]
        except Exception as e:
            if self.debug:
                print(f"[Log Dispatcher Error] {e}")
        finally:
            self.stop_event.set()

    async def handle_cli_input(self):
        """
        Reads lines from stdin and sends them to the server.
        """
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line_task = asyncio.create_task(reader.readline())
                stop_task = asyncio.create_task(self.stop_event.wait())

                done, pending = await asyncio.wait([line_task, stop_task], return_when=asyncio.FIRST_COMPLETED)

                if stop_task in done:
                    line_task.cancel()
                    break

                line = line_task.result()
                if not line:
                    break
                line = line.decode().strip()
                try:
                    self.server.send_command(line)
                except Exception as e:
                    if self.debug:
                        print(f"[Command Error] {e}")
            except (asyncio.CancelledError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"[CLI Input Error] {e}")

if __name__ == "__main__":
    import yaml
    from dotenv import load_dotenv

    with open("configs/server-wrapper.yml", "r") as fp:
        config = yaml.safe_load(fp)
    load_dotenv("configs/server-wrapper.env")
    load_dotenv("configs/server-wrapper-secrets.env")

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
