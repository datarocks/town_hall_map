from __future__ import print_function
import httplib2
import os
import pickle
from copy import deepcopy
from pprint import pprint

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from requests import get

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from local_config import config

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'local_config/client_secret.json'
APPLICATION_NAME = 'Google Sheets API Python Quickstart'

# this is for pickling a cached response...it isn't in use quite yet



def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def geocode_address(address):
    geocoding_url = "https://open.mapquestapi.com/geocoding/v1/address"
    params = {'key': config.MAPQUEST_KEY, 'thumbMaps': 'false', 'location': address}
    geocode_response = get(geocoding_url, params=params)
    full_response = geocode_response.json()
    return full_response

def get_townhall_data():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1yq1NT9DZ2z3B8ixhid894e77u9rN5XIgOwWtTW72IYA'
    rangeName = 'Upcoming Events!C11:P16'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    town_hall_list = []
    address_list = []
    if not values:
        print('No data found.')
    else:
        keys = values[0]
        keys[2] = u'State Represented'
        del values[0]
        for town_hall_data in values:
            town_hall = dict(zip(keys, town_hall_data))
            if town_hall[u'City'] and town_hall[u'State']:
                address_string = town_hall[u'Street Address'] + u', ' + town_hall[u'City'] + u', ' + \
                                           town_hall[u'State'] + u' ' + town_hall[u'Zip']
                town_hall[u'address_string'] = address_string
            else:
                town_hall[u'address_string'] = None
            print(address_string)
            if address_string and address_string not in address_list:
                address_list.append(address_string)
            town_hall_list.append(town_hall)
    return [town_hall_list, address_list]


def generate_geocode_dictionary(address_list, cached_geocode_dict=None):
    if cached_geocode_dict:
        geocode_dictionary = cached_geocode_dict
    else:
        geocode_dictionary = {}
    for address in address_list:
        if address not in geocode_dictionary.keys():
            geocode_response = geocode_address(address)
            geocode_dictionary[address] = geocode_response
    return geocode_dictionary


def append_lat_long_to_townhall_data(town_hall_list, geocode_dict):
    geo_town_hall_list = deepcopy(town_hall_list)
    for town_hall in geo_town_hall_list:
        if town_hall.get(u'address_string'):
            address = town_hall.get(u'address_string')
            geo = geocode_dict.get(address)
            lat_lng = geo.get('results')[0].get('locations', {})[0].get(u'latLng')
            town_hall[u'lat_lng'] = lat_lng
        else:
            town_hall[u'lat_lng'] = None
    return geo_town_hall_list





def main():
    town_hall_list, address_list = get_townhall_data()
    try:
        pkl_file = open('data.pkl', 'rb')
        cached_geocode_dict = pickle.load(pkl_file)
        print('success?')
        pkl_file.close()
    except IOError:
        print('no file yet')
        cached_geocode_dict = None
    geocode_dict = generate_geocode_dictionary(address_list, cached_geocode_dict)
    output = open('data.pkl', 'wb')
    pickle.dump(geocode_dict, output, -1)
    output.close()
    geo_town_hall_list = append_lat_long_to_townhall_data(town_hall_list, geocode_dict)
    pprint(geo_town_hall_list)





if __name__ == '__main__':
    main()
