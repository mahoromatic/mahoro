from logging import debug, info, error, exception
from pythorhead import Lemmy

_r = None
_config = None
_community_cache = {}

def init_reddit(config):
    global _config
    _config = config

def _connect_reddit():
    if _config is None:
        error("Can't connect to reddit without a config")
        return None

    lemmy = Lemmy(_config.lemmy_server)
    lemmy.log_in(_config.lemmy_username, _config.lemmy_password)
    return lemmy


def _ensure_connection():
    global _r
    if _r is None:
        _r = _connect_reddit()
    return _r is not None

def submit_link_post(title, url, community, nsfw):
    _ensure_connection()

    global _community_cache
    community_id = _community_cache.get(community)
    if not community_id:
        community_id = _r.discover_community(community)
        _community_cache[community] = community_id

    try:
        info(f"Submitting post '{title}'    {url}")
        submission = _r.post.create(community_id, name=title, url=url, nsfw=bool(nsfw))
        return submission
    except:
        exception("Failed to submit post")
        return None
