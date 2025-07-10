# Python-Based Server Wrapper

In my best efforts not to learn SourcePawn, I decided to wrap my server in python so that I can react to the log outputs and write my own custom plugins. This directory contains parts of how this is done.

## `fof_server_wrapper.py`
If you're looking for how I launch the server and get the outputs - this is the file to look at. This file reads from [server-wrapper.env](/configs/server-wrapper.env) and [server-wrapper.yml](/configs/server-wrapper.yml), and can run as a standalone with the following command:
```bash
python -m scripts.server.fof_server_wrapper
```

***NOTE**: For this to work, you should have `./srcds_run` in your current directory/the root of the repo.*

This should launch a server and show you the outputs back. (Use Ctrl + C to exit).

The gist of how this works is that I use pty to emulate a terminal for the server to run in. I'm able to read and write to the terminal session in real-time, which is how the server runs commands and feeds back the log output.

## `fof_server_event_handler.py`
This is the overall script that launches the server as well as spawns another (local) server to interact with plugins. This also reads from [server-wrapper.env](/configs/server-wrapper.env) and [server-wrapper.yml](/configs/server-wrapper.yml), and can be run with the following command:
```bash
python -m scripts.server
```

***NOTE**: Like before, for this to work, you should have `./srcds_run` in your current directory/the root of the repo.*

This launches the server in a way that offers event handling, shared plugin storage, and command forwarding.

## `protocol.py`
This file is responsible for handling incoming requests from plugins:
| Request | Description |
| --- | --- |
| `ping` | The client is asking if the server is still active. |
| `store` | The client has data it wants to put in shared storage. |
| `get` | The client wants to retrieve data from shared storage. |
| `command` | The client wants to run a server command. |
| `register` | The client wants to be notified on a certain event. |
| `unregister` | The client no longer wants to be notified of an event. |

There's more information on each of these requests below.

## `data_store.py`
This is essentially a glorified dictionary. It probably didn't need its own breakout class but it defines the `store` and `get` functionality for the shared storage.

### Store Packets
Data is stored when a packet comes in with a json with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'store' |
| keys | A list of keys that lead to where the data is to be stored. |
| payload | The data to store at the location indexed by the keys. |

### Get Packets
When a plugin wants to retrieve data, it's with a packet with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'get' |
| keys | The keys used to index the shared storage. |

### Get-Response Packets
Data is sent back to the client through `protocol.py` in a JSON object with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'get-response' |
| keys | The keys used to index the shared storage. |
| payload | The data at the index specified by the keys. |

## `event_engine.py`
This handles the registered events, processing each line to see if it matches an existing event.
String matching and regex are used to figure out whether or not a line matches, and multiple types of matches can be registered for one event. Here are the possible types of matches:
| match type | description |
| --- | --- |
| logged | The line starts with the log timestamp. |
| regex | The line matches a client-defined regular expression. |
| match | The line contains a client-defined string. |
| exclude | The line does not contain a client-defined string. |
| startswith | The line starts with a client-defined string. |
| endswith | The line ends with a client-defined string. |
| equal | The line exactly equal to a client-defined string. |

***NOTE**: If an event is logged, then the logged portion is ignored, so 'startswith' acts on whatever is after the timestamp rather than starting with the timestamp.*

### Register Event Packets
Events are registered with packets from clients using the following fields:
| Field | Description |
| --- | --- |
| type | Always 'register'  for registering events. |
| registry | A sub-dictionary of events to register. |

Each component in the registry looks like the following:
```json
"registry": {
    "<event_name>": {
        "regex" : "<regex_value>",
        "match": "<match_value>",
        "exclude": "<exclude_value>",
        "startswith": "<startswith_value>",
        "endswith": "<endswith_value>",
        "logged": "<logged_value>",
        "equal": "<equal_value>"
    }
}
```
***NOTE**: Only the values that are needed are put in the dictionary - for instance, if an event only uses "logged" and "exclude", those would be the only two keys in the dictionary.*

### Unregister Event Packets
Events can later be unregistered with packets from the clients with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'unregister' for unregistering events. |
| events | List of event names to no longer listen for. |

***NOTE**: It is perfectly fine for two different clients to use the same event names - they are stored separately and will not interfere with one another.*

### Event Triggered Packets
When all events are evaluated, it goes back to `fof_server_event_handler.py` and constructs a JSON object with the following fields:
| Field | Description |
| --- | --- |
| type | Always 'event' for events. |
| data | The requested data. |
| loginfo | If the text data had the log timestamp, the timestamp info populates this field. |
| triggered | A list of events triggered by the line. |

The handling of these events is up to the plugin.