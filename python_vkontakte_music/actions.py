import os
import tools


class Music(tools.ActionBase):
    action_name = 'music'


class MusicList(Music):
    subaction_required = False
    action_name = 'list'

    def run(self, print_part=None, *args, **kwargs):
        self.process_id_argument(kwargs)
        for audio in self.list_items('audio.get', **kwargs):
            tools.print_audio(audio, print_part)

    def apply_arguments(self, parser):
        self.add_print_part_argument(parser, 'audio', 'id', 'name', 'url')
        self.add_limit_argument(parser, 'audios', 'show')
        self.add_id_argument(parser, 'audio', 'show')
        parser.add_argument('--album_id', type=int, help='List audios in album.')


class MusicListAlbum(MusicList):
    action_name = 'album'

    def run(self, print_part=None, *args, **kwargs):
        for album in self.list_items('audio.getAlbums', **kwargs):
            tools.print_album(album, print_part)

    def apply_arguments(self, parser):
        self.add_print_part_argument(parser, 'album', 'id', 'title')
        self.add_limit_argument(parser, 'albums', 'show')


class MusicDownload(Music):
    action_name = 'download'

    def run(self, interactive=False, skip_error=False, skip_exists=False, destination=None, *args, **kwargs):
        self.process_id_argument(kwargs)
        for audio in self.list_items('audio.get', **kwargs):
            if skip_exists and os.path.exists(tools.make_full_audio_filename(audio, destination)):
                continue
            if interactive and not tools.ask('Download '+ tools.format_audio(audio, print_part='name')):
                continue
            try:
                tools.download_audio(audio, destination)
            except Exception as e:
                if skip_error:
                    print('Error:', e)
                    continue
                else:
                    raise

    def apply_arguments(self, parser):
        self.add_limit_argument(parser, 'audios', 'download')
        self.add_id_argument(parser, 'audio', 'download')
        parser.add_argument('--interactive', action='store_true', help='Download audios interactively.')
        parser.add_argument('--album_id', type=int, help='Download audios from album.')
        parser.add_argument('--skip_error', action='store_true', help='Continue download if an error occurred.')
        parser.add_argument('--skip_exists', action='store_true', help='Do not download existing audios.')
        parser.add_argument('--destination', type=tools.directory_type, help='Directory where to store downloads.')


class MusicSearch(Music):
    action_name = 'search'

    def run(self, print_part=None, *args, **kwargs):
        kwargs['search_own'] = int(kwargs.get('search_own', False))
        kwargs['count'] = kwargs.pop('limit', 100)
        kwargs['q'] = kwargs.pop('query')
        for audio in self.client.call('audio.search', **kwargs)['items']:
            tools.print_audio(audio, print_part)


    def apply_arguments(self, parser):
        self.add_print_part_argument(parser, 'audio', 'id', 'name', 'url')
        self.add_limit_argument(parser, 'audios', 'show')
        parser.add_argument('--search_own', action='store_true', help='Search in own audios.')
        parser.add_argument('query', type=str, help='Search query.')
