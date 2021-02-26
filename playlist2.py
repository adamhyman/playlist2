#  Add two features to your playlist program
#  For Marie Tsaasan
#  By Adam Hyman, Kevin Sim, Van Nguyen
#  Python at Orange Coast - CS231-42100


#  For this assignment, we added a few additional features:
#  1.  Songs can be either files or a website address, like youtube
#  2.  Added option to play randomized songs, for a length of time that the user
#      specifies
#  3.  On startup, the program checks to see if the music files are in the same
#      folder as the playlist file.  If not, it offers to download them
#  4.  Has the option to view the playlist
#  5.  Has "Playlists", which are stored on each users computer.
#      Playlists contain a list of songs.
#      Playlists can be created and deleted, but not modified at the moment.
#  6.  The program uses a settings file to track the number of songs and total
#      listening time, for that computer

from terminusdb_client.woqlclient.woqlClient import WOQLClient
from terminusdb_client.woqlquery.woql_query import WOQLQuery as WQ
from playsound import playsound
import webbrowser
import random
from os import path
import time
from urllib import request
from configparser import ConfigParser

# data base information
server_url = 'https://127.0.0.1:6363'
description = 'A songs database storing information about the artist, song ' \
              'title, song length and the album'
user = 'admin'
account = 'admin'
key = 'root'
db = 'music_playlist2'

# WOQL client
client = WOQLClient(server_url)
client.connect(user=user, account=account, key=key, db=db)

MAIN_MENU = ('\n'
             '---------------------------\n'
             '|        MAIN MENU        |\n'
             '---------------------------\n'
             '1.  View song list\n'
             '2.  Play a song\n'
             '3.  Play randomized songs\n'
             '4.  Add song\n'
             '5.  Edit song\n'
             '6.  Playlists\n'
             '7.  View stats\n'
             '8.  Exit\n'
             )

PLAYLIST_MENU = ('\n'
             '---------------------------\n'
             '|      PLAYLIST MENU      |\n'
             '---------------------------\n'
             '1.  View playlists\n'
             '2.  Play a playlist\n'
             '3.  Add playlist\n'
             '4.  Delete playlist\n'
             '5.  Exit\n'
             )



def create_schema() -> None:
    '''
    Create Schema for the playlist data base, no harm to adding repeatedly as
    it is idempotent
    '''

    schema = WQ().woql_and(
        WQ().doctype("scm:Song", label="Song")
            .description("A playlist that contains songs")
            .property("scm:title", "xsd:string")
            .property("scm:album", "xsd:string")
            .property("scm:artist", "xsd:string")
            .property("scm:length", "xsd:integer")
            .property("scm:location", "xsd:string")
    )
    return schema.execute(client, "Adding Song Class to schema")

def number_of_songs() -> int:
    '''  Returns the number of songs in the database  '''
    song_query = WQ().triple("v:X", "scm:title", "v:Y").execute(client)
    number_of_songs = len(song_query["bindings"])
    return number_of_songs

def view_songs() -> None:
    '''
    Prints the list of all songs
    '''

    print('')
    #           1234567890123456789012345 1234567890123456789012345 12345678901234567890 123456789 12345678901234567890123456789012345678901234
    print('ID   Title                     Album                     Artist               Length    Location              ')
    print('-------------------------------------------------------------------------------------------------------------------------------')

    for song in range(1, number_of_songs() + 1):

        mysong = get_song(str(song))
        print(str(song).ljust(4), mysong['title'].ljust(25)[:25],
              mysong['album'].ljust(25)[:25], mysong['artist'].ljust(20)[:20],
              str(mysong['length']).ljust(9)[:9], str(mysong['location']).ljust(44)[:44])


def play_user_specified_song(settings) -> None:
    '''
    Prompts user for the song number, then plays it.

    If the location is a file, it plays the file.
    If the location is a web address, it opens that address.
    '''
    song_num = input('Enter the song number that you want to play  (Enter to exit):  ')
    while (song_num != ''):
        play_song(settings, song_num)

        song_num = input('Enter the song number that you want to play  (Enter to exit):  ')

def play_song(settings, song_num: str) -> dict:
    '''
    Plays the song, increments the settings' counters, returns the song (dict) that was played
    '''
    song = get_song(song_num)

    settings['main']['songs_played'] = str(int(settings['main']['songs_played']) + 1)
    settings['main']['time_played'] = str(int(settings['main']['time_played']) + song['length'])

    if path.exists(song['location']):
        playsound(song['location'])
    else:
        webbrowser.open(song['location'])
        time.sleep(song['length'] + 3)

    return song

def play_randomized_songs(settings) -> None:
    '''
    Plays random songs for a user specified amount of time
    '''
    min_to_play_for = int(input('Enter number of minutes to play random songs for:  '))

    num_songs = number_of_songs()

    time_played = 0

    while (time_played < min_to_play_for * 60):
        song = play_song(settings, str(random.randint(1, num_songs)))
        time_played += song['length']

