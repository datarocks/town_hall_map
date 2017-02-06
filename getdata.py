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
from geojson import Feature, Point, FeatureCollection, dumps as geojsondumps
import arrow

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


def xstr(s):
    """
    Coerce a nonetype to be an empty string
    :param s:
    :return: a string
    """
    if s is None:
        return ''
    else:
        return str(s)


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

def geocode_address_mapquest(address):
    # geocoding_url = "https://open.mapquestapi.com/geocoding/v1/address" # the data coming out of the open API is less accurate
    geocoding_url = 'http://www.mapquestapi.com/geocoding/v1/address'
    params = {'key': config.MAPQUEST_KEY, 'thumbMaps': 'false', 'location': address}
    geocode_response = get(geocoding_url, params=params)
    full_response = geocode_response.json()
    return full_response


def geocode_address_nominatum(street, city, state, postalcode=None, county=None, country='United States of America'):
    params = {
        'street': street,
        'city': city,
        'county': county,
        'state': state,
        'postalcode': postalcode,
        'country': country,
        'format': 'json',
        'addressdetails': '1'
    }
    geocoding_url = 'https://nominatim.openstreetmap.org/search'
    response = get(geocoding_url, params=params)
    response_content = response.json()
    return response_content




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
            if town_hall.get(u'Street Address') and town_hall.get(u'City') and town_hall.get(u'State'):
                address_string = town_hall.get(u'Street Address').strip() + u', ' + town_hall[u'City'] + u', ' + \
                                           town_hall[u'State'].strip() + u' ' + xstr(town_hall.get(u'Zip'))
                town_hall[u'address_string'] = address_string
            else:
                address_string = None
                town_hall[u'address_string'] = address_string
            print(address_string)
            if address_string and address_string not in address_list:
                address_list.append(address_string)
            town_hall_list.append(town_hall)
            if town_hall.get(u'Party'):
                town_hall[u'Party'] = town_hall[u'Party'].strip()
            if town_hall.get(u'District'):
                town_hall[u'District'] = town_hall[u'District'].strip()
            if town_hall.get(u'State Represented'):
                town_hall[u'State Represented'] = town_hall[u'State Represented'].strip()
            if town_hall.get(u'Date'):
                # dates looks like this: Thursday, February 9, 2017
                print(town_hall[u'Date'])
                split_date = town_hall[u'Date'].split(',')
                if len(split_date) == 3:
                    try:
                        date_string = ' '.join([split_date[1].strip(), split_date[2].strip()])
                        date_8061 = arrow.get(date_string, 'MMMM D YYYY')
                        town_hall[u'date_8061'] = date_8061.format('YYYY-MM-DD')
                        town_hall[u'days_until'] = (date_8061-arrow.now()).days
                        town_hall[u'humanized_date'] = (date_8061.humanize())
                        print((date_8061-arrow.now()).days)
                        print(town_hall[u'humanized_date'])
                    except arrow.parser.ParserError:
                        print("parse error on this date string: "+town_hall[u'Date'])
                        town_hall[u'date_8061'] = None
                else:
                    town_hall[u'date_8061'] = None
                print(town_hall.get(u'date_8061'))
    return [town_hall_list, address_list]


def generate_geocode_dictionary_mapquest(address_list):
    try:
        pkl_file = open('data.pkl', 'rb')
        cached_geocode_dict = pickle.load(pkl_file)
        print('using cached geocoding')
        pkl_file.close()
    except IOError:
        print('no geocoding cache yet, starting from scratch')
        cached_geocode_dict = None
    if cached_geocode_dict:
        geocode_dictionary = cached_geocode_dict
    else:
        geocode_dictionary = {}
    for address in address_list:
        if address not in geocode_dictionary.keys():
            geocode_response = geocode_address_mapquest(address)
            geocode_dictionary[address] = geocode_response
            print('geocoded a thing!')
    output = open('data.pkl', 'wb')
    pickle.dump(geocode_dictionary, output, -1)
    output.close()
    return geocode_dictionary


def generate_geocode_dictionary_nominatum(town_hall_list):
    try:
        pkl_file = open('data_nom.pkl', 'rb')
        cached_geocode_dict = pickle.load(pkl_file)
        print('using cached geocoding')
        pkl_file.close()
    except IOError:
        print('no geocoding cache yet, starting from scratch')
        cached_geocode_dict = None
    if cached_geocode_dict:
        geocode_dictionary = cached_geocode_dict
    else:
        geocode_dictionary = {}
    for town_hall in town_hall_list:
        if town_hall.get(u'address_string') and town_hall.get(u'address_string') not in geocode_dictionary.keys():
            geocode_response = geocode_address_nominatum(street=town_hall.get(u'Street Address'),
                                                         city=town_hall.get(u'City'),
                                                         state=town_hall[u'State'].strip())
            geocode_dictionary[town_hall.get(u'address_string')] = geocode_response
            print(town_hall.get(u'address_string'))
            print(geocode_response)
            print('geocoded a thing!')
    output = open('data_nom.pkl', 'wb')
    pickle.dump(geocode_dictionary, output, -1)
    output.close()
    return geocode_dictionary


def append_lat_long_to_townhall_data_mapquest(town_hall_list, geocode_dict):
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


def append_lat_long_to_townhall_data_nominatum(town_hall_list, geocode_dict):
    geo_town_hall_list = deepcopy(town_hall_list)
    for town_hall in geo_town_hall_list:
        if town_hall.get(u'address_string'):
            address = town_hall.get(u'address_string')
            geo = geocode_dict.get(address)
            print(geo)
            if len(geo) > 0:
                lat_lng = {'lat': float(geo[0]['lat']), 'lng': float(geo[0]['lon'])}
                town_hall[u'lat_lng'] = lat_lng
            else:
                town_hall[u'lat_lng'] = None
        else:
            town_hall[u'lat_lng'] = None
    return geo_town_hall_list


def generate_geojson(geo_town_hall_list):
    feature_list = []
    for town_hall in geo_town_hall_list:
        if town_hall.get(u'lat_lng'):
            lat_lng = town_hall[u'lat_lng']
            point = Point((lat_lng[u'lng'], lat_lng[u'lat']))
            properties = {
                u'date': town_hall.get(u'Date'),
                u'date8061': town_hall.get(u'date_8061'),
                u'district': town_hall.get(u'District'),
                u'location': town_hall.get(u'Location'),
                u'meetingType': town_hall.get(u'Meeting Type'),
                u'member': town_hall.get(u'Member'),
                u'notes': town_hall.get(u'Notes'),
                u'party': town_hall.get(u'Party'),
                u'state': town_hall.get(u'State Represented'),
                u'time': town_hall.get(u'Time')+' '+town_hall.get(u'Time Zone'),
                u'address': town_hall.get(u'address_string')
            }
            feature = Feature(geometry=point, properties=properties)
            feature_list.append(feature)
    feature_collection = FeatureCollection(feature_list)
    return feature_collection



def main():
    town_hall_list, address_list = get_townhall_data()
    geocode_dict = generate_geocode_dictionary_nominatum(town_hall_list)
    geo_town_hall_list = append_lat_long_to_townhall_data_nominatum(town_hall_list, geocode_dict)
    feature_collection = generate_geojson(geo_town_hall_list)
    geojson_string = geojsondumps(feature_collection, sort_keys=True)
    print(geojson_string)





if __name__ == '__main__':
    main()
