from datetime import datetime

from src.services.csv_reader import parse_csv


def read_employees_file(filepath):
    employees = parse_csv(filepath, 'people')

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
        return [morning, afternoon]
    elif time_of_day.strip().lower() == 'matin':
        morning = '{}{}{}{}'.format(availability.year, availability.month, availability.day, 0)
        return [morning]
    else:
        afternoon = '{}{}{}{}'.format(availability.year, availability.month, availability.day, 0)
        return [afternoon]


if __name__ == '__main__':
    filepath = '/Users/emericbris/Downloads/55/fichier-salarie.csv'
    test = read_employees_file(filepath)

    print(test)
