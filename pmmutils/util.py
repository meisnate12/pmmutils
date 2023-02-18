import glob, time, os, requests
from datetime import datetime, timedelta
from functools import cached_property
from pathvalidate import is_valid_filename, sanitize_filename
from tqdm import tqdm
from .exceptions import Failed

def update_send(old_send, timeout):
    def new_send(*send_args, **kwargs):
        if kwargs.get("timeout", None) is None:
            kwargs["timeout"] = timeout
        return old_send(*send_args, **kwargs)
    return new_send

def glob_filter(filter_in):
    filter_in = filter_in.translate({ord("["): "[[]", ord("]"): "[]]"}) if "[" in filter_in else filter_in
    return glob.glob(filter_in)

def is_locked(filepath):
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            file_object = open(filepath, 'a', 8)
            if file_object:
                locked = False
        except IOError:
            locked = True
        finally:
            if file_object:
                file_object.close()
    return locked

def validate_filename(filename):
    if not is_valid_filename(str(filename)):
        filename = sanitize_filename(str(filename))
    return filename

def download_image(download_image_url, path, name="temp"):
    image_response = requests.get(download_image_url)
    if image_response.status_code >= 400:
        raise Failed("Image Error: Image Download Failed")
    if image_response.headers["Content-Type"] not in ["image/png", "image/jpeg", "image/webp"]:
        raise Failed("Image Error: Image Not PNG, JPG, or WEBP")
    if image_response.headers["Content-Type"] == "image/jpeg":
        temp_image_name = f"{name}.jpg"
    elif image_response.headers["Content-Type"] == "image/webp":
        temp_image_name = f"{name}.webp"
    else:
        temp_image_name = f"{name}.png"
    temp_image_name = os.path.join(path, temp_image_name)
    with open(temp_image_name, "wb") as handler:
        handler.write(image_response.content)
    while is_locked(temp_image_name):
        time.sleep(1)
    return temp_image_name

def move_path(file_path, old_base, new_base, suffix=None, append=True):
    rel_path = file_path.removeprefix(old_base)[1:]
    final_path = os.path.join(new_base, rel_path)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)
    final_file = f"{final_path}{suffix}" if suffix and append else final_path.removesuffix(suffix) if suffix else final_path
    os.rename(file_path, final_file)
    return final_file

byte_levels = [
    (1024 ** 5, 'Petabyte'), (1024 ** 4, 'Terabyte'), (1024 ** 3, 'Gigabyte'),
    (1024 ** 2, 'Megabyte'), (1024 ** 1, 'Kilobyte'), (1024 ** 0, 'Byte'),
]
def format_bytes(byte_count):
    byte_count = int(byte_count)
    if byte_count <= 0:
        return "0 Bytes"
    for factor, suffix in byte_levels:
        if byte_count >= factor:
            return f"1 {suffix}" if byte_count == factor else f"{byte_count / factor:.2f} {suffix}s"

def copy_with_progress(src, dst, description=None):
    size = os.path.getsize(src)
    with open(src, "rb") as fsrc:
        with open(dst, "wb") as fdst:
            with tqdm(total=size, unit="B", unit_scale=True, desc=description) as pbar:
                while True:
                    chunk = fsrc.read(4096)
                    if not chunk:
                        break
                    fdst.write(chunk)
                    pbar.update(len(chunk))

def in_the_last(file, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
    file_time = datetime.fromtimestamp(os.path.getctime(file))
    now = datetime.now()
    current = now - timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)
    return current <= file_time <= now, str(now - file_time).split(".")[0]

class Stats:
    def __init__(self):
        self.data = {None: Stat()}

    def start(self, name=None):
        self[name] = Stat()

    def finish(self, name=None):
        return self[name].end

    def runtime(self, name=None):
        return self[name].runtime

    def stat(self, key, value, name=None):
        self[name][key] = value

    def __getitem__(self, name):
        if name in self.data:
            return self.data[name]
        raise KeyError(name)

    def __setitem__(self, key, value):
        self.data[key] = value

class Stat:
    def __init__(self, name=None):
        self.name = name
        self.start = datetime.now()
        self.stats = {}

    def __getitem__(self, key):
        if key in self.stats:
            return self.stats[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.stats[key] = value

    @cached_property
    def end(self):
        return datetime.now()

    @cached_property
    def runtime(self):
        return str(self.end - self.start).split(".")[0]

    def __str__(self):
        return self.runtime
