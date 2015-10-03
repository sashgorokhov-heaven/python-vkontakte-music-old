import os
import tools
import vkontakte
import actions


def _get_arguments():
    import argparse

    def directory(path):
        if os.path.exists(path):
            if os.path.isdir(path):
                return path
            else:
                raise argparse.ArgumentTypeError('%s is not a directory' % path)
        else:
            raise argparse.ArgumentTypeError('%s not found' % path)

    parser = argparse.ArgumentParser('Python Vkontakte Music Downloader')

    group = parser.add_argument_group(title='Use credentials from file')
    group.add_argument('-c', '--credentials', type=argparse.FileType('r'), help='Credentials file')

    group = parser.add_argument_group(title='User credentials from options')
    group.add_argument('-l', '--login', help='User login (email or phone number).')
    group.add_argument('-p', '--pass', help='User password.')

    parser.add_argument('-V', '--version', help='Which API version to use. Default is 5.37.', default='5.37')
    actions_subparsers = parser.add_subparsers(title='Available actions', dest='action')

    music_parser = actions_subparsers.add_parser('music')
    music_subparsers = music_parser.add_subparsers(title='Available actions', dest='action_command')

    music_list_parser = music_subparsers.add_parser('list')
    music_list_parser.add_argument('--print_part', choices=['id', 'name', 'url', 'id+url', 'id+name', 'name+url'], help='Which audio part to show.')
    music_list_parser.add_argument('--album_id', type=int, help='List audios in album.')
    music_list_parser.add_argument('--limit', type=int, help='Show only first N audios.')
    group = music_list_parser.add_mutually_exclusive_group()
    group.add_argument('--id_file', type=argparse.FileType('r'), help='File with list of audio ids to show.')
    group.add_argument('--id', type=int, nargs='+', help='List of audio ids to show.')

    music_download_interactive_parser = music_subparsers.add_parser('download_interactive')
    music_download_interactive_parser.add_argument('--album_id', type=int, help='Download audios in album.')
    music_download_interactive_parser.add_argument('--limit', type=int, help='Download only first N audios.')
    music_download_interactive_parser.add_argument('--skip_error', action='store_true', help='Continue download if an error occurred.')
    music_download_interactive_parser.add_argument('--destination', type=directory, help='Where to store downloads.')

    music_album_list_parser = music_subparsers.add_parser('list_album')
    music_album_list_parser.add_argument('--print_part', choices=['id', 'name', 'id+name'], help='Which album part to show.')

    music_download_parser = music_subparsers.add_parser('download')
    music_download_parser.add_argument('--album_id', type=int, help='Download audios in album.')
    music_download_parser.add_argument('--limit', type=int, help='Download only first N audios.')
    music_download_parser.add_argument('--skip_error', action='store_true', help='Continue download if an error occurred.')
    music_download_parser.add_argument('--destination', type=directory, help='Directory where to store downloads.')
    group = music_download_parser.add_mutually_exclusive_group()
    group.add_argument('--id_file', type=argparse.FileType('r'), help='File with list of audio ids to download.')
    group.add_argument('--id', type=int, nargs='+', help='List of audio ids to download.')

    music_search_parser = music_subparsers.add_parser('search')
    music_search_parser.add_argument('query', type=str, help='Search query.')
    music_search_parser.add_argument('--search_own', action='store_true', help='Search in own audios.')
    music_search_parser.add_argument('--print_part', choices=['id', 'name', 'url', 'id+url', 'id+name', 'name+url'], help='Which audio part to show.')

    args = vars(parser.parse_args())
    nocreds_message = 'Specify ether login and password, or credentials file only.'
    if (args['credentials'] and (args['login'] or args['pass'])) or (not args['credentials'] and not (args['login'] or args['pass'])):
        parser.error(nocreds_message)

    action_func_name = args['action'] + '_' + args['action_command']
    if not hasattr(actions, action_func_name):
        parser.error(action_func_name + ' action not found.')
    args['action_func_name'] = action_func_name

    if args['credentials']:
        args['login'], args['pass'] = list(args['credentials'])

    try:
        args['access_token'] = tools.get_access_token(args['login'], args['pass'])
    except tools.CredentialsError:
        parser.error('Invalid login or password')
    args['client'] = vkontakte.VkontakteClient(args['access_token'], args['version'])

    return args


def _run_action(action_func_name, **kwargs):
    return getattr(actions, action_func_name)(**kwargs)


def main():
    args = _get_arguments()
    _run_action(**args)


if __name__ == '__main__':
    main()