"""
 Parse CSV to extract addresses

 How to use the `csv_reader` script:

 1) Save the xls data file as a csv in UTF8 encoding
 2) Call othe script by specifyng the type of source (hotel or people)
  ```
  $  python src/services/csv_reader.py \
      -t "hotel" \
      -s "/Users/fpaupier/projects/samu_social/data/hotels-generalites.csv"
  ```
 3) A json file with the list of adresses is generated.
"""

import csv
import os
import argparse
import json 


dirname = os.path.dirname(__file__)

def parse_csv(source, csv_type):
    """
    Args:
    source(string): absolute path to the file to process
    csv_type(string): type of csv file, hotel data or volunteer data

    Return:
        json_path: path to the file containing the adress as json format. 
    """
    f_name = source.split('.')[0]
    json_path = "{0}-{1}.json".format(f_name, csv_type)

    adresses = []
    with open(source, "r", encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=";")
        for i, line in enumerate(reader):
            if csv_type == "people" and i > 0:
                adresses.append("{} {} {} {} {}".format(line[2], line[3], line[4], line[5], line[6]))
            if csv_type == "hotel" and i > 0:
                if line[2] == '0': # Only consider non removed hotel
                    adresses.append("{} {} {}".format(line[7], line[8], line[9]))

    with open(json_path, 'w', encoding='utf8') as outfile:
        json.dump(adresses, outfile, ensure_ascii=False)

    return json_path



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A scraper to obtain addresses from a csv"
    )
    parser.add_argument('-t',
                        '--csv_type',
                        help='type of csv file to parse: `hotel` or `people`',
                        type=str,
                        default='hotel',
                        )

    parser.add_argument('-s',
                        '--source',
                        help='path to the source csv file',
                        type=str,
                        )

    args = parser.parse_args()
    parse_csv(args.source, args.csv_type)
