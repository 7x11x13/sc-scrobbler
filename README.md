# sc-scrobble

A Last.FM scrobbler for SoundCloud, using the internal SoundCloud play history API for platform-agnostic scrobbling.

## Why?

SoundCloud scrobbling is [not officially supported](https://support.last.fm/t/soundcloud-scrobbling/176) by Last.FM, and the third party scrobblers available only work for web or Android phones. This scrobbler works regardless of listening platform.

## Setup

Requires the following env vars to be set:

```py
LAST_FM_API_KEY        # see https://www.last.fm/api/account/create
LAST_FM_API_SECRET     # same ^
LAST_FM_USERNAME       # username of account to send scrobbles to
LAST_FM_PASSWORD       # password of account to send scrobbles to
SOUNDCLOUD_USER_ID     # soundcloud user id to get listening history from
COOKIE_RELAY_URL       # cookie-relay (https://github.com/7x11x13/cookie-relay) instance
COOKIE_RELAY_API_KEY   # cookie-relay API key
UPDATE_INTERVAL        # how many seconds to wait between listening history checks
```
