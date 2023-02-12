import argparse, os, platform, requests, uuid
from dotenv import load_dotenv

def parse_choice(env_str, default, arg_bool=False, arg_int=False):
    env_value = os.environ.get(env_str)
    if env_value or (arg_int and env_value == 0):
        if arg_bool:
            if env_value is True or env_value is False:
                return env_value
            elif env_value.lower() in ["t", "true"]:
                return True
            else:
                return False
        elif arg_int:
            try:
                return int(env_value)
            except ValueError:
                return default
        else:
            return str(env_value)
    else:
        return default

class Version:
    def __init__(self, original="Unknown", text="develop"):
        self.original = original
        self.text = text
        self.version = self.original.replace("develop", self.text)
        split_version = self.version.split(f"-{self.text}")
        self.master = split_version[0]
        self.patch = int(split_version[1]) if len(split_version) > 1 else 0
        sep = (0, 0, 0) if self.original == "Unknown" else self.master.split(".")
        self.compare = (sep[0], sep[1], sep[2], self.patch)
        self._has_patch = None

    def has_patch(self):
        return self.patch > 0

    def __str__(self):
        return self.version

    def __bool__(self):
        return self.original != "Unknown"

    def __eq__(self, other):
        return self.compare == other.compare

    def __ne__(self, other):
        return self.compare != other.compare

    def __lt__(self, other):
        return self.compare < other.compare

    def __le__(self, other):
        return self.compare <= other.compare

    def __gt__(self, other):
        return self.compare > other.compare

    def __ge__(self, other):
        return self.compare >= other.compare

class PMMArgs:
    def __init__(self, repo_name, base_dir, options, use_nightly=True, is_nightly=False):
        self.repo = repo_name
        self.base_dir = base_dir
        self.options = options
        self.use_nightly = use_nightly
        self.is_nightly = is_nightly
        self.choices = {}
        self._nightly_version = None
        self._develop_version = None
        self._master_version = None
        self._system_version = None
        self._update_version = None
        self._local_version = None
        self._version = None
        self._local_branch = None
        self._env_branch = None
        self._branch = None
        self._is_docker = None
        self._is_linuxserver = None
        self._uuid = None
        parser = argparse.ArgumentParser()
        if not isinstance(options, list):
            raise ValueError("options must be a list")
        for o in self.options:
            for atr in ["type", "arg", "env", "key", "help", "default"]:
                if atr not in o:
                    raise AttributeError(f"{o} attribute must be in every option")
            if o["type"] == "int":
                parser.add_argument(f"-{o['arg']}", f"--{o['key']}", dest=o["key"], help=o["help"], type=int, default=o["default"])
            elif o["type"] == "bool":
                parser.add_argument(f"-{o['arg']}", f"--{o['key']}", dest=o["key"], help=o["help"], action="store_true", default=o["default"])
            else:
                parser.add_argument(f"-{o['arg']}", f"--{o['key']}", dest=o["key"], help=o["help"])
        args_parsed = parser.parse_args()
        load_dotenv(os.path.join(self.base_dir, "config", ".env"))

        for o in self.options:
            self.choices[o["key"]] = parse_choice(o["env"], getattr(args_parsed, o["key"]), arg_int=o["type"] == "int", arg_bool=o["type"] == "bool")

    @property
    def uuid(self):
        if self._uuid is None:
            uuid_file = os.path.join(self.base_dir, "config", "UUID")
            if os.path.exists(uuid_file):
                with open(uuid_file) as handle:
                    for line in handle.readlines():
                        line = line.strip()
                        if len(line) > 0:
                            self._uuid = str(line)
                            break
            if not self._uuid:
                self._uuid = str(uuid.uuid4())
                with open(uuid_file, "w") as handle:
                    handle.write(self._uuid)
        return self._uuid

    @property
    def system_version(self):
        if self._system_version is None:
            if self.is_docker:
                self._system_version = "Docker"
            elif self.is_linuxserver:
                self._system_version = "Linuxserver"
            else:
                self._system_version = f"Python {platform.python_version()}"
            self._system_version = f"({self._system_version})"
            if self.local_branch:
                self._system_version = f"{self._system_version} (Git: {self.local_branch})"
        return self._system_version

    @property
    def is_docker(self):
        if self._is_docker is None:
            self._is_docker = parse_choice("PMM_DOCKER", False, arg_bool=True)
        return self._is_docker

    @property
    def is_linuxserver(self):
        if self._is_linuxserver is None:
            self._is_linuxserver = parse_choice("PMM_LINUXSERVER", False, arg_bool=True)
        return self._is_linuxserver

    @property
    def local_version(self):
        if self._local_version is None:
            self._local_version = False
            with open(os.path.join(self.base_dir, "VERSION")) as handle:
                for line in handle.readlines():
                    line = line.strip()
                    if len(line) > 0:
                        self._local_version = Version(line)
                        break
        return None if self._local_version is False else self._local_version

    @property
    def nightly_version(self):
        if self._nightly_version is None:
            self._nightly_version = self.online_version("nightly")
        return self._nightly_version

    @property
    def develop_version(self):
        if self._develop_version is None:
            self._develop_version = self.online_version("develop")
        return self._nightly_version

    @property
    def master_version(self):
        if self._master_version is None:
            self._master_version = self.online_version("master")
        return self._master_version

    def online_version(self, level):
        try:
            url = f"https://raw.githubusercontent.com/{self.repo}/{level}/VERSION"
            return Version(requests.get(url).content.decode().strip(), text=level)
        except requests.exceptions.ConnectionError:
            return None

    @property
    def version(self):
        if self._version is None:
            if self.branch == "nightly":
                self._version = self.nightly_version
            elif self.branch == "develop":
                self._version = self.develop_version
            else:
                self._version = self.master_version
        return self._version

    @property
    def local_branch(self):
        if self._local_branch is None:
            try:
                from git import Repo, InvalidGitRepositoryError
                try:
                    self._local_branch = Repo(path=".").head.ref.name # noqa
                except InvalidGitRepositoryError:
                    self._local_branch = False
            except ImportError:
                self._local_branch = False
        return None if self._local_branch is False else self._local_branch

    @property
    def env_branch(self):
        if self._env_branch is None:
            self._env_branch = parse_choice("BRANCH_NAME", "master")
        return self._env_branch

    @property
    def branch(self):
        if self._branch is None:
            if self.is_nightly:
                self._branch = "nightly"
            elif self.local_branch:
                self._branch = self.local_branch
            elif self.env_branch in ["nightly", "develop"]:
                self._branch = self.env_branch
            elif self.local_version.has_patch():
                self._branch = "develop" if not self.use_nightly or self.local_version <= self.develop_version else "nightly"
            else:
                self._branch = "master"
        return self._branch

    @property
    def update_version(self):
        if self._update_version is None:
            self._update_version = False
            if self.version and self.local_version < self.version:
                self._update_version = self.version
        return None if self._update_version is False else self._update_version

