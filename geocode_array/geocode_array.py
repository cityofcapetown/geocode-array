# -*- coding: utf-8 -*-
"""
CCT Geocode Project:
This code reads in a list of addresses in json or csv format, attempts to geocode these addresses with the ArcGIS and Nominatim geocoders,
compares the results from both geocoders and selects the best. Then it attempts to geocode the addresses with the 
CCT geocoder and returns the output from the CCT geocoder as well as the best result from the combination of ArcGIS and Nominatim
in json and csv format.
"""

import json
import urllib
import urllib.request
import argparse
import csv

from geocode_array import API_key


def Google(addr):
    """
    Parameters: add_ID (Address ID) , addr (Address) 
    Step 1: Uses Google geocoder to find address co-ordinates. 
    Step 2: Reverse geocodes to find address.
    Step 3: Geocodes reverse geocoded address to find new co-ordinates.
    Step 4: Calculates distance between both sets of co-ordinates to be used as measure of error.
    Returns: address_G (address from step 1), lat_G (latitude from step 1), lon_G (longitude from step 1), d_G (distance from step 4)
    """
    try:
        values = {"address": addr,
                  "key": API_key}

        request_string = 'https://maps.googleapis.com/maps/api/geocode/json?{}'.format(urllib.parse.urlencode(values))

        req = urllib.request.Request(
            request_string,
            headers={
                'User-Agent': 'Chrome'
            }
        )
        r = urllib.request.urlopen(req)
        code = r.getcode()
        if code == 200:
            result_g = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            result_g = []
        address_g = result_g['results'][0]['formatted_address']

        # reverse
        lat_g, lon_g = result_g['results'][0]['geometry']['location']['lat'], \
                       result_g['results'][0]['geometry']['location']['lng']

        values = {"latlng": '{},{}'.format(lat_g, lon_g),
                  "key": API_key}

        request_string = 'https://maps.googleapis.com/maps/api/geocode/json?{}'.format(urllib.parse.urlencode(values))
        req = urllib.request.Request(
            request_string,
            headers={
                'User-Agent': 'Chrome'
            }
        )
        r = urllib.request.urlopen(req)
        code = r.getcode()
        if code == 200:
            reverse_result_g = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            reverse_result_g = []

        local = reverse_result_g['results'][0]['formatted_address']

        values = {"address": local,
                  "key": API_key}

        request_string = 'https://maps.googleapis.com/maps/api/geocode/json?{}'.format(urllib.parse.urlencode(values))

        req = urllib.request.Request(
            request_string,
            headers={
                'User-Agent': 'Chrome'
            }
        )
        r = urllib.request.urlopen(req)
        code = r.getcode()
        if code == 200:
            result_rev2_g = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            result_rev2_g = []

        # reverse
        lat2_g, lon2_g = result_rev2_g['results'][0]['geometry']['location']['lat'], \
                         result_rev2_g['results'][0]['geometry']['location']['lng']

        # get distance between points
        d_g = ((float(lat2_g) - float(lat_g)) ** 2 + (float(lon2_g) - float(lon_g)) ** 2) ** 0.5

    except Exception as e:
        d_g = 100000
        address_g = None
        lat_g = 'NaN'
        lon_g = 'NaN'

    return address_g, lat_g, lon_g, d_g


