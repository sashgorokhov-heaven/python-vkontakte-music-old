import tools


def music_list(client, print_part, album_id, limit, **kwargs):
    for item in tools.list_items(client, 'audio.get')[:limit]:
        tools.print_audio(item, print_part)


def music_download_interactive(client, album_id, limit, **kwargs):
    for audio in tools.list_items(client, 'audio.get')[:limit]:
        if tools.ask('Download '+ tools.format_audio(audio, print_part='name')):
            tools.download_audio(audio)


def music_list_album(client, print_part, **kwargs):
    for album in tools.list_items(client, 'audio.getAlbums'):
        tools.print_album(album, print_part)