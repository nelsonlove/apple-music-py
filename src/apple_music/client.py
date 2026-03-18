"""Unified client for Apple Music — the single entry point for all operations.

Wraps playback, status, and catalog modules behind a single class.
"""

from __future__ import annotations

from . import catalog, playback, status
from .status import NowPlaying


class MusicClient:
    """Apple Music client.

    Provides programmatic access to Apple Music playback, library search,
    catalog search, playlists, volume, and AirPlay.
    """

    # ── Status ───────────────────────────────────────────────────────

    def now_playing(self) -> NowPlaying | None:
        """Get the currently playing track, or None."""
        return status.get_now_playing()

    def player_state(self) -> str:
        """Get player state: 'playing', 'paused', 'stopped', or 'unknown'."""
        return status.get_player_state()

    # ── Playback control ─────────────────────────────────────────────

    def pause(self) -> str | None:
        """Pause playback. Returns error or None."""
        return playback.pause()

    def resume(self) -> str | None:
        """Resume playback. Returns error or None."""
        return playback.resume()

    def next_track(self) -> str | None:
        """Skip to next track. Returns error or None."""
        return playback.next_track()

    def previous_track(self) -> str | None:
        """Go to previous track. Returns error or None."""
        return playback.previous_track()

    # ── Search (library) ─────────────────────────────────────────────

    def search_songs(
        self,
        name: str,
        limit: int | None = None,
        artist: str | None = None,
    ) -> list[tuple[str, str]]:
        """Search library songs. Returns list of (id, display_text)."""
        return playback.search_songs(name, limit=limit, artist=artist)

    def search_albums(
        self, name: str, limit: int | None = None,
    ) -> list[tuple[str, str]]:
        """Search library albums. Returns list of (album_name, display_text)."""
        return playback.search_albums(name, limit=limit)

    def search_playlists(
        self, name: str, limit: int | None = None,
    ) -> list[tuple[str, str]]:
        """Search playlists. Returns list of (playlist_name, display_text)."""
        return playback.search_playlists(name, limit=limit)

    def search_songs_in_playlist(
        self,
        playlist_name: str,
        song_name: str,
        limit: int | None = None,
        artist: str | None = None,
    ) -> list[tuple[str, str]]:
        """Search songs within a playlist. Returns list of (id, display_text)."""
        return playback.search_songs_in_playlist(
            playlist_name, song_name, limit=limit, artist=artist,
        )

    # ── Play ─────────────────────────────────────────────────────────

    def play_track(self, track_id: str) -> bool:
        """Play a track by its ID."""
        return playback.play_track_by_id(track_id)

    def play_album(self, album_name: str) -> bool:
        """Play an album by name."""
        return playback.play_album_by_name(album_name)

    def play_playlist(self, playlist_name: str) -> bool:
        """Play a playlist by name."""
        return playback.play_playlist_by_name(playlist_name)

    # ── Volume ───────────────────────────────────────────────────────

    def get_volume(self) -> tuple[int, bool] | None:
        """Get (volume, is_muted) or None."""
        return playback.get_volume()

    def set_volume(self, level: int) -> str | None:
        """Set volume (0-100). Returns error or None."""
        return playback.set_volume(level)

    def mute(self) -> str | None:
        """Mute. Returns error or None."""
        return playback.mute()

    def unmute(self) -> str | None:
        """Unmute. Returns error or None."""
        return playback.unmute()

    # ── Shuffle and repeat ───────────────────────────────────────────

    def get_shuffle(self) -> bool | None:
        return playback.get_shuffle()

    def set_shuffle(self, enabled: bool) -> str | None:
        return playback.set_shuffle(enabled)

    def get_repeat(self) -> str | None:
        return playback.get_repeat()

    def set_repeat(self, mode: str) -> str | None:
        return playback.set_repeat(mode)

    # ── Love/dislike ─────────────────────────────────────────────────

    def love(self) -> str | None:
        """Love current track. Returns error or None."""
        return playback.love_current_track()

    def dislike(self) -> str | None:
        """Dislike current track. Returns error or None."""
        return playback.dislike_current_track()

    def love_state(self) -> tuple[bool, bool] | None:
        """Get (favorited, disliked) for current track."""
        return playback.get_current_track_love_state()

    # ── Playlists ────────────────────────────────────────────────────

    def list_playlists(self) -> list[tuple[str, int]]:
        """List all playlists. Returns list of (name, track_count)."""
        return playback.get_all_playlists()

    def create_playlist(self, name: str) -> tuple[bool, str]:
        """Create a playlist. Returns (success, message)."""
        return playback.create_playlist(name)

    def add_to_playlist(self, playlist_name: str, track_id: str) -> tuple[bool, str]:
        """Add a track to a playlist. Returns (success, message)."""
        return playback.add_song_to_playlist(playlist_name, track_id)

    def remove_from_playlist(self, playlist_name: str, track_id: str) -> tuple[bool, str]:
        """Remove a track from a playlist. Returns (success, message)."""
        return playback.remove_song_from_playlist(playlist_name, track_id)

    # ── AirPlay ──────────────────────────────────────────────────────

    def airplay_devices(self) -> list[tuple[str, str, bool, bool]]:
        """List AirPlay devices. Returns list of (name, kind, available, selected)."""
        return playback.get_airplay_devices()

    def set_airplay(self, device_name: str, selected: bool) -> str | None:
        """Select/deselect an AirPlay device. Returns error or None."""
        return playback.set_airplay_device(device_name, selected)

    # ── Catalog (Apple Music streaming) ──────────────────────────────

    def search_catalog(self, query: str, limit: int = 10) -> list[tuple[str, str]]:
        """Search Apple Music catalog. Returns list of (trackViewUrl, display_text)."""
        results = catalog.search_catalog(query, limit=limit)
        return catalog.format_catalog_results(results)

    def open_catalog_track(self, track_url: str) -> bool:
        """Open a catalog track URL in Music.app."""
        return catalog.open_catalog_track(track_url)