def ArcGIS(addr):
    """
    Parameters: add_ID (Address ID) , addr (Address) 
    Step 1: Uses ArcGIS geocoder to find address co-ordinates. 
    Step 2: Reverse geocodes to find address.
    Step 3: Geocodes reverse geocoded address to find new co-ordinates.
    Step 4: Calculates distance between both sets of co-ordinates to be used as measure of error.
    Returns: address_AG (address from step 1), lat_AG (latitude from step 1), lon_AG (longitude from step 1), d_AG (distance from step 4)
    """
    try:
        request_string = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?'
        values = {"singleLine": addr,
                  "outSR": 4326,
                  "f": "json"}
        req = urllib.request.Request(
            request_string,
            data=urllib.parse.urlencode(values).encode("utf-8"),
            headers={
                'User-Agent': 'Chrome'
            }
        )
        f = urllib.request.urlopen(req)
        code = f.getcode()
        if code == 200:
            result_ag = json.loads(f.read().decode('utf-8'))
        else:
            result_ag = []
            print('Got incorrect code: {}'.format(code))

        address_ag = result_ag['candidates'][0]['address']

        # reverse
        lon_ag, lat_ag = result_ag['candidates'][0]['location']['x'], result_ag['candidates'][0]['location']['y']
        request_string = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/reverseGeocode?'
        values = {"location": '{},{}'.format(lon_ag, lat_ag),
                  "outSR": 4326,
                  "f": "pjson"}
        req = urllib.request.Request(
            request_string,
            data=urllib.parse.urlencode(values).encode("utf-8"),
            headers={
                'User-Agent': 'Chrome'
            }
        )
        f = urllib.request.urlopen(req)
        code = f.getcode()
        if code == 200:
            reverse_result_ag = json.loads(f.read().decode('utf-8'))
        else:
            reverse_result_ag = []
            print('Got incorrect code: {}'.format(code))

        request_string = 'https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?'
        values = {"singleLine": reverse_result_ag['address']['LongLabel'],
                  "outSR": 4326,
                  "f": "json"}
        req = urllib.request.Request(
            request_string,
            data=urllib.parse.urlencode(values).encode("utf-8"),
            headers={
                'User-Agent': 'Chrome'
            }
        )
        f = urllib.request.urlopen(req)
        code = f.getcode()
        if code == 200:
            result_rev2_ag = json.loads(f.read().decode('utf-8'))
        else:
            result_rev2_ag = []
            print('Got incorrect code: {}'.format(code))

        lon2_ag, lat2_ag = result_rev2_ag['candidates'][0]['location']['x'], \
                           result_rev2_ag['candidates'][0]['location']['y']

        # get distance between points
        d_ag = ((float(lat2_ag) - float(lat_ag)) ** 2 + (float(lon2_ag) - float(lon_ag)) ** 2) ** 0.5
        # print('distance: {}'.format(d_AG))

    except Exception as e:
        d_ag = 100000
        address_ag = None
        lat_ag = 'NaN'
        lon_ag = 'NaN'

    return address_ag, lat_ag, lon_ag, d_ag


def Nominatim(addr):
    """
    Parameters: add_ID (Address ID) , addr (Address) 
    Step 1: Uses Nominatim geocoder to find address co-ordinates. 
    Step 2: Reverse geocodes to find address.
    Step 3: Geocodes reverse geocoded address to find new co-ordinates.
    Step 4: Calculates distance between both sets of co-ordinates to be used as measure of error.
    Returns: address_N (address from step 1), lat_N (latitude from step 1), lon_N (longitude from step 1), d_N (distance from step 4)
    """

    try:
        values = {"q": addr}
        request_string = 'https://nominatim.openstreetmap.org/?addressdetails=1&format=json&limit=1&{}'.format(
            urllib.parse.urlencode(values))
        req = urllib.request.Request(
            request_string,
            headers={'User-Agent': 'Chrome'}
        )
        f = urllib.request.urlopen(req)

        code = f.getcode()
        if code == 200:
            result_n = json.loads(f.read().decode('utf-8'))
        else:
            result_n = []
            print('Got incorrect code: {}'.format(code))

        address_n = result_n[0]['display_name']

        # reverse
        lat_n, lon_n = result_n[0]['lat'], result_n[0]['lon']
        request_string = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={}&lon={}'.format(lat_n, lon_n)

        req = urllib.request.Request(
            request_string,
            headers={'User-Agent': 'Chrome'}
        )
        f = urllib.request.urlopen(req)

        code = f.getcode()
        if code == 200:
            reverse_result_n = json.loads(f.read().decode('utf-8'))
        else:
            reverse_result_n = []
            print('Got incorrect code: {}'.format(code))

        # print('reverse: ',reverse_result_n['display_name'])

        local = reverse_result_n['display_name']
        values = {"q": local}
        request_string = 'https://nominatim.openstreetmap.org/?addressdetails=1&format=json&limit=1&{}'.format(
            urllib.parse.urlencode(values))
        req = urllib.request.Request(
            request_string,
            headers={'User-Agent': 'Chrome'}
        )
        f = urllib.request.urlopen(req)

        code = f.getcode()
        if code == 200:
            result_rev2_n = json.loads(f.read().decode('utf-8'))
        else:
            result_rev2_n = []
            print('Got incorrect code: {}'.format(code))

        lat2_n, lon2_n = result_rev2_n[0]['lat'], result_rev2_n[0]['lon']

        # get distance between points
        d_n = ((float(lat2_n) - float(lat_n)) ** 2 + (float(lon2_n) - float(lon_n)) ** 2) ** 0.5
        # print('distance: {}'.format(d_N))
    except Exception as e:
        d_n = 100000
        address_n = None
        lat_n = 'NaN'
        lon_n = 'NaN'

    return address_n, lat_n, lon_n, d_n


