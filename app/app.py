"""
Endpoint handlers.

Main application module
"""
import logging
import traceback

import boto3
import pandas as pd
from boto3.dynamodb.conditions import Attr, Key
from flask import Flask, jsonify, request
from flask.views import MethodView

DYNAMO_RESOURCE = boto3.resource(
    service_name='dynamodb',
    region_name='ap-southeast-2',
    endpoint_url='http://dynamodb-local:8000'
)
DDB_TABLE = DYNAMO_RESOURCE.Table('PandoraDetails')
app = Flask(__name__)


class CompanyAPI(MethodView):
    """Class-based view for the company API."""

    def get(self, company_id):
        """
        Retrieve company details.

        Retrieve a company's list of users.
        """
        payload = {}
        try:
            user_details = [
                'user_id', 'fullname', 'email', 'phone'
            ]
            # Retrieve the company
            key_exp = Key('pk').eq('company') & Key(
                'sk').begins_with(str(company_id))
            company = DDB_TABLE.query(
                KeyConditionExpression=key_exp
            )
            if company.get('Count', 0) == 0:
                payload = {'Error': 'Company being retrieved does not exist'}
                status_code = 404
            else:
                company = company['Items'][0]
                # Retrieve users employees the company
                user_key_exp = Key('pk').eq('person') & Key(
                    'sk').begins_with(str(company_id))
                users = DDB_TABLE.query(
                    KeyConditionExpression=user_key_exp,
                    ProjectionExpression=', '.join(user_details)
                )
                payload = {
                    'companyID': company_id,
                    'companyName': company['metadata']['name'],
                    'employees': users.get('Items', []),
                    'lastRecord': users.get('LastEvaluatedKey')
                }
                status_code = 200
        except Exception as ex:
            logging.error('Unknown error occured', exc_info=True)
            payload = {'Error': 'Unknown error occured'}
            status_code = 500
        return jsonify(payload), status_code


class UserAPI(MethodView):
    """Class-based view for the user API."""

    lsi_key_combinations = [
        'True#True', 'True#False', 'False#True', 'False#False'
    ]

    def retrieve_user(self, user_id):
        """Retrieve user from table."""
        pk_exp = Key('pk').eq('person')

        for lsi_key in self.lsi_key_combinations:
            sk_exp = Key('lsi').eq(lsi_key + '#' + user_id)
            key_exp = pk_exp & sk_exp
            # Retrieve user with ID
            user = DDB_TABLE.query(
                IndexName='user-id-index',
                KeyConditionExpression=key_exp
            )
            if user.get('Count', 0) == 0:
                continue
            else:
                return user['Items'][0]

    def retrieve_common_friends(
            self, user_ids, friends=pd.DataFrame(), last_record=None):
        """Retrieve multiple users from the table."""
        key_exp = Key('pk').eq('person') & Key('lsi').begins_with(
            'True#False')
        filters = {
            'IndexName': 'user-id-index',
            'KeyConditionExpression': key_exp,
            'FilterExpression': Attr('index').is_in(user_ids)
        }
        if last_record:
            filters['ExclusiveStartKey'] = last_record
        users = DDB_TABLE.query(**filters)
        friends = friends.append(users['Items'])
        if users.get('LastEvaluatedKey') is not None:
            self.retrieve_common_friends(
                user_ids, friends,
                last_record=users.get('LastEvaluatedKey')
            )
        return friends

    def get(self, user_id):
        """
        Retrieve user details.

        Retrieve user details if user ID is existing.
        If user ID is not existing, check for query parameters
        user_1 and user_2 to retrieve user details
        """
        payload = {}
        try:
            if user_id:
                # Retrieve user details
                user = self.retrieve_user(user_id)
                if user:
                    payload = {
                        'username': user['username'],
                        'age': int(user['age']),
                        'fruits': list(
                            user['fruits']) if user['fruits'] else None,
                        'vegetables': list(
                            user['vegetables']) if user['vegetables'] else None
                    }
                    status_code = 200
                else:
                    payload = {
                        'Error': 'User being retrieved does not exist'}
                    status_code = 404
            else:
                if request.args:
                    if 'user1' in request.args and 'user2' in request.args:
                        # Retreive details of users
                        user1 = self.retrieve_user(request.args['user1'])
                        user2 = self.retrieve_user(request.args['user2'])
                        if user1 and user2:
                            required_keys = (
                                'fullname', 'age', 'address', 'phone')
                            # Cast age as int since DynamoDB
                            # casts it as Decimal and it is not serializable
                            user1['age'] = int(user1['age'])
                            user2['age'] = int(user2['age'])
                            # Prepare set of friends
                            user1_friends = set(user1['friends'])
                            user2_friends = set(user2['friends'])
                            # Get intersection of friends
                            # to find common
                            common_friends = user1_friends.intersection(
                                user2_friends)
                            # Retrieve all common friends details
                            friends_dframe = self.retrieve_common_friends(
                                common_friends)
                            # If empty just return empty
                            if friends_dframe.empty:
                                friends_dframe = []
                            else:
                                friends_dframe['age'] = friends_dframe[
                                    'age'].astype(int)
                                friends_dframe = friends_dframe[
                                    [
                                        'user_id', 'fullname', 'age',
                                        'address', 'phone', 'eyeColor',
                                        'has_died',
                                    ]
                                ].to_dict(
                                    orient='records'
                                )
                            payload = {
                                'user1': {
                                    k: user1[k] for k in required_keys
                                },
                                'user2': {
                                    k: user2[k] for k in required_keys
                                },
                                'common_friends': friends_dframe
                            }
                            status_code = 200
                        else:
                            # Return error if at least one of the users
                            # is/are not existing
                            payload = {
                                'Error': 'User(s) requested are not existing:'
                                'Existing User({})?: {},'
                                ' Existing User({})?: {}'.format(
                                    request.args['user1'],
                                    user1 is not None,
                                    request.args['user2'],
                                    user2 is not None,
                                )
                            }
                            status_code = 400
                    else:
                        # Return error if one of the required parameters
                        # user1 or user2 is missing
                        payload = {
                            'Error':
                                'One of the required query '
                                'parameters missing. Existing keys: {}'.format(
                                    request.args.keys()
                                )
                        }
                        status_code = 400
                else:
                    # Return error if there are no query parameters to parse
                    # or no user ID to retrieve
                    payload = {
                        'Error': 'No query parameters'
                    }
                    status_code = 400
        except Exception as ex:
            logging.error('Unknown error occured', exc_info=True)
            payload = {'Error': 'Unknown error occured'}
            status_code = 500
        return jsonify(payload), status_code


user_api = UserAPI.as_view('users_api')
company_api = CompanyAPI.as_view('companies')
app.add_url_rule(
    '/users/', view_func=user_api,
    defaults={'user_id': None})
app.add_url_rule(
    '/users/<string:user_id>', view_func=user_api)
app.add_url_rule(
    '/companies/<int:company_id>',
    view_func=company_api)
