from dataclasses import dataclass
import re

@dataclass(frozen=True)
class EventPattern:
    name: str
    pattern: re.Pattern
    extractor: callable

EVENT_PATTERNS = {
    # NOTE: Chop off the timestamp with this pattern BEFORE using the other patterns.
    # Example: `L 05/03/2025 - 01:36:24: `
    "timestamp": EventPattern(
        name="timestamp",
        pattern=re.compile(r"L (\d{2}/\d{2}/\d{4} - \d{2}:\d{2}:\d{2}): (.*)"),
        extractor=lambda m: {"event_type": "timestamp", "timestamp": m[0]}
    ),

    # Example: `"Scarfy<132><[U:1:Numbers]><>\" entered the game`
    "entered_game": EventPattern(
        name="entered_game",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" entered the game'),
        extractor=lambda m: {"event_type": "entered_game", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3]}
    ),

    # Example: `"Scarfy<132><[U:1:Numbers]><Unassigned>" joined team "Spectator"`
    "join_team": EventPattern(
        name="join_team",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" joined team "(.*?)"'),
        extractor=lambda m: {"event_type": "join_team", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "prev_team": m[3], "new_team": m[4]}
    ),

    # Example: `"Scarfy<132><[U:1:Numbers]><Vigilantes>" say "!gt_creepycreek"`
    "say": EventPattern(
        name="say",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" say "(.*)"'),
        extractor=lambda m: {"event_type": "say", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "message": m[4]}
    ),

    # Example: `"Scarfy<129><[U:1:Numbers]><Bandidos>" say_team "wha"`
    "say_team": EventPattern(
        name="say_team",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" say_team "(.*)"'),
        extractor=lambda m: {"event_type": "team_say", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "message": m[4]}
    ),

    # Example: `server_message: "quit"`
    "server_message": EventPattern(
        name="server_message",
        pattern=re.compile(r'server_message: "(.*?)"'),
        extractor=lambda m: {"event_type": "server_message", "message": m[0]}
    ),

    # Example: `rcon from "127.0.0.1:50478": command "quit"`
    "rcon_command": EventPattern(
        name="rcon_command",
        pattern=re.compile(r'rcon from "([\d\.:]+)": command "(.*)"'),
        extractor=lambda m: {"event_type": "rcon_command", "address": m[0], "command": m[1]}
    ),

    # Example: `"BOT Gypsy<683><BOT><Desperados>" disconnected (reason "Kicked from server")`
    "disconnect": EventPattern(
        name="disconnect",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" disconnected \(reason "(.*?)"?\)?'),
        extractor=lambda m: {"event_type": "disconnect", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "reason": m[4]}
    ),

    # Example: `Log file started (file "logs/L0323075.log") (game "/home/fofserver/fofserver/fof") (version "0")`
    "log_start": EventPattern(
        name="log_start",
        pattern=re.compile(r'Log file started \(file "(.*?)"\) \(game "(.*?)"\) \(version "(.*?)"\)'),
        extractor=lambda m: {"event_type": "log_start", "filename": m[0], "game_path": m[1], "version": m[2]}
    ),

    # Example: `Log file closed.`
    "log_end": EventPattern(
        name="log_end",
        pattern=re.compile(r"Log file closed\."),
        extractor=lambda m: {"event_type": "log_end"}
    ),

    # Example: `"BOT Mezcal<188><BOT><>" connected, address "none"`
    "connected": EventPattern(
        name="connected",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><>" connected, address "(.*?)"'),
        extractor=lambda m: {"event_type": "connected", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "address": m[3]}
    ),

    # Example: `"BOT Brokstone<193><BOT><Bandidos>" triggered "combat" (notoriety "17")`
    "triggered_combat": EventPattern(
        name="triggered_combat",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" triggered "combat" \(notoriety "(-?\d+)"\)'),
        extractor=lambda m: {"event_type": "triggered_combat", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "notoriety": int(m[4])}
    ),

    # Example: `"BOT Brokstone<193><BOT><Bandidos>" killed "BOT Kowalski<190><BOT><Rangers>" with "arrow" (headshot) (attacker_position "306 755 380") (victim_position "-150 361 280")`
    "kill": EventPattern(
        name="kill",
        pattern=re.compile(
            r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" killed '
            r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" with "(.+?)"( \(headshot\))? '
            r'\(attacker_position "(.+?)"\) \(victim_position "(.+?)"\)'
        ),
        extractor=lambda m: {
            "event_type": "kill",
            "attacker": {"name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "position": m[10]},
            "victim": {"name": m[4], "user_id": int(m[5]), "steam_id": m[6], "team": m[7], "position": m[11]},
            "weapon": m[8], "headshot": m[9] is not None
        }
    ),

    # Example: `[META] Loaded 0 plugins (1 already loaded)`
    "loaded_plugins": EventPattern(
        name="loaded_plugins",
        pattern=re.compile(r'\[META\] Loaded (\d+) plugins\.?( \((.*)?already loaded\))?'),
        extractor=lambda m: {
            "event_type": "loaded_plugins",
            "plugin_count": int(m[0]),
            "already_loaded": int(m[2]) if len(m) > 1 and m[2] and m[2].isdigit() else 0
        }
    ),

    # Example: `server_cvar: "sm_nextmap" "fof_sweetwater"`
    "server_cvar": EventPattern(
        name="server_cvar",
        pattern=re.compile(r'server_cvar: "(.+?)" "(.*?)"'),
        extractor=lambda m: {"event_type": "server_cvar", "key": m[0], "value": m[1]}
    ),

    # Example: `"sm_super_kick_version" = "1.10.0"`
    "init_cvar": EventPattern(
        name="init_cvar",
        pattern=re.compile(r'"(\S+)" = "(.*)"'),
        extractor=lambda m: {"event_type": "init_cvar", "key": m[0], "value": m[1]}
    ),
    
    # Example: `server cvars start`
    "start_cvars": EventPattern(
        name="start_cvars",
        pattern=re.compile(r'server cvars start'),
        extractor=lambda m: {"event_type": "start_cvars"}
    ),

    # Example: `server cvars end`
    "end_cvars": EventPattern(
        name="end_cvars",
        pattern=re.compile(r'server cvars end'),
        extractor=lambda m: {"event_type": "end_cvars"}
    ),

    # Example: `Loading map "fof_sweetwater"`
    "loading_map": EventPattern(
        name="loading_map",
        pattern=re.compile(r'Loading map "(\S+)"'),
        extractor=lambda m: {"event_type": "loading_map", "map": m[0]}
    ),

    # Example: `Started map "fof_sweetwater" (CRC "6863ca2417cb94ea3e1999d2305795fc")`
    "started_map": EventPattern(
        name="started_map",
        pattern=re.compile(r'Started map "(\S+)" \(CRC "(\w+)"\)'),
        extractor=lambda m: {"event_type": "started_map", "map": m[0], "CRC": m[1]}
    ),

    # Example: `Engine error: Host_Error: WatchdogHandler called - server exiting.`
    "engine_error": EventPattern(
        name="engine_error",
        pattern=re.compile(r'Engine error: (.*)'),
        extractor=lambda m: {"event_type": "engine_error", "error": m[0]}
    ),

    # Example: Banid: "<><[U:1:Numbers]><>" was banned "permanently" by "Console"
    "ban": EventPattern(
        name="ban",
        pattern=re.compile(r'Banid: "<><(\[U:\d+:\d+\])><>" was banned "(.*?)" by "(.*?)"'),
        extractor=lambda m: {"event_type": "ban", "steam_id": m[0], "duration": m[1], "source": m[2]}
    ),

    # Example: `"Scarfy<136><[U:1:Numbers]><>" STEAM USERID validated`
    "steamid_validated": EventPattern(
        name="steamid_validated",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\])><.*?>" STEAM USERID validated'),
        extractor=lambda m: {"event_type": "steamid_validated", "name": m[0], "user_id": int(m[1]), "steam_id": m[2]}
    ),

    # Example: `"BOT Mezcal<188><BOT><Desperados>" committed suicide with "world"`
    "suicide": EventPattern(
        name="suicide",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" committed suicide with "(.*)"'),
        extractor=lambda m: {"event_type": "suicide", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "weapon": m[4]}
    ),

    # Example: `"Northern Star<1948><[U:1:Numbers]><Rangers>" changed name to "yellowbelliedcoward"`
    "change_name": EventPattern(
        name="change_name",
        pattern=re.compile(r'"(.+?)<(\d+)><(\[U:\d+:\d+\]|BOT|Console)><(.*?)>" changed name to "(.*)"'),
        extractor=lambda m: {"event_type": "change_name", "name": m[0], "user_id": int(m[1]), "steam_id": m[2], "team": m[3], "new_name": m[4]}
    ),

    # Example: `Connection to Steam servers successful.`
    "steam_server_connection": EventPattern(
        name="steam_server_connection",
        pattern=re.compile(r'Connection to Steam servers successful\.'),
        extractor=lambda m: {"event_type": "steam_server_connection"}
    ),

    # Example: `Connection to Steam servers lost.  (Result = 3)`
    "steam_connection_lost": EventPattern(
        name="steam_connection_lost",
        pattern=re.compile(r'Connection to Steam servers lost\.\s*\(Result = (\d+)\)'),
        extractor=lambda m: {"event_type": "steam_connection_lost", "result": int(m[0])}
    ),

    # Example: `STEAMAUTH: Client Scarfy received failure code 6`
    "steamauth_fail": EventPattern(
        name="steamauth_fail",
        pattern=re.compile(r'STEAMAUTH: Client (.*?) received failure code (\d+)'),
        extractor=lambda m: {"event_type": "steamauth_fail", "client": m[0], "code": int(m[1])}
    ),

    # Example: `=== Scarfy was kicked due high ping or unreliable connection (ping 253 loss 0) ===`
    "ping_kick": EventPattern(
        name="ping_kick",
        pattern=re.compile(r'=== (.*) was kicked due high ping or unreliable connection \(ping (\d+) loss (\d+)\) ==='),
        extractor=lambda m: {"event_type": "ping_kick", "client": m[0], "ping": int(m[1]), "loss": int(m[2])}
    ),

    # Example: `Public IP is 138.197.125.1`
    "public_ip": EventPattern(
        name="public_ip",
        pattern=re.compile(r'\s*Public IP is ([\d\.]+)\.'),
        extractor=lambda m: {"event_type": "public_ip", "address": m[0]}
    ),

    # Example: `Assigned anonymous gameserver Steam ID [A:1:Some:Numbers].`
    "gameserver_id": EventPattern(
        name="gameserver_id",
        pattern=re.compile(r'Assigned (anonymous|persistent) gameserver Steam ID \[([\w:]+)\]\.'),
        extractor=lambda m: {
            "event_type": "gameserver_id",
            "persistent": m[0] == "persistent",
            "anonymous": m[0] == "anonymous",
            "id": m[1]
        }
    ),

    # Example: `VAC secure mode is activated.`
    "vac_mode": EventPattern(
        name="vac_mode",
        pattern=re.compile(r'VAC secure mode is (\w+)\.'),
        extractor=lambda m: {"event_type": "vac_mode", "activated": m[0] == "activated"}
    ),

    # Example: `========== Stats For Team VIGILANTES Score: 0  Avg Skill: <1/5 - Why go on killing?> ===========\n`
    "scoreboard_team_header": EventPattern(
        name="scoreboard_team_header",
        pattern=re.compile(r'=+ Stats For Team (\w+) Score: (\d+)  Avg Skill: <(\d+)/5 - .+> =+'),
        extractor=lambda m: {"event_type": "scoreboard_team_header", "team": m[0], "skill": int(m[1])}
    ),

    # Example: `Scarfy                             602       36       26       7        71.57% 2          1204`
    "scoreboard_player_line": EventPattern(
        name="scoreboard_player_line",
        pattern=re.compile(r'^(.+?)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+([\d.]+%)?\s*(\d+)?\s*(-?\d+)?$'),
        extractor=lambda m: {
            "event_type": "scoreboard_player_line", 
            "player": m[0], 
            "notoriety": int(m[1]), 
            "frags": int(m[2]), 
            "deaths": int(m[3]), 
            "assists": int(m[4]), 
            "accuracy": float(m[5].strip('%')) if m[5] else None, 
            "dominates": int(m[6]) if m[6] is not None else 0, 
            "noto_balance": int(m[7]) if m[7] else None
        }

    )
}

def check_event(line, event):
    if event not in EVENT_PATTERNS: return None, None

    matchobj = EVENT_PATTERNS[event].pattern.match(line)
    if matchobj:
        return event, EVENT_PATTERNS[event].extractor(matchobj.groups())
    else:
        return None, None

def check_known_events(line):
    for name, event in EVENT_PATTERNS.items():
        if name == "timestamp": continue
        match = event.pattern.match(line)
        if match:
            return event.name, event.extractor(match.groups())
    return None, None

def strip_timestamp(line): 
    return line[25:]