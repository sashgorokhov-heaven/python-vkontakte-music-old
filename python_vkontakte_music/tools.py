from __future__ import print_function

import os
import vkontakte
import string
import urllib


ACCESS_TOKEN_FILENAME = '.access_token'
APPLICATION_ID = '5091851'
SCOPE = ['audio']


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


def format_audio(audio_item, name_only=False, url_only=False):
    """
    Print audio item.

    :param dict audio_item: dict describing one audio
    :param bool only_url: print only audio url. Default False.
    :param bool valid_name: print with valid audio name as filename. Default True.
    """
    line = ''
    if not url_only:
        line += make_audio_name(audio_item['artist'], audio_item['title'])
    if not name_only:
        line += ('  ' if not url_only else '') + audio_item['url']
    return line


def print_audio(audio_item, name_only=False, url_only=False):
    print(format_audio(audio_item, name_only, url_only))


def ask(message):
    if not message.endswith('?'):
        message += ' ?'
    message += ' Y/N: '
    while True:
        inp = raw_input(message).lower()
        if inp == 'y':
            return True
        elif inp == 'n' or inp == '':
            return False
        else:
            print('Invalid character.')


def list_items(client, method, **kwargs):
    return client.call(method, **kwargs)['items']


class Downloader:
    def __init__(self, filename, url):
        self.filename = filename
        self.url = url

    def format_filename(self):
        if len(self.filename) > 50:
            return self.filename[:48] + '...'
        return self.filename

    def _reporthook(self, transfered, block_size, total_size):
        p = round(((float(transfered)*float(block_size))/float(total_size)) * 100.0, 1)
        print('Downloading {}: {}%'.format(self.format_filename(), p), end='\r')

    def start(self):
        urllib.urlretrieve(self.url, self.filename, reporthook=self._reporthook)
        print()


def download(audio):
    filename = make_audio_name(audio['artist'], audio['title']) + '.mp3'
    Downloader(filename, audio['url']).start()