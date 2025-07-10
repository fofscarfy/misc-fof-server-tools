class DataStore:
    def __init__(self):
        self.anonymous_data = {}

    def store(self, body):
        keys, payload = body["keys"], body["payload"]
        dict_ = self.anonymous_data
        for key in keys[:-1]:
            if key not in dict_ or not isinstance(dict_[key], dict):
                dict_[key] = {}
            dict_ = dict_[key]
        dict_[keys[-1]] = payload

    def get(self, keys):
        dict_ = self.anonymous_data
        for key in keys[:-1]:
            if key not in dict_ or not isinstance(dict_[key], dict):
                return None
            dict_ = dict_[key]
        return dict_.get(keys[-1], None)