def CCT(add_id, addr):
    """
    Parameters: add_ID (Address ID) , addr (Address) 
    Step 1: Uses CCT geocoder to find address co-ordinates. 
    Step 2: Reverse geocodes to find address.
    Step 3: Geocodes reverse geocoded address to find new co-ordinates.
    Step 4: Calculates distance between both sets of co-ordinates to be used as measure of error.
    Returns: cct_address (address from step 1), cct_loc (latitude and longitude from step 1), cct_error (distance from step 4)
    """

    try:
        request_string = 'https://citymaps.capetown.gov.za/agsext1/rest/services/Here/GC_CoCT/GeocodeServer' \
                         '/geocodeAddresses '
        values = {"addresses": {"records": [{"attributes": {"OBJECTID": add_ID, "SingleLine": addr}}]},
                  "outSR": 4326,
                  "f": "json"}
        req = urllib.request.Request(request_string,
                                     data=urllib.parse.urlencode(values).encode("utf-8"),
                                     headers={'User-Agent': 'Chrome'})
        r = urllib.request.urlopen(req)
        code = r.getcode()
        if code == 200:
            result_cct = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            result_cct = []
        # print(result_cct["locations"][0]['address'], result_cct["locations"][0]['location'])
        cct_address = result_cct["locations"][0]['address']

        cct_loc = result_cct["locations"][0]['location']
        cct_lat, cct_lon = result_cct["locations"][0]['location']['y'], result_cct["locations"][0]['location']['x']

        # print(cct_address, cct_lat, cct_lon)

        request_string = 'https://citymaps.capetown.gov.za/agsext1/rest/services/Here/GC_CoCT/GeocodeServer' \
                         '/reverseGeocode '
        values = {"location": str(cct_loc),
                  "outSR": 4326,
                  "f": "pjson"}

        req = urllib.request.Request(request_string,
                                     data=urllib.parse.urlencode(values).encode("utf-8"),
                                     headers={'User-Agent': 'Chrome'})
        r = urllib.request.urlopen(req)
        code = r.getcode()
        if code == 200:
            reverse_result = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            reverse_result = []

        # print(reverse_result['address']['Match_addr'])
        reverse_addr = reverse_result['address']['Match_addr']

        request_string = 'https://citymaps.capetown.gov.za/agsext1/rest/services/Here/GC_CoCT/GeocodeServer' \
                         '/geocodeAddresses '
        values = {"addresses": {"records": [{"attributes": {"OBJECTID": add_ID, "SingleLine": reverse_addr}}]},
                  "outSR": 4326,
                  "f": "json"}
        req = urllib.request.Request(request_string,
                                     data=urllib.parse.urlencode(values).encode("utf-8"),
                                     headers={'User-Agent': 'Chrome'})
        r = urllib.request.urlopen(req)

        code = r.getcode()
        if code == 200:
            result_rev2_cct = json.loads(r.read().decode('utf-8'))
        else:
            print('Got incorrect code: {}'.format(code))
            result_rev2_cct = []

        # print(result_rev2_cct["locations"][0]['address'], result_rev2_cct["locations"][0]['location'])

        cct_lat2, cct_lon2 = result_rev2_cct["locations"][0]['location']['y'], \
                             result_rev2_cct["locations"][0]['location']['x']

        # get distance between points
        d_cct = ((float(cct_lat2) - float(cct_lat)) ** 2 + (float(cct_lon2) - float(cct_lon)) ** 2) ** 0.5
        # print('distance: {}'.format(d_cct))
        # print(d_cct)
        cct_error = d_cct

    except Exception as e:
        # print("address {} failed".format(add))
        cct_address = None
        cct_loc = 'NaN'
        cct_error = 'NaN'

    return cct_address, cct_loc, cct_error


