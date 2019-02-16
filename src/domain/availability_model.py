from src.services.csv_reader import parse_csv


def read_employees_file(filepath):
    employees = parse_csv(filepath, 'people')
    import ipdb; ipdb.set_trace()
    employees_availabity = employees['availability']

    return employees_availabity


if __name__ == '__main__':
    filepath = '/Users/emericbris/Downloads/55/fichier-salarie.csv'
    test = read_employees_file(filepath)

    print(test)
