import os
from datetime import datetime

from src.domain.model_couple import solve_couples
from src.services.csv_reader import CsvReader
from src.domain.solver import solve_routes


### Should
# HOTELS_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'hotels-generalites.csv')
# EMPLOYEES_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'fichier-salarie.csv')

### Should not
HOTELS_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "enriched-hotels_subset.csv"
)
EMPLOYEES_DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "enriched-fichier-salarie.csv"
)


def main():
    csv_reader = CsvReader()

    ### Should
    # hotels, employees = csv_reader.parse(HOTELS_DATA_FILE, 'hotel'), csv_reader.parse(EMPLOYEES_DATA_FILE, 'people')
    ### Should not
    hotels, employees = (
        csv_reader.parse_enriched(HOTELS_DATA_FILE, "hotel"),
        csv_reader.parse_enriched(EMPLOYEES_DATA_FILE, "people"),
    )

    # FIXME: for performances reasons, we have the latitude and longitude
    #        data already inserted in the CSV files
    ### Should
    # _enrich_entity_with_point(map, hotels)
    # _enrich_entity_with_point(map, employees)

    employees = _enrich_employees_with_availabilities(employees)

    _enrich_employees_with_preferred_sectors(employees)

    # 1) Call model couple
    print('=========================================================')
    print('Start Resolution: Solver 1')
    print('=========================================================')
    assignments = solve_couples(employees)

    # 2) Select a date to focus on / filter model_couples
    # select the point of beginning / ending of each couples
    workers = format_couples_with_positions(employees, assignments[0])
    print('\n')

    # 3) Call solver
    print('=========================================================')
    print('Start Resolution: Solver 2')
    print('=========================================================')
    itinerary = solve_routes(hotels, workers)

    for worker in workers:
        worker['visits'] = [{
            'date': datetime.strptime(str(raw_visit_date)[:-1], '%Y%m%d').date().isoformat(),
            'time': 'Matin' if str(raw_visit_date)[-1] == 0 else 'Après-Midi'}
            for raw_visit_date in worker['availabilities']]

    for i, v in enumerate(itinerary):
        workers[i]['routes'] = v[1:-1]

    print_final_solution(workers)

    # 4) API/Mail/print to display solutions
    # TODO

    return workers


def format_couples_with_positions(employees, assignements):
    workers = []
    address_per_person = {p['name']: p['address'] for p in employees}
    postcode_per_person = {p['name']: p['postcode'] for p in employees}

    for couple, (availability, sector) in assignements.items():
        p1, p2 = couple
        workers.append({"name": "{}_and_{}".format(p1, p2),
                        "address": address_per_person[p1],
                        "postcode": postcode_per_person[p1],
                        "point": SECTOR_COORDINATES[sector],
                        "sector": sector,
                        "availabilities": availability})
    return workers


SECTOR_COORDINATES = {1: {'latitude': 48.852969, 'longitude' : 2.349894},
                      2: {'latitude': 48.582882, 'longitude': 2.499829},
                      3: {'latitude': 48.938204, 'longitude': 1.997205},
                      4: {'latitude': 48.909555, 'longitude': 2.445373}}


def _enrich_employees_with_preferred_sectors(employees):
    sectors_compatibility = {
        75: 1,
        77: 2,
        91: 2,
        94: 2,
        78: 3,
        92: 3,
        95: 3,
        93: 4,
    }
    for employee in employees:
        if employee["area1"]:
            employee_preferred_area = int(employee["area1"])
        else:
            employee["sector"] = None
            return
        if employee_preferred_area not in sectors_compatibility:
            employee["sector"] = None
        else:
            employee["sector"] = sectors_compatibility[int(employee["area1"])]


# /!\ Careful: impure function
def _enrich_entity_with_point(map, entities):
    for entity in entities:
        entity_address_and_postcode = {
            "address": entity.get("address"),
            "postcode": entity.get("postcode"),
        }
        point = map.point(entity_address_and_postcode)
        entity["point"] = point


def _enrich_employees_with_availabilities(employees):
    grouped_employees = {}
    for employee in employees:
        name_and_surname = "{} {}".format(
            employee["name"].strip(), employee["surname"].strip()
        )
        new_availability = process_employee_availability(employee)
        if name_and_surname not in grouped_employees:
            grouped_employees[name_and_surname] = employee
            grouped_employees[name_and_surname]["availabilities"] = new_availability
        else:
            new_availability = process_employee_availability(employee)
            grouped_employees[name_and_surname]["availabilities"] += new_availability

    return grouped_employees.values()


def process_employee_availability(employee):
    availability = datetime.strptime(employee["availability"], "%d/%m/%Y")
    time_of_day = employee["time_of_day"]
    if time_of_day.strip().lower() == "jour":
        morning, afternoon = (
            "{}{}{}{}".format(
                availability.year, availability.month, availability.day, 0
            ),
            "{}{}{}{}".format(
                availability.year, availability.month, availability.day, 1
            ),
        )
        return [int(morning), int(afternoon)]
    elif time_of_day.strip().lower() == "matin":
        morning = "{}{}{}{}".format(
            availability.year, availability.month, availability.day, 0
        )
        return [int(morning)]
    else:
        afternoon = "{}{}{}{}".format(
            availability.year, availability.month, availability.day, 0
        )
        return [int(afternoon)]


def print_final_solution(workers):
    for i, worker in enumerate(workers):
        print("---------------------------------")
        print("Binome {} from sector {} , address {} {} should visits hotels: "
              .format(worker.get('name'),
                      worker.get('sector'),
                      worker.get('address'),
                      worker.get('postcode'),))
        print("\n".join(worker.get('routes')))
        print("on dates : {}".format(worker.get('visits')))
        print("---------------------------------")


if __name__ == "__main__":
    main()
