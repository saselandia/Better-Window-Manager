#!/usr/bin/env bash
# Re-apply Spicetify and relaunch Spotify in the workspace it was in (see reload-spotify.py)
exec python3 "$(dirname "$(readlink -f "$0")")/reload-spotify.py" "$@"
