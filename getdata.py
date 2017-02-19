from __future__ import print_function
import httplib2
import os
import pickle
from copy import deepcopy
import json
import re
from pprint import pprint

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from requests import get
from geojson import Feature, Point, FeatureCollection, dumps as geojsondumps
import arrow
from smartystreets_python_sdk import StaticCredentials, exceptions
from smartystreets_python_sdk.us_street import ClientBuilder, Lookup

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

from local_config import config
from reconcile import reconciled_addresses

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


def convert_links(value):
    """
    see: https://gist.github.com/guillaumepiot/4539986
    :param value: text that might have urls
    :return: text with hyperlinks
    """
    value = value.replace('https://docs.google.com/forms/d/e/1FAIpQLSdUEg_dMc3PBwogi0RZSAORVhvb98keOevkcqIrR4eplcRuGA/viewform', 'https://goo.gl/g2oSqa')
    # Replace url to link
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)

    # Replace email to mailto
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value


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


def geocode_address_nominatum(street, city, state, address_string, postalcode=None, county=None, country=None):
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
    if len(response_content) == 0:
        print("no nominatum response for: " + address_string)
        return None
    else:
        return response_content


def get_townhall_data():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)

    spreadsheetId = '1yq1NT9DZ2z3B8ixhid894e77u9rN5XIgOwWtTW72IYA'
    rangeName = 'Upcoming Events!C11:R'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])
    town_hall_list = []
    address_list = []
    if not values:
        print('No data found.')
    else:
        keys = values[0]
        pprint(keys)
        keys[2] = u'State Represented'
        del values[0]
        for town_hall_data in values:
            town_hall = dict(zip(keys, town_hall_data))
            if town_hall.get(u'Street Address') and town_hall.get(u'City') and town_hall.get(u'State'):
                address_string = town_hall.get(u'Street Address').strip() + u', ' + xstr(town_hall.get(u'City')).strip()\
                                 + u', ' + town_hall[u'State'].strip() + u' ' + xstr(town_hall.get(u'Zip')).strip()
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
            if town_hall.get(u'Notes'):
                town_hall[u'Notes'] = convert_links(town_hall[u'Notes'])
            if town_hall.get(u'Date'):
                # dates looks like this: Thursday, February 9, 2017
                print(town_hall[u'Date'])
                split_date = town_hall[u'Date'].split(',')
                if len(split_date) == 3:
                    try:
                        date_string = ' '.join([split_date[1].strip(), split_date[2].strip()])
                        date_8061 = arrow.get(date_string, 'MMMM D YYYY')
                        town_hall[u'date_8061'] = date_8061.format('YYYY-MM-DD')
                    except arrow.parser.ParserError:
                        try:
                            date_string = ' '.join([split_date[1].strip(), split_date[2].strip()])
                            date_8061 = arrow.get(date_string, 'MMM D YYYY')
                            town_hall[u'date_8061'] = date_8061.format('YYYY-MM-DD')
                        except arrow.parser.ParserError:
                            print("parse error on this date string: "+town_hall[u'Date'])
                            town_hall[u'date_8061'] = None
                else:
                    print("no attempt to parse this date string: " + town_hall[u'Date'])
                    town_hall[u'date_8061'] = None
    return town_hall_list


def generate_geocode_dictionary(town_hall_list, reconciled_addresses_dictionary):
    try:
        pkl_file = open('data_geo.pkl', 'rb')
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
        th_address_str = town_hall.get(u'address_string')
        if th_address_str:
            # first we ask nominatum if they know anything if we already haven't done so
            if 'nominatum' not in geocode_dictionary.get(th_address_str, {}).keys():
                nominatum_response = geocode_address_nominatum(street=town_hall.get(u'Street Address'),
                                                               city=town_hall.get(u'City'),
                                                               state=town_hall[u'State'].strip(),
                                                               address_string=th_address_str,
                                                               postalcode=xstr(town_hall.get(u'State')).strip())
                # check to see if there is already a dictionary there
                if geocode_dictionary.get(th_address_str):
                    geocode_dictionary[th_address_str]['nominatum'] = nominatum_response
                else:
                    geocode_dictionary[th_address_str] = {'nominatum': nominatum_response}
            # then we ask smartystreets if we haven't already:
            if 'smartystreets' not in geocode_dictionary.get(th_address_str, {}).keys():
                smartydata = geocode_smartystreets(street=town_hall.get(u'Street Address'), city=town_hall.get(u'City'),
                                                   state=town_hall.get(u'State'), zipcode=town_hall.get(u'Zip'),
                                                   address_string= th_address_str)
                if geocode_dictionary.get(th_address_str):
                    geocode_dictionary[th_address_str]['smartystreets'] = smartydata
                else:
                    geocode_dictionary[th_address_str] = {'smartystreets': smartydata}
        # then we jam in the reconciled data every time because we might keep messing with it and who cares there is no rate limit
        if th_address_str in reconciled_addresses_dictionary.keys():
            if geocode_dictionary.get(th_address_str):
                geocode_dictionary[th_address_str]['reconciled']= reconciled_addresses[th_address_str]['reconciled']
            else:
                geocode_dictionary[th_address_str] = {'reconciled': reconciled_addresses[th_address_str]['reconciled']}

    output = open('data_geo.pkl', 'wb')
    pickle.dump(geocode_dictionary, output, -1)
    output.close()
    return geocode_dictionary


