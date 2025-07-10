from scripts.log_parsing import check_event

def yield_log_lines(file):
    with open(file, "r", encoding="utf-8", errors="ignore") as fp:
        base_line = None
        base_data = None

        while (line := fp.readline()):
            evt, data = check_event(line, "timestamp")
            if evt is not None:
                if base_line is not None: 
                    yield base_line[25:].replace("\n", "").strip(), data
                base_line = ""
                base_data = data
            base_line += line

        if base_line is not None and base_line.endswith("\n"):
            yield base_line[25:].replace("\n", "").strip(), base_data

def yield_line_data(file):
    for line, data in yield_log_lines(file):
        evt, evt_data = check_known_events(line)

        yield line, data.update(evt_data)