def compare(address_ag, lat_ag, lon_ag, d_ag, address_n, lat_n, lon_n, d_n, add_id):
    """
    Compares outputs from ArcGIS and Nominatim and returns the most accurate result
    """
    try:
        dist = [d_ag, d_n]
        print(dist)
        if d_ag == 0.0:
            # print('use ArcGIS: {}'.format(address_ag))
            print('use ArcGIS')
            lat = lat_ag
            lon = lon_ag
            address_name = address_ag
            error = d_ag

        elif d_n == 0.0:
            # print('use Nominatim: {}'.format(address_n))
            print('use Nominatim')
            lat = lat_n
            lon = lon_n
            address_name = address_n
            error = d_n

        elif d_ag == min(dist):
            # print('use ArcGIS because min dist: {}'.format(address_ag))
            print('use ArcGIS because min dist')
            lat = lat_ag
            lon = lon_ag
            address_name = address_ag
            error = d_ag

        elif d_n == min(dist):
            # print('use Nominatim because min dist: {}'.format(address_n))
            print('use Nominatim because min dist')
            lat = lat_n
            lon = lon_n
            address_name = address_n
            error = d_n

        else:
            print('did not work on address ID: {}'.format(add_id))
            lat = 'NaN'
            lon = 'NaN'
            address_name = None
            error = 'NaN'

        # print("address ID: {}, address: {}, lat: {}, lon: {}, error: {}, option: {}".format(add_ID, address_name,
        # lat, lon, error, option))

    except Exception as e:
        print('did not work on address ID: {}'.format(add_id))
        lat = 'NaN'
        lon = 'NaN'
        address_name = None
        error = 'NaN'
    return lat, lon, address_name, error


def compare_all(address_G, lat_g, lon_g, d_g, address_ag, lat_ag, lon_ag, d_ag, address_n, lat_n, lon_n, d_n, add_id):
    """
    Compares outputs from Google, ArcGIS, and Nominatim and returns the most accurate result
    """
    try:
        dist = [d_g, d_ag, d_n]
        print(dist)

        if d_g == 0.0:
            # print('use google: {}'.format(address_G))
            print('use google')
            lat = lat_g
            lon = lon_g
            address_name = address_G
            error = d_g

        elif d_ag == 0.0:
            # print('use ArcGIS: {}'.format(address_ag))
            print('use ArcGIS')
            lat = lat_ag
            lon = lon_ag
            address_name = address_ag
            error = d_ag

        elif d_n == 0.0:
            # print('use Nominatim: {}'.format(address_n))
            print('use Nominatim')
            lat = lat_n
            lon = lon_n
            address_name = address_n
            error = d_n

        elif d_g == min(dist):
            # print('use google because min dist: {}'.format(address_G))
            print('use google because min dist')
            lat = lat_g
            lon = lon_g
            address_name = address_G
            error = d_g

        elif d_ag == min(dist):
            # print('use ArcGIS because min dist: {}'.format(address_ag))
            print('use ArcGIS because min dist')
            lat = lat_ag
            lon = lon_ag
            address_name = address_ag
            error = d_ag

        elif d_n == min(dist):
            # print('use Nominatim because min dist: {}'.format(address_n))
            print('use Nominatim because min dist')
            lat = lat_n
            lon = lon_n
            address_name = address_n
            error = d_n

        else:
            print('did not work on address ID: {}'.format(add_id))
            lat = 'NaN'
            lon = 'NaN'
            address_name = None
            error = 'NaN'

    except Exception as e:
        print('did not work on address ID: {}'.format(add_id))
        lat = 'NaN'
        lon = 'NaN'
        address_name = None
        error = 'NaN'

    return lat, lon, address_name, error