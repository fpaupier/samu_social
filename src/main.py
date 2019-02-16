import csv
import os
from datetime import datetime

from src.domain.model_couple import solve_couples
from src.services.csv_reader import CsvReader
from src.services.map import Map
from src.domain.solver import solve


### Should
# HOTELS_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'hotels-generalites.csv')
# EMPLOYEES_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'fichier-salarie.csv')

### Should not
HOTELS_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'enriched-hotels-generalites.csv')
EMPLOYEES_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'enriched-fichier-salarie.csv')


def main():
    csv_reader = CsvReader()
    map = Map()

    ### Should
    # hotels, employees = csv_reader.parse(HOTELS_DATA_FILE, 'hotel'), csv_reader.parse(EMPLOYEES_DATA_FILE, 'people')
    ### Should not
    hotels, employees = csv_reader.parse_enriched(HOTELS_DATA_FILE, 'hotel'), \
                        csv_reader.parse_enriched(EMPLOYEES_DATA_FILE, 'people')

    # FIXME: for performances reasons, we have the latitude and longitude
    #        data already inserted in the CSV files
    ### Should
    # _enrich_entity_with_point(map, hotels)
    # _enrich_entity_with_point(map, employees)

    employees = _enrich_employees_with_availabilities(employees)

    # 1) Call model couple
    availabilities = solve_couples(employees)

    # 2) Select a date to focus on / filter model_couples

    # 3) Call solver
    solve(hotels, len(availabilities))

    # 4) API/Mail/print to display solutions


# /!\ Careful: impure function
def _enrich_entity_with_point(map, entities):
    for entity in entities:
        entity_address_and_postcode = {
            'address': entity.get('address'),
            'postcode': entity.get('postcode'),
        }
        point = map.point(entity_address_and_postcode)
        entity['point'] = point


def _enrich_employees_with_availabilities(employees):
    grouped_employees = {}
    for employee in employees:
        name_and_surname = '{} {}'.format(employee['name'].strip(), employee['surname'].strip())
        new_availability = process_employee_availability(employee)
        if name_and_surname not in grouped_employees:
            grouped_employees[name_and_surname] = employee
            grouped_employees[name_and_surname]['availabilities'] = new_availability
        else:
            new_availability = process_employee_availability(employee)
            grouped_employees[name_and_surname]['availabilities'] += new_availability

    return grouped_employees.values()


def process_employee_availability(employee):
    availability = datetime.strptime(employee['availability'], '%d/%m/%Y')
    time_of_day = employee['time_of_day']
    if time_of_day.strip().lower() == 'jour':
        morning, afternoon = '{}{}{}{}'.format(availability.year, availability.month, availability.day, 0), \
                             '{}{}{}{}'.format(availability.year, availability.month, availability.day, 1)
        return [int(morning), int(afternoon)]
    elif time_of_day.strip().lower() == 'matin':
        morning = '{}{}{}{}'.format(availability.year, availability.month, availability.day, 0)
        return [int(morning)]
    else:
        afternoon = '{}{}{}{}'.format(availability.year, availability.month, availability.day, 0)
        return [int(afternoon)]


if __name__ == '__main__':
    main()
