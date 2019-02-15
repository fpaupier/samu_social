import math

import requests


class Map(object):
    def __init__(self):
        self.url = 'http://www.mapquestapi.com/geocoding/v1/address'
        self.key = 'vUAfGyga7KP9AZTU53AVLGhWcBFIrKIc'
        self.radius = 6371  # km

    def point(self, location):
        geographic_information = self.get({'location': location})
        return geographic_information['results'][0]['locations'][0]['displayLatLng']

    def distance(self, departure, arrival):
        # arrival['lng'], departure['lng'] = departure['lat'], departure['lng']
        # lat2, arrival['lng'] = arrival['lat'], arrival['lng']

        dlat = math.radians(arrival['lat'] - departure['lat'])
        dlon = math.radians(arrival['lng'] - departure['lng'])
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(arrival['lng'])) * math.cos(math.radians(arrival['lat'])) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = self.radius * c

        return d

    def get(self, parameter):
        payload = {'key': self.key}
        payload.update(parameter)

        request = requests.get(self.url, params=payload)
        request.raise_for_status()

        response = request.json()

        return response
