import json
import asyncio

class FofServerProtocol:
    def __init__(self, event_engine, data_store, server, debug=False):
        self.clients = {}
        self.event_engine = event_engine
        self.data_store = data_store
        self.server = server
        self.debug = debug

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.clients[addr] = writer
        try:
            while True:
                try:
                    data = await asyncio.wait_for(reader.readline(), timeout=60.0)
                except asyncio.TimeoutError:
                    continue
                if not data: break
                body = json.loads(data.decode(errors='ignore').strip())
                type_ = body["type"]
                if type_ == 'ping':
                    await self.ping(writer)
                elif type_ == "store":
                    self.data_store.store(body)
                elif type_ == "get":
                    await self.get(body, writer)
                elif type_ == "command":
                    self.server.send_command(body["command"])
                elif type_ == "register":
                    self.event_engine.register(addr, body)
                elif type_ == "unregister":
                    self.event_engine.unregister(addr, body)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if self.debug:
                print(f"[Client Handler Error] {e}")
        finally:
            if self.debug:
                print(f"[Client Disconnected] {addr}")
            # Unregister all events for this client!
            self.event_engine.unregister_all_for_addr(addr)
            writer.close()
            await writer.wait_closed()
            del self.clients[addr]

    async def ping(self, writer):
        try:
            writer.write(b'__pong__\n')
            await writer.drain()
        except Exception:
            pass

    async def get(self, body, writer):
        keys = body["keys"]
        payload = self.data_store.get(keys)
        writer.write((json.dumps({"type": "get-response", "keys": keys, "payload": payload}) + "\n").encode())
        await writer.drain()