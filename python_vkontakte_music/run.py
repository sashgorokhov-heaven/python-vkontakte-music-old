import tools
import vkontakte
import actions


def _get_arguments():
    import argparse

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

    music_download_interactive_parser = music_subparsers.add_parser('download_interactive')
    music_album_list_parser = music_subparsers.add_parser('list_album')
    music_album_list_parser.add_argument('--print_part', choices=['id', 'name', 'id+name'], help='Which album part to show.')

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