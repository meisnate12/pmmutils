import os, ruamel.yaml
from pmmutils import Failed

class YAML:
    def __init__(self, path=None, input_data=None, check_empty=False, create=False, start_empty=False):
        self.path = path
        self.input_data = input_data
        self.yaml = ruamel.yaml.YAML()
        self.yaml.indent(mapping=2, sequence=2)
        try:
            if input_data:
                self.data = self.yaml.load(input_data)
            else:
                if start_empty or (create and not os.path.exists(self.path)):
                    with open(self.path, 'w'):
                        pass
                    self.data = {}
                else:
                    with open(self.path, encoding="utf-8") as fp:
                        self.data = self.yaml.load(fp)
        except ruamel.yaml.error.YAMLError as e:
            e = str(e).replace("\n", "\n      ")
            raise Failed(f"YAML Error: {e}")
        except Exception as e:
            raise Failed(f"YAML Error: {e}")
        if not self.data or not isinstance(self.data, dict):
            if check_empty:
                raise Failed("YAML Error: File is empty")
            self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def __repr__(self):
        return repr(self.data)

    def __len__(self):
        return len(self.data)

    def __delitem__(self, key):
        del self.data[key]

    def clear(self):
        return self.data.clear()

    def copy(self):
        return self.data.copy()

    def has_key(self, k):
        return k in self.data

    def update(self, *args, **kwargs):
        return self.data.update(*args, **kwargs)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def pop(self, *args):
        return self.data.pop(*args)

    def __iter__(self):
        return iter(self.data)

    def save(self):
        if self.path:
            with open(self.path, 'w', encoding="utf-8") as fp:
                self.yaml.dump(self.data, fp)

    @staticmethod
    def inline(data):
        if isinstance(data, list):
            output = ruamel.yaml.comments.CommentedSeq(data)
        elif isinstance(data, dict):

            output = ruamel.yaml.comments.CommentedMap(data)
        else:
            return data
        output.fa.set_flow_style()
        return output

    @staticmethod
    def quote(data):
        return ruamel.yaml.scalarstring.DoubleQuotedScalarString(data)
