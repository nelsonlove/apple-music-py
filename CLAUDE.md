# apple-music-py

Python library and CLI for controlling Apple Music on macOS. Formerly "clawtunes".

## Architecture

```
src/
├── apple_music/            # Access library (no CLI dependencies)
│   ├── client.py           # MusicClient: unified API (single entry point)
│   ├── applescript.py      # AppleScript execution wrapper (osascript)
│   ├── catalog.py          # Apple Music catalog search (iTunes Search API)
│   ├── playback.py         # Library operations: search, play, volume, playlists, AirPlay
│   └── status.py           # Now-playing info and player state (NowPlaying dataclass)
├── clawtunes/              # CLI package (consumes apple_music)
│   ├── cli.py              # Click-based commands calling MusicClient
│   └── selection.py        # Interactive numbered menu for multiple matches
plugin/
  claude-code/              # Claude Code plugin (calls CLI)
```

Dependency direction: `plugin → CLI (apple-music) → MusicClient (apple_music) → AppleScript`

## Python API

```python
from apple_music import MusicClient
client = MusicClient()
client.now_playing()          # NowPlaying | None
client.search_songs("query")  # list of (id, display_text)
client.pause()                # error string | None
```

## Development

```bash
uv run pytest              # run tests
uv run apple-music --help  # run CLI
just test                  # run tests via justfile
just check                 # lint + type-check + test
```

## Key constraints

- `MusicClient` is the single entry point for the `apple_music` library
- The library has zero CLI dependencies — `click` is only in `clawtunes/`
- All Apple Music interaction goes through AppleScript (`osascript`)
- Mute state is cached in `~/Library/Caches/clawtunes/`
