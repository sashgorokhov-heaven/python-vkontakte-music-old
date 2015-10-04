def main():
    import argparse
    import tools, actions, vkontakte

    parser = argparse.ArgumentParser('Python Vkontakte Music Downloader')
    tools.ActionBase(parser)
    args = vars(parser.parse_args())

    nocreds_message = 'Specify ether login and password, or credentials file only.'
    if (args['credentials'] and (args['login'] or args['pass'])) or (not args['credentials'] and not (args['login'] or args['pass'])):
        parser.error(nocreds_message)

    if args['credentials']:
        args['login'], args['pass'] = list(args.pop('credentials'))

    try:
        args['access_token'] = tools.get_access_token(args.pop('login'), args.pop('pass'))
    except tools.CredentialsError:
        parser.error('Invalid login or password')

    action = args.pop('action_instance')
    action_name = args.pop('action')
    action.client = vkontakte.VkontakteClient(args.pop('access_token'), args.pop('version'))

    return action.run(**args)

if __name__ == '__main__':
    main()