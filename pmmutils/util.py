import glob, time, os, requests
from pathvalidate import is_valid_filename, sanitize_filename
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
