from csv import DictReader, DictWriter
from datetime import datetime
import os
import boto3
import requests


CSV_URL = 'https://opendata.arcgis.com/datasets/6f2a47a25872470a815bcd95f52c2872_0.csv'
S3_CLIENT = boto3.client('s3')
S3_BUCKET_NAME = 'mo-coviz-data'


class Pipe:
    value = ""
    def write(self, text):
        self.value = self.value + text


def write_csv_to_bucket(key, content):
    params = {
        'Bucket': S3_BUCKET_NAME,
        'ACL': 'public-read',
        'Key': key,
        'Body': content,
    }
    return S3_CLIENT.put_object(**params)


def parse_response(r):
    return DictReader([str(l) for l in r.iter_lines()])


def clean_county_name(county_name):
    if county_name == 'ST LOUIS':
        county_name = 'St. Louis County'
    else:
        county_name = county_name.title() \
            .replace('St ', 'St. ') \
            .replace('Ste ', 'Ste. ')

    return county_name


def slice_columns(data):
    return [ 
        {
            'county': clean_county_name(d['MOHSISNAME']),
            'cases': int(d['Cases']),
            'deaths': int(d['Deaths']),
        } for d in data
    ]


def combine_city_w_county(city_name, county_name, data):
    city_data = [d for d in data if d['county'] == city_name][0]
    county_data = [d for d in data if d['county'] == county_name][0]
    county_data['cases'] += city_data['cases']
    county_data['deaths'] += city_data['deaths']

    combined_data = [
        d for d in data if d['county'] not in [city_name, county_name]
    ]
    combined_data.append(county_data)

    return sorted(combined_data, key=lambda k: k['county'])


def get_processed_csv(data):
    pipe = Pipe()
    headers = data[0].keys()
    writer = DictWriter(pipe, headers)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

    return pipe.value


def main():
    r = requests.get(CSV_URL)
    r.raise_for_status()

    write_csv_to_bucket('raw/latest.csv', r.content)
    # write the new source data to the s3 bucket (with timestamp)

    raw_data = parse_response(r)

    sliced_data = slice_columns(raw_data)

    processed_data = combine_city_w_county(
        'Kansas City', 'Jackson', sliced_data
    )
    processed_data = combine_city_w_county(
        'Joplin', 'Jasper', processed_data
    )

    processed_csv = get_processed_csv(processed_data)

    write_csv_to_bucket('processed/latest.csv', processed_csv)


if __name__ == '__main__':
    main()