def add_song(title='', album='', artist='', length=0, location='') -> None:
    '''
    Adds a song to database, either with variables passed to it
    or prompts user to enter song title, album, artist, length, location
    '''

    if title == ''   : title = input("Enter song's title:  ")
    if album == ''   : album = input("Enter song's album name:  ")
    if artist == ''  : artist = input("Enter artist's name:  ")
    if length == 0   : length = int(input("Enter song's length in seconds:  "))
    if location == '': location = input("Enter location (filename or web address):  ")

    #  Because the string can't have a ':'
    if location.upper()[:7] == 'HTTP://':
        location = location[7:]
    elif location.upper()[:8] == 'HTTPS://':
        location = location[8:]

    # Inserts new song
    WQ().woql_and(
        WQ().insert(f"doc:{number_of_songs() + 1}", "scm:Song")
            .property("scm:title", title)
            .property("scm:album", album)
            .property("scm:artist", artist)
            .property("scm:length", length)
            .property("scm:location", location)
    ).execute(client, f"Insert song {number_of_songs()} from python")


def edit_song() -> None:
    '''
    Allows user to edit a song's attributes.
    '''
    song_id = input("Enter song's id: ")
    song = get_song('terminusdb:///data/' + song_id)

    print('')
    print('Song ' + song_id)
    print('1.  Title:     ' + song['title'])
    print('2.  Album:     ' + song['album'])
    print('3.  Artist:    ' + song['artist'])
    print('4.  Length:    ' + str(song['length']))
    print('5.  Location:  ' + song['location'])
    print('')

    item_to_edit = '1'
    while item_to_edit in ['1', '2', '3', '4', '5']:

        item_to_edit = input('Enter the number of the item that you wish to edit (Enter to exit):  ')
        if item_to_edit == '':
            break

        item = ['0', 'title', 'album', 'artist', 'length', 'location'][int(item_to_edit)]

        new_value = input('Input new ' + item + ':  ')
        print ('')

        #  Because length is the only attribute of a song that is an int.  The rest are str.
        if item == 'length':
           new_value = int(new_value)

        #  Because the location can't have a ':'
        if item == 'location':
            if new_value.upper()[:7] == 'HTTP://':
                new_value = new_value[7:]
            elif new_value.upper()[:8] == 'HTTPS://':
                new_value = new_value[8:]

        WQ().woql_and(
            WQ().triple("doc:" + song_id, "scm:" + item, "v:Title"),
            WQ().delete_triple("doc:" + song_id, "scm:" + item, "v:Title"),
            WQ().add_triple("doc:" + song_id, "scm:" + item, new_value),
        ).execute(client, "Updated the " + str(new_value))



def get_song(item: str) -> dict:
    '''
    Gets a song from the database
    Returns dict, with key's:  myid, title, album, artist, length
    '''
    data_query = WQ().triple(item, 'v:P', 'v:Y').execute(client)

    song = dict()

    song['myid'] = item[19:]
    song['myid'] = item
    for i in data_query["bindings"]:
        if i['P'] == 'terminusdb:///schema#title':
            song['title'] = i['Y']['@value']
        if i['P'] == 'terminusdb:///schema#album':
            song['album'] = i['Y']['@value']
        if i['P'] == 'terminusdb:///schema#artist':
            song['artist'] = i['Y']['@value']
        if i['P'] == 'terminusdb:///schema#length':
            song['length'] = i['Y']['@value']
        if i['P'] == 'terminusdb:///schema#location':
            song['location'] = i['Y']['@value']

    return song

def check_audio_files() -> None:
    '''
    Checks the audio files are on the computer that is running this program.
    Offers to download them if necessary.
    '''
    songs = ['Ezra - ABC Song.mp3',
             'Ezra - Happy Birthday.mp3',
             'Ezra - This Land is Your Land.mp3',
             'Ezra - ABC Gummy Bears.mp3',
             'Noah - Star Spangled Banner.mp3']

    for song in songs:
        if not(path.exists(song)):
            download = input('Song ' + song + ' is not available on this computer.  Download it?  (Y/N)  ')
            if download.upper() == 'Y':
                url = 'https://adamhyman-public.s3-us-west-2.amazonaws.com/' + song
                url = url.replace(' ', '%20')
                request.urlretrieve(url, song)


def initialize_settings() -> ConfigParser:
    '''  Gets settings from config.ini and returns settings in a ConfigParser object  '''
    config = ConfigParser()
    config.optionxform = str       #  Sets config to be case senstive
    config.read('config.ini')
    if 'playlists' not in config:
        config['playlists'] = {}
    if 'main' not in config:
        config['main'] = {}
        config['main']['songs_played'] = '0'
        config['main']['time_played'] = '0'
    return config



def play_playlist(settings) -> None:
    '''
    Asks user which number playlist they want to play and for how long,
    then plays it!
    '''
    playlist_num = int(input('Enter the playlist number that you want to play:  '))
    min_to_play_for = int(input('Enter number of minutes to play playlist for:  '))
    for index, key in enumerate(settings['playlists'], start=1):
        if index == playlist_num:
            songs = settings['playlists'][key].split()

    time_played = 0
    while (time_played < min_to_play_for * 60):
        song = play_song(random.choice(songs))
        time_played += song['length']

