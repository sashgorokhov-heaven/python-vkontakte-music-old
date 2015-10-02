from distutils.core import setup

setup(
    requires=['requests'],
    name='python-vkontakte-music',
    version='0.1',
    packages=['python_vkontakte_music'],
    url='',
    license='',
    author='Alexander Gorokhov',
    author_email='sashgorokhov@gmail.com',
    description='Download your vkontakte music by this command line tool with ease.',
    entry_points={'console_scripts':['pyvkmusic = python_vkontakte_music:main']},
)
