"""
Load data into datastore
"""
import argparse

import boto3
import numpy as np
import pandas as pd

DYNAMO_RESOURCE = boto3.resource(
    service_name='dynamodb',
    region_name='ap-southeast-2',
    endpoint_url='http://dynamodb-local:8000'
)
TABLE_NAME = 'PandoraDetails'


def create_table():
    """Attempt to create the table"""
    try:
        DYNAMO_RESOURCE.create_table(
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'lsi',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'sk',
                    'KeyType': 'RANGE'
                },
            ],
            LocalSecondaryIndexes=[
                {
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'pk',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'lsi',
                            'KeyType': 'RANGE'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                    }
                }
            ],
            TableName=TABLE_NAME,
            BillingMode='PAY_PER_REQUEST'
        )
    except Exception as ex:
        print(ex)
        print('Unable to create table: ', TABLE_NAME)


def load_companies(path):
    """Load companies json file into datastore."""
    print('Loading company data from: ', path)
    table = DYNAMO_RESOURCE.Table(TABLE_NAME)
    dframe = pd.read_json(path, orient='records')
    with table.batch_writer() as writer:
        for entry in dframe.to_dict(orient='records'):
            item = {
                'pk': 'company',
                'sk': '{}#{}#'.format(
                    entry['index'],
                    entry['company']
                ),
                'metadata': {
                    'name': entry['company']
                }
            }
            writer.put_item(Item=item)


def vector_operations(columns=[], **kwargs):
    """Vectorised operations for dataframes."""
    ret_vectors = []
    if 'sk' in columns:
        sk_column = kwargs['company_id'].astype(str).str.cat(
            [
                kwargs['index'].astype(str),
            ], sep="#")
        ret_vectors.append(sk_column)
    if 'lsi' in columns:
        has_brown_eyes = kwargs['eyeColor'].str.lower() == 'brown'
        lsi_column = has_brown_eyes.astype(str).astype(str).str.cat(
            [
                kwargs['has_died'].astype(str), kwargs[
                    'user_id'].astype(str)
            ], sep="#")
        ret_vectors.append(lsi_column)
    if 'username' in columns:
        username_column = kwargs['name'].str.split(' ').str[0]
        ret_vectors.append(username_column)
    return (vector for vector in ret_vectors)


def load_people(path):
    """Load people json file into datastore."""
    print('Loading people data from: ', path)
    table = DYNAMO_RESOURCE.Table(TABLE_NAME)
    dframe = pd.read_json(path, orient='records')
    dframe['pk'] = 'person'
    dframe['sk'], dframe['lsi'], dframe['username'] = vector_operations(
        columns=['sk', 'lsi', 'username'],
        user_id=dframe['_id'],
        company_id=dframe['company_id'],
        index=dframe['index'],
        has_died=dframe['has_died'],
        name=dframe['name'],
        eyeColor=dframe['eyeColor']
    )
    dframe['age'] = dframe['age'].astype(int)
    dframe['friends'] = dframe['friends'].apply(
        lambda x: [item['index'] for item in x])
    dframe.rename({
        '_id': 'user_id',
        'name': 'fullname'
    }, inplace=True, axis=1)
    with table.batch_writer() as writer:
        for entry in dframe.to_dict(orient='records'):
            writer.put_item(Item=entry)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "companies_file",
        help="path for the companies' details file")
    parser.add_argument(
        "people_file",
        help="path for the peoples' details file")

    args = parser.parse_args()
    create_table()
    load_companies(args.companies_file)
    load_people(args.people_file)
