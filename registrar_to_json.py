#!/usr/bin/env python3
import argparse, os.path, csv, json
from os import makedirs
from datetime import date

def safe(args):
    # Destination folder doesn't exist.
    if not os.path.exists(os.path.dirname(args.json_path)):
        makedirs(os.path.dirname(args.json_path))
    # Destination path already exists, cannot overwrite.
    elif os.path.exists(args.json_path) and not args.force:
        return False
    # Source file unrealistically small.
    return os.path.exists(args.csv_path) and os.path.getsize(args.csv_path) > 2000000

def to_json(args):
    with open(args.csv_path, 'r') as csv_file:
        # I want each row as a dict, because that's how we interact with the JSON.
        csv_reader = csv.DictReader(csv_file)

        # If the CSV includes a UTF byte order mark (looks like '\ufeff"Field Name"'), pull the fieldname out.
        if csv_reader.fieldnames[0].startswith('\ufeff"'):
            csv_reader.fieldnames[0] = csv_reader.fieldnames[0].split('"')[1]

        # Graduation service expects lowercase fieldnames.
        csv_reader.fieldnames = [name.lower() for name in csv_reader.fieldnames]

        with open(args.json_path, 'w') as json_file:
            # JSON file is a dict of records, with each record on a separate line.
            # Each record is <etd record key>: <dict of csv row>
            first_line = True
            for row in csv_reader:
                # If compact output is requested, skip rows without graduation dates.
                if args.compact and row['degree status date'].strip() == '':
                    continue
                if first_line:
                    # First line, start a dict.
                    json_file.write('{"%s":' % row['etd record key'])
                    # First line only happens once.
                    first_line = False
                else:
                    # After the first line, so add a comma and new line before dumping the next record.
                    json_file.write(',\n"%s":' % row['etd record key'])
                # No matter how the line begins, always dump the record.
                # Sort the fields because Python dicts don't order their keys.
                json.dump(row, json_file, separators=(',', ':'), sort_keys=True)

            # End dict.
            json_file.write('}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reformats the Registrar's CSV data as JSON.")
    parser.add_argument('csv_path',
            help='Path to the CSV file to reformat.')
    parser.add_argument('json_path',
            nargs='?',
            help='Path for the JSON file to be created. Default is "registrar-data-<date>-compact.json".')
    parser.add_argument('--force', '--overwrite', '-f', '-o',
            action='store_true',
            help='Overwrite an existing output file.')
    output_type = parser.add_mutually_exclusive_group()
    output_type.add_argument('--compact', '-c',
            default=True,
            action='store_true',
            help='Assumed by default. Compacts the output by only including rows with graduation dates.')
    output_type.add_argument('--full',
            action='store_false',
            dest='compact',
            help='Prevents output from being reduced to only rows with graduation dates')
    args = parser.parse_args()

    if args.json_path is None:
        today = date.today().strftime('%Y%m%d')
        record_type = 'compact'
        if not args.compact:
            record_type = 'full'
        args.json_path = 'registrar-data-{}-{}.json'.format(today, record_type)

    args.csv_path = os.path.abspath(os.path.expanduser(args.csv_path))
    args.json_path = os.path.abspath(os.path.expanduser(args.json_path))

    if safe(args):
        to_json(args)
    else:
        print('Something is wrong with the arguments supplied. Double check that the CSV exists, and the JSON does not.')
