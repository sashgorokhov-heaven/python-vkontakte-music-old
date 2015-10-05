from __future__ import print_function
import argparse

import os
import requests
import string
import urllib
from urllib.request import urlretrieve
import vkontakte


ACCESS_TOKEN_FILENAME = '.access_token'
APPLICATION_ID = '5091851'
SCOPE = ['audio', 'groups', 'friends']


class CredentialsError(Exception): pass


def check_access_token_file():
    if os.path.exists(ACCESS_TOKEN_FILENAME):
        with open(ACCESS_TOKEN_FILENAME, 'r') as f:
            access_token = f.read()
            try:
                vkontakte.VkontakteClient(access_token).call('audio.get')
            except:
                return None
            else:
                return access_token
    else:
        return None


def save_access_token_file(access_token):
    with open(ACCESS_TOKEN_FILENAME, 'w') as f:
        f.write(access_token)


def retrieve_access_token(login, password):
    try:
        return vkontakte.auth(login, password, APPLICATION_ID, SCOPE)[0]
    except:
        raise CredentialsError('Invalid login or password.')


def get_access_token(login, password):
    access_token = check_access_token_file()
    if not access_token:
        access_token = retrieve_access_token(login, password)
        save_access_token_file(access_token)
    return access_token


class ActionBase(object):
    subaction_required = True
    action_name = None

    def __init__(self, parser):
        # apply arguments only if function was defined in class (do not use parents apply_arguments)
        if 'apply_arguments' in self.__class__.__dict__:
            self.apply_arguments(parser)
        subactions = self.get_subactions()
        if subactions:
            subparsers = parser.add_subparsers(title='Available actions')
            if self.subaction_required:
                subparsers.dest = 'action'
                subparsers.required = True
            for action_class in subactions:
                parser = subparsers.add_parser(action_class.action_name)
                action = action_class(parser)
                parser.set_defaults(action_instance=action)

    @classmethod
    def get_subactions(cls):
        return cls.__subclasses__()

    def apply_arguments(self, parser):
        """
        Add arguments to action's parser.

        :param argparse.ArgumentParser parser: parser for this action.
        """
        group = parser.add_argument_group(title='Use credentials from file')
        group.add_argument('-c', '--credentials', type=argparse.FileType('r'), help='Credentials file')

        group = parser.add_argument_group(title='User credentials from options')
        group.add_argument('-l', '--login', help='User login (email or phone number).')
        group.add_argument('-p', '--pass', help='User password.')

        parser.add_argument('-V', '--version', help='Which API version to use. Default is 5.37.', default='5.37')

    def add_print_part_argument(self, parser, what, *choices):
        additional = list()
        choices = list(choices)
        for n, item in enumerate(choices, 1):
            for other in choices[n:]:
                additional.append(item+'+'+other)
        choices += additional
        parser.add_argument('--print_part', choices=choices, help='Which %s part to show.' % what)

    def add_limit_argument(self, parser, what, action):
        parser.add_argument('--limit', type=int, help='%s only first N %s.' % (action.capitalize(), what))

    def add_id_argument(self, parser, what, action):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--id_file', type=argparse.FileType('r'), help='File with list of %s ids to %s.' % (what, action))
        group.add_argument('--id', type=int, nargs='+', help='List of %s ids to %s.' % (what, action))

    def run(self, *args, **kwargs):
        print(self.__class__.__name__, args, kwargs)

    def list_items(self, method, limit=None, run_full=True,  **kwargs):
        """Get a full list of items"""
        kwargs['count'] = 100
        if limit and limit < kwargs['count']:
            kwargs['count'] = limit
        first = self.client.call(method, **kwargs)
        total = first['count']
        offset = len(first['items'])
        n = 0
        items = first['items']
        while offset <= total:
            for item in items:
                if limit and n == limit:
                    raise StopIteration()
                yield item
                n += 1
            if not run_full:
                raise StopIteration()
            if offset == total:
                raise StopIteration()
            kwargs['offset'] = offset
            items = self.client.call(method, **kwargs)['items']
            offset += len(items)

    def process_id_argument(self, kwargs):
        if kwargs.get('id_file', None):
            kwargs['id'] = from_ids_file(kwargs.pop('id_file'))
        id = kwargs.pop('id', None)
        if id:
            kwargs['audio_ids'] = ','.join(map(str, id))


def filter_text(text):
    """Remove invalid symbols from string"""
    return ''.join(c if c in string.printable else '?' for c in text.strip())


def filter_audio_name(artist, title):
    """Return valid artist and title for saving as filename"""
    return list(map(filter_text, (artist[:175], title[:175])))


