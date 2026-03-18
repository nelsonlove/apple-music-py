"""Clawtunes CLI - Control Apple Music from the command line."""

import click

from apple_music import MusicClient
from apple_music import status as music_status
from clawtunes.selection import is_non_interactive, select_item


def format_error(error: str) -> str:
    """Format error message, adding hints for common issues."""
    if "Not authorized" in error or "-1743" in error:
        return (
            f"{error}\n"
            "Hint: Grant automation access in System Settings > "
            "Privacy & Security > Automation > enable your terminal to control Music"
        )
    return error


@click.group()
@click.version_option()
@click.option(
    "--non-interactive", "-N", is_flag=True, help="Don't prompt; list matches and exit"
)
@click.option("--first", "-1", is_flag=True, help="Auto-select the first match")
@click.pass_context
def cli(ctx, non_interactive, first):
    """Control Apple Music from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["non_interactive"] = non_interactive
    ctx.obj["first"] = first
    ctx.obj["client"] = MusicClient()


def _client(ctx) -> MusicClient:
    return ctx.obj["client"]


@cli.group()
def play():
    """Play songs, albums, or playlists."""
    pass


@play.command("song")
@click.argument("name")
@click.option("--artist", "-A", default=None, help="Filter by artist name")
@click.pass_context
def play_song(ctx, name: str, artist: str | None):
    """Play a song by name."""
    client = _client(ctx)
    songs = client.search_songs(name, artist=artist)

    if not songs:
        click.echo(f"No songs found matching '{name}'")
        raise SystemExit(1)

    if len(songs) == 1:
        click.echo(f"Playing: {songs[0][1]}")
        if not client.play_track(songs[0][0]):
            raise SystemExit(1)
        return

    click.echo(f"Found {len(songs)} matching songs:")
    selected_id = select_item(songs, "Select a song")

    if selected_id is None:
        if not is_non_interactive():
            click.echo("Cancelled")
        raise SystemExit(1)

    selected_display = next(d for i, d in songs if i == selected_id)
    click.echo(f"Playing: {selected_display}")
    if not client.play_track(selected_id):
        raise SystemExit(1)


@play.command("album")
@click.argument("name")
@click.pass_context
def play_album(ctx, name: str):
    """Play an album by name."""
    client = _client(ctx)
    albums = client.search_albums(name)

    if not albums:
        click.echo(f"No albums found matching '{name}'")
        raise SystemExit(1)

    if len(albums) == 1:
        click.echo(f"Playing album: {albums[0][1]}")
        if not client.play_album(albums[0][0]):
            raise SystemExit(1)
        return

    click.echo(f"Found {len(albums)} matching albums:")
    selected_name = select_item(albums, "Select an album")

    if selected_name is None:
        if not is_non_interactive():
            click.echo("Cancelled")
        raise SystemExit(1)

    selected_display = next(d for n, d in albums if n == selected_name)
    click.echo(f"Playing album: {selected_display}")
    if not client.play_album(selected_name):
        raise SystemExit(1)


@play.command("playlist")
@click.argument("name")
@click.pass_context
def play_playlist(ctx, name: str):
    """Play a playlist by name."""
    client = _client(ctx)
    playlists = client.search_playlists(name)

    if not playlists:
        click.echo(f"No playlists found matching '{name}'")
        raise SystemExit(1)

    if len(playlists) == 1:
        click.echo(f"Playing playlist: {playlists[0][1]}")
        if not client.play_playlist(playlists[0][0]):
            raise SystemExit(1)
        return

    click.echo(f"Found {len(playlists)} matching playlists:")
    selected_name = select_item(playlists, "Select a playlist")

    if selected_name is None:
        if not is_non_interactive():
            click.echo("Cancelled")
        raise SystemExit(1)

    selected_display = next(d for n, d in playlists if n == selected_name)
    click.echo(f"Playing playlist: {selected_display}")
    if not client.play_playlist(selected_name):
        raise SystemExit(1)


@cli.command()
@click.pass_context
def pause(ctx):
    """Pause playback."""
    error = _client(ctx).pause()
    if error is None:
        click.echo("Paused")
    else:
        click.echo(f"Failed to pause: {format_error(error)}", err=True)
        raise SystemExit(1)


@cli.command()
@click.pass_context
def resume(ctx):
    """Resume playback."""
    error = _client(ctx).resume()
    if error is None:
        click.echo("Resumed")
    else:
        click.echo(f"Failed to resume: {format_error(error)}", err=True)
        raise SystemExit(1)


@cli.command("next")
@click.pass_context
def next_track(ctx):
    """Skip to the next track."""
    error = _client(ctx).next_track()
    if error is None:
        click.echo("Skipped to next track")
    else:
        click.echo(f"Failed to skip: {format_error(error)}", err=True)
        raise SystemExit(1)


@cli.command("prev")
@click.pass_context
def prev_track(ctx):
    """Go to the previous track."""
    error = _client(ctx).previous_track()
    if error is None:
        click.echo("Went to previous track")
    else:
        click.echo(f"Failed to go back: {format_error(error)}", err=True)
        raise SystemExit(1)


@cli.command("status")
@click.option("--debug", is_flag=True, help="Show AppleScript output for debugging")
@click.pass_context
def show_status(ctx, debug: bool):
    """Show the currently playing track."""
    if debug:
        stdout, stderr, returncode = music_status.get_now_playing_raw()
        click.echo(f"AppleScript stdout: {stdout!r}")
        if stderr:
            click.echo(f"AppleScript stderr: {stderr!r}", err=True)
        click.echo(f"AppleScript exit code: {returncode}")
        now_playing = music_status.parse_now_playing(stdout, returncode)
    else:
        now_playing = _client(ctx).now_playing()
    player_state = _client(ctx).player_state()

    if now_playing is None:
        click.echo("Nothing is playing")
        return

    state_indicator = (
        "▶" if player_state == "playing" else "⏸" if player_state == "paused" else "⏹"
    )

    click.echo(f"{state_indicator} {now_playing.name}")
    click.echo(f"  Artist: {now_playing.artist}")
    click.echo(f"  Album:  {now_playing.album}")
    click.echo(
        f"  {now_playing.progress_bar} {now_playing.position_formatted} / {now_playing.duration_formatted}"
    )


# Volume control


@cli.command("volume")
@click.argument("level", required=False)
@click.pass_context
def volume(ctx, level: str | None):
    """Get or set volume. Use +/- prefix for relative adjustment."""
    client = _client(ctx)
    if level is None:
        result = client.get_volume()
        if result is None:
            click.echo("Failed to get volume", err=True)
            raise SystemExit(1)
        vol, muted = result
        mute_indicator = " (muted)" if muted else ""
        click.echo(f"Volume: {vol}%{mute_indicator}")
        return

    try:
        if level.startswith("+"):
            result = client.get_volume()
            if result is None:
                click.echo("Failed to get current volume", err=True)
                raise SystemExit(1)
            current, _ = result
            new_level = current + int(level[1:])
        elif level.startswith("-"):
            result = client.get_volume()
            if result is None:
                click.echo("Failed to get current volume", err=True)
                raise SystemExit(1)
            current, _ = result
            new_level = current - int(level[1:])
        else:
            new_level = int(level)
    except ValueError:
        click.echo(f"Invalid volume level: {level}", err=True)
        raise SystemExit(1)

    error = client.set_volume(new_level)
    if error:
        click.echo(f"Failed to set volume: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo(f"Volume: {max(0, min(100, new_level))}%")


@cli.command("mute")
@click.pass_context
def mute(ctx):
    """Mute volume."""
    error = _client(ctx).mute()
    if error:
        click.echo(f"Failed to mute: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo("Muted")


@cli.command("unmute")
@click.pass_context
def unmute(ctx):
    """Unmute volume."""
    error = _client(ctx).unmute()
    if error:
        click.echo(f"Failed to unmute: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo("Unmuted")


# Shuffle and repeat


@cli.command("shuffle")
@click.argument("state", type=click.Choice(["on", "off"], case_sensitive=False))
@click.pass_context
def shuffle(ctx, state: str):
    """Set shuffle mode."""
    error = _client(ctx).set_shuffle(state.lower() == "on")
    if error:
        click.echo(f"Failed to set shuffle: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo(f"Shuffle: {state.lower()}")


@cli.command("repeat")
@click.argument("mode", type=click.Choice(["off", "all", "one"], case_sensitive=False))
@click.pass_context
def repeat(ctx, mode: str):
    """Set repeat mode."""
    error = _client(ctx).set_repeat(mode.lower())
    if error:
        click.echo(f"Failed to change repeat mode: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo(f"Repeat: {mode.lower()}")


# Search


@cli.command("search")
@click.argument("query")
@click.option("--songs/--no-songs", "-s", default=True, help="Search songs")
@click.option("--albums/--no-albums", "-a", default=True, help="Search albums")
@click.option(
    "--playlists/--no-playlists", "-p", default=False, help="Search playlists"
)
@click.option("--limit", "-n", default=10, help="Max results per category")
@click.option("--artist", "-A", default=None, help="Filter songs by artist name")
@click.pass_context
def search(ctx, query, songs, albums, playlists, limit, artist):
    """Search for songs, albums, or playlists."""
    client = _client(ctx)
    found_any = False

    if songs:
        results = client.search_songs(query, limit=limit, artist=artist)
        if results:
            found_any = True
            click.echo(f"Songs ({len(results)}):")
            for _, display in results:
                click.echo(f"  {display}")
            click.echo()

    if albums:
        results = client.search_albums(query, limit=limit)
        if results:
            found_any = True
            click.echo(f"Albums ({len(results)}):")
            for _, display in results:
                click.echo(f"  {display}")
            click.echo()

    if playlists:
        results = client.search_playlists(query, limit=limit)
        if results:
            found_any = True
            click.echo(f"Playlists ({len(results)}):")
            for _, display in results:
                click.echo(f"  {display}")
            click.echo()

    if not found_any:
        click.echo(f"No results found for '{query}'")


# Love/dislike


@cli.command("love")
@click.pass_context
def love(ctx):
    """Love the current track."""
    client = _client(ctx)
    error = client.love()
    if error:
        click.echo(f"Failed to love track: {format_error(error)}", err=True)
        raise SystemExit(1)
    now_playing = client.now_playing()
    click.echo(f"Loved: {now_playing.name}" if now_playing else "Loved current track")


@cli.command("dislike")
@click.pass_context
def dislike(ctx):
    """Dislike the current track."""
    client = _client(ctx)
    error = client.dislike()
    if error:
        click.echo(f"Failed to dislike track: {format_error(error)}", err=True)
        raise SystemExit(1)
    now_playing = client.now_playing()
    click.echo(f"Disliked: {now_playing.name}" if now_playing else "Disliked current track")


# Playlists


@cli.command("playlists")
@click.pass_context
def list_playlists(ctx):
    """List all playlists."""
    playlists = _client(ctx).list_playlists()
    if not playlists:
        click.echo("No playlists found")
        return

    click.echo(f"Playlists ({len(playlists)}):")
    for name, count in playlists:
        click.echo(f"  {name} ({count} tracks)")


@cli.group()
def playlist():
    """Manage playlists (create, add songs, remove songs)."""
    pass


@playlist.command("create")
@click.argument("name")
@click.pass_context
def playlist_create(ctx, name: str):
    """Create a new playlist."""
    success, message = _client(ctx).create_playlist(name)
    click.echo(message, err=not success)
    if not success:
        raise SystemExit(1)


@playlist.command("add")
@click.argument("playlist_name")
@click.argument("song")
@click.option("--artist", "-A", default=None, help="Filter by artist name")
@click.pass_context
def playlist_add(ctx, playlist_name: str, song: str, artist: str | None):
    """Add a song to a playlist."""
    client = _client(ctx)
    songs = client.search_songs(song, artist=artist)

    if not songs:
        click.echo(f"No songs found matching '{song}'")
        raise SystemExit(1)

    if len(songs) == 1:
        selected_id, selected_display = songs[0]
    else:
        click.echo(f"Found {len(songs)} matching songs:")
        result = select_item(songs, "Select a song")
        if result is None:
            if not is_non_interactive():
                click.echo("Cancelled")
            raise SystemExit(1)
        selected_id = result
        selected_display = next(d for i, d in songs if i == selected_id)

    success, message = client.add_to_playlist(playlist_name, selected_id)
    if success:
        click.echo(f'Added "{selected_display}" to "{playlist_name}"')
    else:
        click.echo(message, err=True)
        raise SystemExit(1)


@playlist.command("remove")
@click.argument("playlist_name")
@click.argument("song")
@click.option("--artist", "-A", default=None, help="Filter by artist name")
@click.pass_context
def playlist_remove(ctx, playlist_name: str, song: str, artist: str | None):
    """Remove a song from a playlist."""
    client = _client(ctx)
    songs = client.search_songs_in_playlist(playlist_name, song, artist=artist)

    if not songs:
        click.echo(f"No songs found matching '{song}' in playlist '{playlist_name}'")
        raise SystemExit(1)

    if len(songs) == 1:
        selected_id, selected_display = songs[0]
    else:
        click.echo(f"Found {len(songs)} matching songs in '{playlist_name}':")
        result = select_item(songs, "Select a song")
        if result is None:
            if not is_non_interactive():
                click.echo("Cancelled")
            raise SystemExit(1)
        selected_id = result
        selected_display = next(d for i, d in songs if i == selected_id)

    success, message = _client(ctx).remove_from_playlist(playlist_name, selected_id)
    if success:
        click.echo(f'Removed "{selected_display}" from "{playlist_name}"')
    else:
        click.echo(message, err=True)
        raise SystemExit(1)


# AirPlay


@cli.command("airplay")
@click.argument("device", required=False)
@click.option("--off", is_flag=True, help="Deselect the device")
@click.pass_context
def airplay(ctx, device: str | None, off: bool):
    """List or select AirPlay devices."""
    client = _client(ctx)
    devices = client.airplay_devices()

    if device is None:
        if not devices:
            click.echo("No AirPlay devices found")
            return
        click.echo("AirPlay devices:")
        for name, kind, available, selected in devices:
            status_str = ""
            if selected:
                status_str = " [selected]"
            elif not available:
                status_str = " [unavailable]"
            click.echo(f"  {name} ({kind}){status_str}")
        return

    matching = [d for d in devices if device.lower() in d[0].lower()]
    if not matching:
        click.echo(f"No device found matching '{device}'", err=True)
        raise SystemExit(1)

    if len(matching) > 1:
        click.echo(f"Multiple devices match '{device}':")
        for name, kind, _, _ in matching:
            click.echo(f"  {name} ({kind})")
        raise SystemExit(1)

    target_name = matching[0][0]
    error = client.set_airplay(target_name, not off)
    if error:
        click.echo(f"Failed to set AirPlay device: {format_error(error)}", err=True)
        raise SystemExit(1)
    click.echo(f"{'Deselected' if off else 'Selected'}: {target_name}")


# Catalog (Apple Music streaming)


@cli.group()
def catalog_cmd():
    """Search Apple Music catalog."""
    pass


cli.add_command(catalog_cmd, name="catalog")


@catalog_cmd.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=10, help="Max results")
@click.pass_context
def catalog_search(ctx, query: str, limit: int):
    """Search Apple Music catalog and open the song in Music."""
    client = _client(ctx)
    results = client.search_catalog(query, limit=limit)

    if not results:
        click.echo(f"No results found for '{query}' in Apple Music catalog")
        raise SystemExit(1)

    if len(results) == 1:
        track_url, display = results[0]
    else:
        click.echo(f"Found {len(results)} results in Apple Music:")
        result = select_item(results, "Select a song")
        if result is None:
            if not is_non_interactive():
                click.echo("Cancelled")
            raise SystemExit(1)
        track_url = result
        display = next(d for u, d in results if u == track_url)

    click.echo(f"Opening in Apple Music: {display}")
    if not client.open_catalog_track(track_url):
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