def geocode_smartystreets(street, city, state, address_string, zipcode=None):
    auth_id = config.SMARTY_AUTH_ID  # We recommend storing your keys in environment variables
    auth_token = config.SMARTY_AUTH_TOKEN
    credentials = StaticCredentials(auth_id, auth_token)

    smarty_client = ClientBuilder(credentials).build()

    lookup = Lookup()
    lookup.street = street
    lookup.city = city
    lookup.state = state
    lookup.zipcode = zipcode

    try:
        smarty_client.send_lookup(lookup)
    except exceptions.SmartyException as err:
        print(err)
        return None

    result = lookup.result

    if not result:
        print("No smarty streets candidates. This address is not valid: " + address_string)
        return None

    first_candidate = result[0]
    # print("Address is valid. (There is at least one candidate)\n")
    data = {

        'street': first_candidate.components.primary_number + " " + first_candidate.components.street_name,
        'city': first_candidate.components.city_name,
        'zipcode': first_candidate.components.zipcode,
        'state': first_candidate.components.state_abbreviation,
        'latitude': first_candidate.metadata.latitude,
        'longitude': first_candidate.metadata.longitude,
        'first_candidate': first_candidate,
        'full_result': result

    }
    return data


def append_lat_long_to_townhall_data(town_hall_list, geocode_dict):
    geo_town_hall_list = deepcopy(town_hall_list)
    non_geo_town_hall_list = []
    for town_hall in geo_town_hall_list:
        if town_hall.get(u'address_string'):
            address = town_hall.get(u'address_string')
            reconciled = geocode_dict.get(address, {}).get('reconciled')
            nominatum = geocode_dict.get(address, {}).get('nominatum')
            smartystreets = geocode_dict.get(address, {}).get('smartystreets')
            if reconciled:
                town_hall[u'lat_lng'] = reconciled['corrected_lat_long']
                town_hall[u'address_string'] = reconciled['corrected_string']
            elif nominatum:
                town_hall[u'lat_lng'] = {'lat': float(nominatum[0]['lat']), 'lng': float(nominatum[0]['lon'])}
            elif smartystreets:
                town_hall[u'lat_lng'] = {'lat': float(smartystreets['latitude']), 'lng': float(smartystreets['longitude'])}
            else:
                town_hall[u'lat_lng'] = None
                non_geo_town_hall_list.append(town_hall)
        else:
            town_hall[u'lat_lng'] = None
            non_geo_town_hall_list.append(town_hall)
    return geo_town_hall_list, non_geo_town_hall_list


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
    latest_load = arrow.now(tz='US/Central').format('MMMM D, YYYY h:mm a')+' Central'
    feature_collection = FeatureCollection(feature_list, properties={'latestLoad': latest_load})
    return feature_collection

def generate_non_geo_townhall_list(non_geo_town_halls):
    cleaned_list = []
    for town_hall in non_geo_town_halls:
        jsonized = {
            u'date': town_hall.get(u'Date'),
            u'date8061': town_hall.get(u'date_8061'),
            u'district': town_hall.get(u'District'),
            u'location': town_hall.get(u'Location'),
            u'meetingType': town_hall.get(u'Meeting Type'),
            u'member': town_hall.get(u'Member'),
            u'notes': town_hall.get(u'Notes'),
            u'party': town_hall.get(u'Party'),
            u'state': town_hall.get(u'State Represented'),
            u'time': xstr(town_hall.get(u'Time')) + ' ' + xstr(town_hall.get(u'Time Zone')),
            u'address': town_hall.get(u'address_string')
        }
        cleaned_list.append(jsonized)
    print("number of non-geo town halls: " + str(len(cleaned_list)))
    return cleaned_list


def main():
    town_hall_list = get_townhall_data()
    geocode_dict = generate_geocode_dictionary(town_hall_list, reconciled_addresses)
    geo_town_hall_list, non_geo_town_hall_list = append_lat_long_to_townhall_data(town_hall_list, geocode_dict)
    feature_collection = generate_geojson(geo_town_hall_list)
    geojson_string = geojsondumps(feature_collection, sort_keys=True)
    map_data = open('docs/map_data.js', 'wb')
    json_geojson = json.loads(geojson_string)
    jsonized_non_geo_town_halls = generate_non_geo_townhall_list(non_geo_town_hall_list)
    map_data.write("var geoJsonData = %s" % json.dumps(json_geojson, indent=4, sort_keys=True) + ";\n"
                   + "var nonGeoData= %s" % json.dumps(jsonized_non_geo_town_halls, indent=4, sort_keys=True) + ";")
    map_data.close()
    #pprint(geocode_dict)
    print("list of addresses that don't pass validation:")
    non_address_list = []
    for town_hall in non_geo_town_hall_list:
        if xstr(town_hall.get(u'address_string')) not in non_address_list:
            non_address_list.append(xstr(town_hall.get(u'address_string')))
    print(non_address_list)
    # pprint(geocode_dict)


if __name__ == '__main__':
    main()
