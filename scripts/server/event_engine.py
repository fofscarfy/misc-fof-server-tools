import re

class EventEngine:
    def __init__(self, debug=False):
        self.condition_registry = {}
        self.callback_registry = {}
        self.compiled_regex = {}
        self.debug = debug

    def register(self, addr, body):
        registry = body["registry"]
        for name, conds in registry.items():
            conditions = [(k, v) for k, v in conds.items()]
            callback = (addr, name)
            for condition in conditions:
                if condition not in self.condition_registry:
                    self.condition_registry[condition] = set()
                self.condition_registry[condition].add(callback)
                if condition[0] == "regex" and condition[1] not in self.compiled_regex:
                    self.compiled_regex[condition[1]] = re.compile(condition[1])
            self.callback_registry[callback] = conditions
            if self.debug:
                print(f"Registered {name} for {addr}!")

    def unregister(self, addr, body):
        events = body["events"]
        for event in events:
            callback = (addr, event)
            if callback not in self.callback_registry: continue
            conditions = self.callback_registry[callback]
            del self.callback_registry[callback]
            for condition in conditions:
                self.condition_registry[condition].remove(callback)
                if not self.condition_registry[condition]:
                    del self.condition_registry[condition]
                    if condition[0] == "regex":
                        del self.compiled_regex[condition[0]]

    def unregister_all_for_addr(self, addr):
        # Unregister all callbacks for this addr
        callback_names = [cb[1] for cb in self.callback_registry if cb[0] == addr]
        for name in callback_names:
            self.unregister(addr, {"events": [name]})

    def process_line(self, text):
        loginfo = ""
        if not text.startswith("L ") or len(text) <= 25 or text[12:15] != " - " or text[23:25] != ": ":
            loginfo = ""
        else:
            loginfo = text[:25]
            text = text[25:]

        satisfaction = {k: len(v) for k, v in self.callback_registry.items()}
        for condition, callbacks in self.condition_registry.items():
            type_, val = condition
            matches = True
            if type_ == 'logged':
                matches = str(loginfo != "") == val
            elif type_ == 'regex':
                matches = self.compiled_regex[val].search(text)
            elif type_ == 'match':
                matches = val in text
            elif type_ == 'exclude':
                matches = val not in text
            elif type_ == 'startswith':
                matches = text.startswith(val)
            elif type_ == 'endswith':
                matches = text.endswith(val)
            elif type_ == 'equal':
                matches = text == val
            if matches:
                for callback in callbacks:
                    satisfaction[callback] -= 1

        triggered = []
        for callback, complete in satisfaction.items():
            if complete == 0:
                triggered.append(callback)
        return text, loginfo, triggered
