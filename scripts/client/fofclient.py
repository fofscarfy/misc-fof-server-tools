import asyncio
import json
import os

class FofClient:
    COMMAND_DICT = {"type": "command", "command": ""}
    GET_DICT = {"type": "get", "keys": []}
    STORE_DICT = {"type": "store", "keys": [], "payload": {}}
    REGISTER_DICT = {"type": "register", "registry": {}}
    UNREGISTER_DICT = {"type": "unregister", "events": []}

    def __init__(self, host="127.0.0.1", port=9000, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.reader = None
        self.writer = None
        self.event_handlers = {}
        self.listen_task = None
        self._on_connect = []
        self._on_disconnect = []
        self._connected = asyncio.Event()
        self._interrupted = False

    def on_connect(self, behavior):
        self._on_connect.append(behavior)

    def on_disconnect(self, behavior):
        self._on_disconnect.append(behavior)

    async def _fire_on_connect(self):
        self._connected.set()
        for func in self._on_connect:
            await func(self)

    async def _fire_on_disconnect(self):
        self._connected.clear()
        for func in self._on_disconnect:
            await func(self)

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.listen_task = asyncio.create_task(self._listen())
            await self._fire_on_connect()
        except:
            await self._fire_on_disconnect()
            raise

    async def disconnect(self):
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def send(self, payload):
        if not self.writer:
            raise RuntimeError("Not connected.")
        self.writer.write((payload + "\n").encode())
        await self.writer.drain()

    async def command(self, command_str):
        self.COMMAND_DICT["command"] = command_str
        await self.send(json.dumps(self.COMMAND_DICT))

    async def store(self, keys, value):
        self.STORE_DICT["keys"] = keys
        self.STORE_DICT["payload"] = value
        await self.send(json.dumps(self.STORE_DICT))

    async def get(self, keys):
        self.GET_DICT["keys"] = keys
        await self.send(json.dumps(self.GET_DICT))

    async def register_event(self, name, regex=None, match_=None, exclude=None, startswith=None, endswith=None, logged=None, equal=None):
        registry = {}
        if regex is not None: registry["regex"] = regex
        if match_ is not None: registry["match"] = match_
        if exclude is not None: registry["exclude"] = exclude
        if startswith is not None: registry["startswith"] = startswith
        if endswith is not None: registry["endswith"] = endswith
        if logged is not None: registry["logged"] = logged
        if equal is not None: registry["equal"] = equal

        self.REGISTER_DICT["registry"] = {name: registry}
        await self.send(json.dumps(self.REGISTER_DICT))

    async def unregister_event(self, name):
        self.UNREGISTER_DICT["events"] = [name]
        await self.send(json.dumps(self.UNREGISTER_DICT))

    def on_event(self, name):
        # Decorator to attach a handler
        def decorator(func):
            self.event_handlers[name] = func
            return func
        return decorator

    async def _listen(self):
        try:
            while True:
                line = await self.reader.readline()
                if not line:
                    break

                try:
                    message = json.loads(line.decode(errors="ignore").strip())
                    print(f"Received {message}")
                except Exception as e:
                    print(f"[FofClient] Failed to parse message: {e}")
                    continue

                if message["type"] == "get-response":
                    print("[FofClient] Get-response (not handled automatically):", message)
                elif message["type"] == "event":
                    triggered = message.get("triggered", [])

                    for event_name in triggered:
                        if event_name in self.event_handlers:
                            try:
                                await self.event_handlers[event_name](message)
                            except Exception as e:
                                print(f"[FofClient] Error in event handler {event_name}: {e}")
                else:
                    print("[FofClient] Unrecognized message:", message)

        except asyncio.CancelledError:
            self._interrupted = True
            pass
        except Exception as e:
            print(f"[FofClient] Listener error: {e}")

    async def run(self, reconnect_delay=5):
        failed_connect = False
        while True:
            try:
                if self.debug: print("Attempting connection!")
                await self.connect()
                if self.debug: print("Connected!")
                failed_connect = False
                await self.listen_task
                if self._interrupted:
                    print("Interrupted - closing!")
                    break
                print("Lost connection! Will retry.")
            except Exception as e:
                await self._fire_on_disconnect()
                if isinstance(e, KeyboardInterrupt):
                    print("Interrupted - closing!")
                    break
                if not failed_connect:
                    failed_connect = True
                    print(f"[FofClient] Connection error: {e}")
            await asyncio.sleep(reconnect_delay)

async def main():
    bot = FofClient()

    await bot.run()

    while True:
        command = input("> ")
        if not command: continue