def view_playlists(settings) -> None:
    '''  Prints playlists from the settings  '''
    if len(settings['playlists']) == 0:
        print ('No saved playlists!')
    else:
        print('\nID  Playlist')
        print('---------------------------------------')
        for index, key in enumerate(settings['playlists'], start=1):
            print(str(index).ljust(4) + key)

def add_playlist(settings) -> None:
    '''  Adds a playlist to the settings  '''
    new_playlist_name = input('Please enter the name of your new playlist:  ')
    songs = []

    finished = False
    while not finished:
        song_num = input('Song number to add (Enter when done):  ')
        if song_num != '':
            songs.append(song_num)
        else:
            finished = True

    songs_string = " ".join(x for x in songs)
    settings['playlists'][new_playlist_name] = songs_string


def delete_playlist(settings) -> None:
    '''  Deletes a playlist from the settings  '''
    playlist_to_delete = int(input('Enter playlist number that you wish to delete (Enter to skip):  '))
    for index, key in enumerate(settings['playlists'], start=1):
        if index == playlist_to_delete:
            settings.remove_option('playlists', key)

def playlists(settings) -> None:
    '''
    Loads the settings from the users computer
    Prints the playlist menu, and lets the user modify playlists
    Saves settings when the function exits
    '''

    option = '1'
    while option in ['1', '2', '3', '4']:
        print (PLAYLIST_MENU)
        option = input('Select between 1 - 5:  ')
        if option == '1':
            view_playlists (settings)
        if option == '2':
            play_playlist(settings)
        if option == '3':
            add_playlist(settings)
        elif option == '4':
            delete_playlist(settings)

def view_stats(settings) -> None:
    '''  Prints the stats (number of songs played, and length of time listened) '''

    sec  = int(settings['main']['time_played'])
    days = sec // 86400
    remainder = sec % 86400
    days2 = str(days) + ' day' + ('s' if days != 1 else '')

    hours = remainder // 3600
    remainder = remainder % 3600
    hours2 = str(hours) + ' hour' + ('s' if hours != 1 else '')

    minutes = remainder // 60
    minutes2 = str(minutes) + ' minute' + ('s' if hours != 1 else '')

    seconds = remainder % 60
    seconds2 = str(seconds) + ' second' + ('s' if seconds != 1 else '')

    print('You have listened to ' + str(settings['main']['songs_played']) + ' songs.')
    print('You have listened for ' + str(days2) + ', ' + str(hours2) + ', ' + str(minutes2) + ' and ' + str(seconds2) + '.')

def main() -> None:
    '''
    Give user the choice between (1) view songlist, (2) play a song,
    (3) play random songs, (4) add a song, (5) edit a song, (6) playlists
    and calls the appropriate function
    '''
    create_schema()
    check_audio_files()
    settings = initialize_settings()

    option = '1'
    while option in ['1', '2', '3', '4', '5', '6', '7']:
        print(MAIN_MENU)
        option = input('Select between 1 - 7:  ')
        if option == '1':
            view_songs()
        if option == '2':
            play_user_specified_song(settings)
        if option == '3':
            play_randomized_songs(settings)
        elif option == '4':
            add_song()
        elif option == '5':
            edit_song()
        elif option == '6':
            playlists(settings)
        elif option == '7':
            view_stats(settings)

    with open('config.ini', 'w') as configfile:
        settings.write(configfile)

    print("Thanks for using this music playing program!")


def test_music_player() -> None:
    '''  Performs assert tests  '''

    #  Test get_settings()
    test_settings = initialize_settings()
    assert 'playlists' in test_settings

    #  Test adding a song
    old_num_songs = number_of_songs()
    add_song(title='aaa',album='bbb',artist='ccc',length=100,location='testfile.mp3')
    new_num_songs = number_of_songs()
    assert new_num_songs - old_num_songs == 1

    #  Check song was added correctly
    test_song = get_song(str(new_num_songs))
    assert test_song['myid'] == str(new_num_songs)
    assert test_song['title'] == 'aaa'
    assert test_song['album'] == 'bbb'
    assert test_song['artist'] == 'ccc'
    assert test_song['length'] == 100
    assert test_song['location'] == 'testfile.mp3'

    #  Delete the song, so no changes are made to the database
    WQ().delete_triple("doc:" + str(new_num_songs), "scm:title", "aaa").execute(client)
    WQ().delete_triple("doc:" + str(new_num_songs), "scm:album", "bbb").execute(client)
    WQ().delete_triple("doc:" + str(new_num_songs), "scm:artist", "ccc").execute(client)
    WQ().delete_triple("doc:" + str(new_num_songs), "scm:length", 100).execute(client)
    WQ().delete_triple("doc:" + str(new_num_songs), "scm:location", 'testfile.mp3').execute(client)
    WQ().delete_object("doc:" + str(new_num_songs))

    #  Test song was deleted
    assert old_num_songs == number_of_songs()

test_music_player()


if __name__ == "__main__":
    main()
