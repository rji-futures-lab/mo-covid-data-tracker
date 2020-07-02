from csv import DictReader, DictWriter
from datetime import datetime
import json
import os
import boto3
import requests


FEATURE_LAYER_URL = 'https://services6.arcgis.com/Bd4MACzvEukoZ9mR/arcgis/rest/services/county_MOHSIS_map/FeatureServer/0/query'
PARAMS = {
    'f': 'json',
    'where': '1=1',
    'returnGeometry': False,
    'spatialRel': 'esriSpatialRelIntersects',
    'outFields': '*',
    'orderByFields': 'NAME2 asc',
    'resultOffset': 0,
    'resultRecordCount': 121,
    'resultType': 'standard',
    'cacheHint': True,
}

S3_CLIENT = boto3.client('s3')
S3_BUCKET_NAME = 'mo-coviz-data'


class Pipe:
    value = ""
    def write(self, text):
        self.value = self.value + text


def get_feature_layer():
    r = requests.get(FEATURE_LAYER_URL, params=PARAMS)
    r.raise_for_status()

    return r.json()


def get_county_attributes(layer):
    return [f['attributes'] for f in layer['features']]


def write_to_s3(key, content):
    params = {
        'Bucket': S3_BUCKET_NAME,
        'ACL': 'public-read',
        'Key': key,
        'Body': content,
    }
    return S3_CLIENT.put_object(**params)


def edit_row(row):
    if row['NAME'] == 'St. Louis' and row['TYPE'] == 'County':
        county_name = 'St. Louis County'
    else:
        county_name = row['NAME']

    try:
        cases = int(row['CASES'])
    except TypeError:
        cases = None

    try:
        deaths = int(row['DEATHS'])
    except TypeError:
        deaths = None        

    return {
        'county': county_name,
        'cases': cases,
        'deaths': deaths,
    }


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


def to_csv(data):
    pipe = Pipe()
    headers = data[0].keys()
    writer = DictWriter(pipe, headers)
    writer.writeheader()
    for row in data:
        writer.writerow(row)

    return pipe.value


def main():
    layer = get_feature_layer()

    write_to_s3('county_MOHSIS_map/layer/latest.json', json.dumps(layer))

    county_attributes = get_county_attributes(layer)
    
    full_csv = to_csv(county_attributes)
    
    write_to_s3('county_MOHSIS_map/county-attributes/latest.csv', full_csv)

    for row in county_attributes:
        print(edit_row(row))

    county_edited_attributes = [edit_row(r) for r in county_attributes]

    county_edited_attributes = combine_city_w_county('Kansas City', 'Jackson', county_edited_attributes)
    
    county_edited_attributes = combine_city_w_county('Joplin', 'Jasper', county_edited_attributes)
    
    edited_csv = to_csv(county_edited_attributes)

    write_to_s3('county_MOHSIS_map/county-attributes-edited/latest.csv', edited_csv)


def lambda_handler(event, context):
    return main()


if __name__ == '__main__':
    main()
