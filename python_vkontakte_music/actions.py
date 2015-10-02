import tools


def music_list(client, print_part, **kwargs):
    for item in tools.list_items(client, 'audio.get'):
        tools.print_audio(item, print_part)


def music_download_interactive(client, **kwargs):
    for audio in tools.list_items(client, 'audio.get'):
        if tools.ask('Download '+ tools.format_audio(audio, name_only=True)):
            tools.download_audio(audio)