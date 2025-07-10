# Python Plugins with FofClient
So... you're here because you didn't want to learn SourcePawn. Or worse, you want to cast judgement on me - not to worry, there are plenty of opportunities for that.

FofClient is a way to interact with the python server wrapper that allows you to react to text-based events in real-time. You can register events, send server commands, and pass data between plugins with a shared storage on the server side.

The goal of this was to make simple, free-standing breakout plugins that remain lightweight and separate in their functionality - this way you don't just keep coding directly on the main server.

The client connects to a separate server spawned by the python server wrapper, which is then used to interact with the Fistful of Frags server.

## FofClient Functions

There are a few useful user-facing functions that are useful when designing plugins using FofClient.

### `command`
This one will run whatever string you pass on the server console.

### `store`
This takes a list of keys and a payload to be stored in the shared storage between plugins. The keys should be an ordered list of keys used to index the shared storage, and the payload is the data to store at that location.

### `get`
This takes a list of keys which is used to index the shared storage. The keys should be an ordered list of keys used to index the shared storage. Responses appear in `self.received_data` at the same index as in the shared storage.

### `register`
This is used to register event names and what they go with. The function handle looks like this:
```python
    async def register_event(self, name, regex=None, match_=None, exclude=None, startswith=None, endswith=None, logged=None, equal=None):
```

The `name` is just a name assignment you give the event. The other arguments are used to assess whether a line from the server output triggers this event:
| match type | description |
| --- | --- |
| logged | The line starts with the log timestamp. |
| regex | The line matches a client-defined regular expression. |
| match | The line contains a client-defined string. |
| exclude | The line does not contain a client-defined string. |
| startswith | The line starts with a client-defined string. |
| endswith | The line ends with a client-defined string. |
| equal | The line exactly equal to a client-defined string. |

### `unregister`
This is used to unregister events from the server that you're no longer using. This can't be used to unregister events of other clients - only your own. You just have to pass in the name of the event you want to unregister.

### `on_connect`/`on_disconnect`
These commands take single-argument functions to run when the server starts, the single argument being the client itself. This is especially useful for registering events. Here's an example for how you might do this:
```python
fofclient = FofClient()
async def register_on_connect(client):
    await client.register_event("on_mapchange", startswith="-------- Mapchange to ")

fofclient.on_connect(register_on_connect)
```

## Working with FofClient
Let's take a look at a snippet of [my bot randomization script](/scripts/bots/autoshuffler.py) as an example.
```python
    async def start(self):
        self.fofclient = FofClient()

        @self.fofclient.on_event("on_mapchange")
        async def randomize(message_data):
            print("Map Changing! Shuffling bots.")
            shuffle_bots(self.data_file, self.output_file, self.boss_chance, self.same_team, self.same_team_no)

        async def register_on_connect(client):
            await client.register_event("on_mapchange", startswith="-------- Mapchange to ", exclude='say')

        self.fofclient.on_connect(register_on_connect)
        await self.fofclient.run()
```

The first thing you might notice is that we have a decorator:
```python
@self.fofclient.on_event("on_mapchange")
```
This is telling our fofclient that whenever it receives an event called `"on_mapchange"`, it should run `randomize` using the incoming message data.

`message_data` is the data that is reported when the client receives an event response. It's a dictionary with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'event' when returning data. |
| loginfo | If the line has the logging timestamp at the front, this contains that string |
| data | This is the line that matched. This never contains the logging timestamp. |
| triggered | A list of strings corresponding to events that were triggered by this line. |

After defining this function, it needs to be registered with the server when we connect, as well as define what exactly `"on_mapchange"` is. So we tell our client to register our definition of `"on_mapchange"` when the client connects to the server:
```python
async def register_on_connect(client):
    await client.register_event("on_mapchange", startswith="-------- Mapchange to ", exclude='say')

self.fofclient.on_connect(register_on_connect)
```
Here we're defining `register_on_connect` as a behavior to perform when the client makes a connection to the server. We're also defining `"on_mapchange"` to be any line that (excluding the timestamp) starts with `"-------- Mapchange to "` and excludes the word `"say"`. Any line that has these qualities will trigger this event.

Finally, we can start our client with the following:
```
await self.fofclient.run()
```
Once this is going, the client should always be on and will register its events whenever it makes a connection to the server.

***NOTE**: You don't have to worry about unregistering events before disconnecting - the server will automatically remove all events attached to your plugin if it disconnects.*

***NOTE**: You don't have to restart your plugins in the event that the server goes down and comes back up if you use `on_connect` - it will continue to listen for the server and re-register once the server is back.*