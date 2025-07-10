# Log Parsing
Here's what each of the files in this folder do:

# fof_regex.py

This is where all of the regular expressions are stored. You can either access them directly with the `EVENT_PATTERNS` dictionary or use one of the helper functions to make things easier:

- `check_event(line, event)`: Check against a specific event type in `EVENT_PATTERNS` - if successful, it will return the name of the event and the extracted matching data.
- `check_known_events(line)`: This will iterate over all events (excluding timestamp) until one of them matches. It will similarly return the name of the event and the extracted data.
- `strip_timestamp(line)`: This simple helper just chops off the first few characters corresponding to the log events.

***Note**: When processing lines, it's easiest to first extract the timestamp data and then match against known events.*

Feel free to share if you have more events that you think people would benefit from.

# fof_log_iterator.py

This just contains a couple functions that help iterate over lines.

- `yield_log_lines(file)`: This is an iterator that will yield lines from a file in the format `(line_without_timestamp, extracted_timestamp_data)`.
- `yield_line_data(file)`: This method uses `yield_log_lines` and checks the remainder of the line against patterns stored in `fof_regex.py`. The data returned is similar: `(line_without_timestamp, extracted_data_plus_timestamp_data)`.

# logparser.py

This is mostly a test script, but you can use it to go through your log directory to get stats on how much each event has been triggered as well as any leftover events that weren't handled by the pre-defined patterns.