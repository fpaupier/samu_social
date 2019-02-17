"""
 Parse CSV to extract addresses

 How to use the `csv_reader` script:

 1) Save the xls data file as a csv in UTF8 encoding
 2) Call the script by specifying the type of source (hotel or people)
  ```
  $  python src/services/csv_reader.py \
      -t "hotel" \
      -s "/Users/fpaupier/projects/samu_social/data/hotels-generalites.csv"
  ```
 3) A json file with the list of addresses is generated.
"""

import csv
import argparse
import json


class CsvReader(object):
    def parse(self, source, csv_type):
        results = []

        with open(source, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            data = {i: j for i, j in enumerate(reader)}
            for i, line in data.items():
                if csv_type == "people" and i > 0:
                    formatted_address = '{} {} {} {}'.format(line[2], line[3], line[4], line[5])
                    people = {
                        'name': line[0],
                        'surname': line[1],
                        'address': ' '.join(formatted_address.split()),
                        'postcode': line[6],
                        'license': line[7],
                        'availability': line[8],
                        'time_of_day': line[9],
                        'area1': line[10],
                        'area2': line[11],
                        'area3': line[12],
                        'area4': line[13],
                    }
                    results.append(people)
                if csv_type == "hotel" and i > 0:
                    if line[2] == "0":  # Only consider non removed hotel
                        formatted_address = "{} {}".format(line[7], line[9])
                        hotel = {
                            'hotel_status': line[2],
                            'nom': line[6],
                            'address': ' '.join(formatted_address.split()),
                            'postcode': line[8],
                            'capacity': line[41],
                            'bedroom_number': line[43],
                            'features': sum([int(line[i]) for i, line in enumerate(reader) if i in range(62, 150)]),
                            ### Should not
                        }
                        results.append(hotel)

        return results

    def parse_enriched(self, source, csv_type):
        results = []

        with open(source, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            data = {i: j for i, j in enumerate(reader)}
            for i, line in data.items():
                if csv_type == 'people' and i > 0:
                    point = {'latitude': float(line[6]), 'longitude': float(line[8])} if (line[6] and line[8]) else None
                    people = {
                        'address': line[0],
                        'area1': line[1],
                        'area2': line[2],
                        'area3': line[3],
                        'area4': line[4],
                        'availability': line[5],
                        'license': line[7],
                        'name': line[9],
                        'point': point,
                        'postcode': line[11],
                        'surname': line[12],
                        'time_of_day': line[13],
                    }
                    results.append(people)
                if csv_type == 'hotel' and i > 0:
                    point = {'latitude': float(line[5]), 'longitude': float(line[6])} if (line[5] and line[6]) else None
                    hotel = {
                        'address': line[0],
                        'bedroom_number': line[1],
                        'capacity': line[2],
                        'features': line[3],
                        'hotel_status': line[4],
                        'nom': line[7],
                        'point': point,
                        'postcode': line[9],
                    }
                    results.append(hotel)
        return results


def parse_csv(source, csv_type, write=False):
    """
    Args:
    source(string): absolute path to the file to process
    csv_type(string): type of csv file, hotel data or volunteer data

    Return:
        json_path: path to the file containing the adress as json format. 
    """
    f_name = source.split(".")[0]
    json_path = "{0}-{1}.json".format(f_name, csv_type)

    results = []
    with open(source, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        data = {i: j for i, j in enumerate(reader)}
        for i, line in data.items():
            if csv_type == "people" and i > 0:
                formatted_address = '{} {} {} {}'.format(line[2], line[3], line[4], line[5])
                people = {
                    'name': line[0],
                    'surname': line[1],
                    'address': ' '.join(formatted_address.split()),
                    'postcode': line[6],
                    'license': line[7],
                    'availability': line[8],
                    'time_of_day': line[9],
                    'area1': line[10],
                    'area2': line[11],
                    'area3': line[12],
                    'area4': line[13],
                }
                results.append(people)
            if csv_type == "hotel" and i > 0:
                if line[2] == "0":  # Only consider non removed hotel
                    formatted_address = "{} {}".format(line[7], line[9])
                    hotel = {
                        'hotel_status': line[2],
                        'nom': line[6],
                        'address': ' '.join(formatted_address.split()),
                        'postcode': line[8],
                        'capacity': line[41],
                        'bedroom_number': line[43],
                        'features': sum([int(line[i]) for i, line in enumerate(reader) if i in range(62, 150)]),
                    }
                    results.append(hotel)

    if write:
        with open(json_path, "w", encoding="utf8") as outfile:
            json.dump(results, outfile, ensure_ascii=False)
        return json_path

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A scraper to obtain addresses from a csv"
    )
    parser.add_argument(
        "-t",
        "--csv_type",
        help="type of csv file to parse: `hotel` or `people`",
        type=str,
        default="hotel",
    )

    parser.add_argument("-s", "--source", help="path to the source csv file", type=str)

    args = parser.parse_args()

    data = parse_csv(args.source, args.csv_type, write=False)

    print(data)
