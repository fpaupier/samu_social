import os
from datetime import datetime

from src.domain.model_couple import exploration, satisfaction
from src.services.csv_reader import CsvReader
from src.services.map import Map

HOTELS_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'hotels-generalites.csv')
EMPLOYEES_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'fichier-salarie.csv')


def main():
    csv_reader = CsvReader()
    map = Map()

    hotels, employees = csv_reader.parse(HOTELS_DATA_FILE, 'hotel'), csv_reader.parse(EMPLOYEES_DATA_FILE, 'people')

    # _enrich_entity_with_point(map, hotels)
    _enrich_entity_with_point(map, employees)

    employees = _enrich_employees_with_availabilities(employees)

    # 1) Call model couple

    persons, disponibility_per_persons = [p['name'] for p in employees], {p['name']: p['availabilities'] for p in employees}

    print('---- Exploration ----')
    exploration_status, exploration_assignments, maximisation = exploration(persons, disponibility_per_persons)

    print('---- Satisfaction ----')
    satisfaction_status, satisfaction_assignments = satisfaction(persons, disponibility_per_persons, maximisation)
    # 2) Select a date to focus on / filter model_couples

    # 3) Call solver

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
