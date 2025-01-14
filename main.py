import os
import time
from typing import TypedDict
import structlog
import pylast
import requests
from soundcloud import HistoryItem, SoundCloud
from dotenv import load_dotenv

load_dotenv()


class Scrobble(TypedDict):
    artist: str
    title: str
    timestamp: int


log = structlog.get_logger()

fm = pylast.LastFMNetwork(
    api_key=os.getenv("LAST_FM_API_KEY"),
    api_secret=os.getenv("LAST_FM_API_SECRET"),
    username=os.getenv("LAST_FM_USERNAME"),
    password_hash=pylast.md5(os.getenv("LAST_FM_PASSWORD")),
)

soundcloud: SoundCloud = None


def get_auth_token():
    user_id = os.getenv("SOUNDCLOUD_USER_ID")
    cookie_url = os.getenv("COOKIE_RELAY_URL")
    cookie_key = os.getenv("COOKIE_RELAY_API_KEY")
    url = f"{cookie_url}/cookies/soundcloud/{user_id}/oauth_token"
    with requests.get(url, headers={"Cookie-Relay-API-Key": cookie_key}) as r:
        r.raise_for_status()
        return r.json()["value"]


def get_sc_client():
    global soundcloud
    if soundcloud and soundcloud.is_auth_token_valid():
        return soundcloud

    soundcloud = SoundCloud(auth_token=get_auth_token())
    return soundcloud


most_recent_item: HistoryItem = None
to_scrobble: list[Scrobble] = []


def scrobble_from_item(item: HistoryItem):
    return {
        "artist": item.track.user.username,
        "title": item.track.title,
        "timestamp": int(item.played_at / 1000),
    }


def is_a_scrobble(item: HistoryItem, next_item: HistoryItem):
    # https://www.last.fm/api/scrobbling#when-is-a-scrobble-a-scrobble
    played_for_s = (next_item.played_at - item.played_at) / 1000
    track_length_s = item.track.duration / 1000
    if track_length_s <= 30:
        return False
    if played_for_s * 2 >= track_length_s:
        return True
    return played_for_s >= 4 * 60


def update_scrobbles():
    global most_recent_item
    global to_scrobble
    client = get_sc_client()
    scrobbles = []
    next_item = None
    latest_item = None
    for item in client.get_my_history():
        if latest_item is None:
            latest_item = item

        if item.played_at <= most_recent_item.played_at:
            break

        if next_item:
            if is_a_scrobble(item, next_item):
                scrobbles.append(scrobble_from_item(item))

        next_item = item

    if next_item:
        if is_a_scrobble(most_recent_item, next_item):
            scrobbles.append(scrobble_from_item(most_recent_item))

    if most_recent_item.played_at != latest_item.played_at:
        log.debug(
            "Now playing",
            artist=latest_item.track.user.username,
            title=latest_item.track.title,
        )
        fm.update_now_playing(latest_item.track.user.username, latest_item.track.title)

    most_recent_item = latest_item

    to_scrobble += scrobbles
    if scrobbles:
        log.debug("New scrobbles", scrobbles=scrobbles)

    if to_scrobble:
        fm.scrobble_many(to_scrobble)
        to_scrobble = []


def init():
    global most_recent_item
    client = get_sc_client()
    most_recent_item = next(client.get_my_history())


def main():
    init()
    while True:
        try:
            update_scrobbles()
        except Exception as err:
            log.error("An error occurred", exc_info=err)
        finally:
            time.sleep(int(os.getenv("UPDATE_INTERVAL")))


if __name__ == "__main__":
    main()
