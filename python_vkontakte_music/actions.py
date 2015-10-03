import tools


def music_list(client, print_part, album_id, limit, id, id_file, **kwargs):
    if id or id_file:
        if id_file:
            id = tools.from_ids_file(id_file)
        iterator = tools.list_items(client, 'audio.get', limit, run_full=False, album_id=album_id, audio_ids=','.join(map(str, id)))
    else:
        iterator = tools.list_items(client, 'audio.get', limit, album_id=album_id)

    for item in iterator:
        tools.print_audio(item, print_part)


def music_download_interactive(client, album_id, limit, destination, skip_error, **kwargs):
    iterator = tools.list_items(client, 'audio.get', limit, album_id=album_id)

    for audio in iterator:
        if tools.ask('Download '+ tools.format_audio(audio, print_part='name')):
            try:
                tools.download_audio(audio, destination)
            except Exception as e:
                if skip_error:
                    print('Error:', e)
                    continue
                else:
                    raise


def music_download(client, album_id, limit, destination, skip_error, id, id_file, **kwargs):
    if id or id_file:
        if id_file:
            id = tools.from_ids_file(id_file)
        iterator = tools.list_items(client, 'audio.get', limit, run_full=False, album_id=album_id, audio_ids=','.join(map(str, id)))
    else:
        iterator = tools.list_items(client, 'audio.get', limit, album_id=album_id)

    for audio in iterator:
        try:
            tools.download_audio(audio, destination)
        except Exception as e:
            if skip_error:
                print('Error:', e)
                continue
            else:
                raise


def music_search(client, query, search_own, print_part, **kwargs):
    items = client.call('audio.search', q=query, search_own=int(search_own))
    for item in items['items']:
        tools.print_audio(item, print_part)


def music_list_album(client, print_part, **kwargs):
    for album in tools.list_items(client, 'audio.getAlbums'):
        tools.print_album(album, print_part)