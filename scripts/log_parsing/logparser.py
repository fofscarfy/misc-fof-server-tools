import re
from pathlib import Path

from scripts.log_parsing import EVENT_PATTERNS, check_known_events, yield_log_lines

# Directory settings
log_dir = Path("fof/logs")  # Change this to your actual path
output_dir = Path("./unprocessed")
output_dir.mkdir(exist_ok=True)

# File to collect unhandled lines
unprocessed_file = output_dir / "unprocessed.txt"
                
counts = {}
# Process logs
with unprocessed_file.open("w", encoding="utf-8") as unprocessed_out:
    for log_file in log_dir.glob("*.log"):
        for line, data in yield_log_lines(log_file):
            name, event_data = check_known_events(line)
            if name is None: 
                unprocessed_out.write(line + "\n")
            else: 
                data.update(event_data)
                if name not in counts: 
                    counts[name] = {
                        "count": 1,
                        "example": line
                    }
                else: counts[name]["count"] += 1

import json
print(json.dumps(counts, indent=4))