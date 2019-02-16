import os

from src.services.csv_reader import CsvReader
from src.services.map import Map

HOTELS_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'hotels-generalites.csv')
EMPLOYEES_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fichier-salarie.csv')


def main():
    csv_reader = CsvReader()
    hotels, employees = csv_reader.parse(HOTELS_DATA_FILE, 'hotel'), csv_reader.parse(EMPLOYEES_DATA_FILE, 'people')

    map = Map()

    _enrich_entity_with_point(map, hotels)
    _enrich_entity_with_point(map, employees)

    # 1) Call model couple

    # 2) Select a date to focus on / filter model_couples

    # 3) Call solver

    # 4) API/Mail/print to display solutions
    

# /!\ Careful: closure/impure function
def _enrich_entity_with_point(map, entity):
    entity_address_and_postcode = {
        'address': entity.get('address'),
        'postcode': entity.get('postcode'),
    }
    point = map.point(entity_address_and_postcode)
    entity['point'] = point