def make_audio_name(artist, title, valid_name=True, sep='-'):
    """
    Create audio name.

    :param bool valid_name: print with valid audio name as filename. Default True.
    :param str sep: artist and title separator. Default "-".
    :return str: formatted audio name.
    """
    if valid_name:
        artist, title = filter_audio_name(artist, title)
    return artist + ' %s ' % sep + title


def print_part_format(d, config, print_part=None):
    """
    :param dict d: item dict.
    :param list config: print config.
    :param str print_part: which part from config to add to formatted string.
    :return str: formatted string.
    """
    config_dict = dict()
    keys_list = list()
    for config_item in config:
        key = list(config_item)[0]
        config_dict[key] = config_item[key]
        keys_list.append(key)
    if print_part is not None:
        print_part = set(print_part.split('+'))
    else:
        print_part = set(config_dict)
    format = list()
    for key in keys_list:
        if key in print_part:
            if 'getter' in config_dict[key]:
                value = config_dict[key]['getter'](d)
            else:
                value = d[config_dict[key].get('key', key)]
            value = config_dict[key].get('format', str)(value)
            format.append(value)
    return '  '.join(format)


def format_audio(audio, print_part=None):
    """
    Format audio.

    :param dict audio: dict describing one audio.
    :param str print_part: id, name, or url. Which part of audio to print. Default is None (print all).
    """
    return print_part_format(audio, [
        {'id': {}},
        {'name': {'getter': lambda d: make_audio_name(d['artist'], d['title'])}},
        {'url': {}}
    ], print_part)


def print_audio(audio, print_part=None):
    """Just format and print an audio"""
    print(format_audio(audio, print_part))


def format_album(album, print_part=None):
    """
    Format album.

    :param dict album: dict describing one album.
    :param str print_part: id, or name. Which part of album to print. Default is None (print all).
    """
    return print_part_format(album, [
        {'id': {}},
        {'title': {'format': filter_text}}
    ], print_part)


def print_album(album, print_part=None):
    """Just format and print an album"""
    print(format_album(album, print_part))


def format_group(group, print_part=None):
    """
    Format group.

    :param dict group: dict describing one group.
    :param print_part:  id or name. Which part of group to print. Default is None (print all).
    """
    return print_part_format(group, [
        {'id': {}},
        {'name': {'format': filter_text}}
    ])


def print_group(group, print_part=None):
    """Just format and print group"""
    print(format_group(group, print_part))


def format_friend(friend, print_part=None):
    """
    Format group.

    :param dict friend: dict describing one friend.
    :param print_part:  id or name. Which part of friend to print. Default is None (print all).
    """
    return print_part_format(friend, [
        {'id': {}},
        {'name': {'getter': lambda d: filter_text(d['first_name']+ ' '+d['last_name'])}}
    ])


def print_friend(friend, print_part=None):
    """Just format and print friend"""
    print(format_friend(friend, print_part))


def ask(message):
    """Ask user a question"""
    if not message.endswith('?'):
        message += ' ?'
    message += ' Y/N: '
    while True:
        inp = input(message).lower()
        if inp == 'y':
            return True
        elif inp == 'n' or inp == '':
            return False
        else:
            print('Invalid character.')


class Downloader:
    def __init__(self, filename, url, with_reporthook=False):
        self.filename = filename
        self.url = url
        self.with_reporthook = with_reporthook

    def format_filename(self):
        if len(self.filename) > 50:
            return self.filename[:48] + '...'
        return self.filename

    def _reporthook(self, transfered, block_size, total_size):
        p = round(((float(transfered)*float(block_size))/float(total_size)) * 100.0, 1)
        print('Downloading {}: {}%'.format(self.format_filename(), p), end='\r')

    def start(self):
        if self.with_reporthook:
            urlretrieve(self.url, self.filename, reporthook=self._reporthook)
        else:
            urlretrieve(self.url, self.filename)
        print()


def download_raw(url, filename, reporthook=None, chunk_size=1024,):
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for n, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
            if chunk:
                f.write(chunk)
                f.flush()
            if reporthook:
                reporthook(n, chunk_size, int(r.headers.get('content-length', 1)))


def from_ids_file(id_file):
    for line in id_file:
        line = line.strip()
        if line:
            yield int(line)


def directory_type(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise argparse.ArgumentTypeError('%s is not a directory' % path)
    else:
        raise argparse.ArgumentTypeError('%s not found' % path)


def make_full_audio_filename(audio, destination=None):
    filename = make_audio_name(audio['artist'], audio['title']) + '.mp3'
    if destination:
        return os.path.join(destination, filename)
    return filename


def download_audio(audio, destination=None):
    filename = make_full_audio_filename(audio, destination)
    Downloader(filename, audio['url'], with_reporthook=True).start()