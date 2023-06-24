import configparser
from logging import warning
import os


class WhitespaceFriendlyConfigParser(configparser.ConfigParser):
    def get(self, section, option, *args, **kwargs):
        val = super().get(section, option, *args, **kwargs)
        return val.strip('"')


class Config:
    def __init__(self):
        self.debug = False
        self.module = None
        self.database = None

        self.lemmy_server = None
        self.lemmy_username = None
        self.lemmy_password = None
        self.community = None

        self.post_title = None


def from_file(file_path):
    parsed = WhitespaceFriendlyConfigParser()
    success = parsed.read(file_path)
    if len(success) == 0:
        warning("Failed to load config file")
        return None

    config = Config()

    if "data" in parsed:
        sec = parsed["data"]
        config.database = sec.get("database", None)

    if "post" in parsed:
        sec = parsed["post"]
        config.post_title = sec.get("title", None)

    # secrets from env variables
    config.lemmy_server = os.environ.get("LEMMY_SERVER")
    config.lemmy_username = os.environ.get("LEMMY_USERNAME")
    config.lemmy_password = os.environ.get("LEMMY_PASSWORD")
    config.community = os.environ.get("LEMMY_COMMUNITY")

    return config


def validate_config(config):
    def is_bad_str(s):
        return s is None or len(s) == 0

    if is_bad_str(config.database):
        return "database missing"
    if is_bad_str(config.post_title):
        return "post title missing"
