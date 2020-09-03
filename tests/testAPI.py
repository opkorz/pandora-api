"""
Test Cases for Pandora API
"""
import json
from unittest import TestCase, TestLoader, TextTestRunner, mock

from app.app import app


class MockEmptyDynamoResource(object):

    def __init__(self, *args, **kwargs):
        pass

    def query(self, **kwargs):
        return {'Count': 0}


class MockCompanyDynamoResource(MockEmptyDynamoResource):
    user_item = {
        'Items': [{
            'user_id': '123asddv32ef',
            'fullname': 'Tester User',
            'email': 'test@test.com',
            'phone': '+61123123123',
        }],
        'Count': 1
    }

    company_item = {
        'Items': [{
            'pk': 'company',
            'sk': '1#Test#',
            'metadata': {
                'name': 'Test'
            }
        }],
        'Count': 1
    }

    def query(self, **kwargs):
        if kwargs['KeyConditionExpression']._values[0]._values[1] == 'company':
            return self.company_item
        else:
            return self.user_item


class MockUserDynamoResource(MockEmptyDynamoResource):
    user_item = {
        'Items': [{
            'lsi': 'True#False#123asddv32ef',
            'user_id': '123asddv32ef',
            'fullname': 'Tester User',
            'username': 'Tester',
            'email': 'test@test.com',
            'phone': '+61123123123',
            'age': 31,
            'fruits': ['apples', 'oranges'],
            'vegetables': ['okra', 'celery']
        }],
        'Count': 1
    }

    def query(self, **kwargs):
        return self.user_item


class CompanyAPITestCases(TestCase):
    """Test cases for the Company API."""
    url = '/companies/{}'

    def test_company_api_missing_id(self):
        """Test if app returns 404 if company id is not provided."""
        with app.test_client() as client:
            resp = client.get(self.url.format(''))
            self.assertEqual(resp.status_code, 404)

    def test_company_api_invalid_method(self):
        """Test if app returns 405 if company id is not provided."""
        with app.test_client() as client:
            resp = client.post(self.url.format(1))
            self.assertEqual(resp.status_code, 405)

    def test_company_api_company_non_existent(self):
        """Test if app returns 405 if company id is not provided."""
        with app.test_client() as client, mock.patch(
            'app.app.DDB_TABLE',
            MockEmptyDynamoResource()
        ):
            resp = client.get(self.url.format(1))
            self.assertEqual(resp.status_code, 404)
            resp_body = resp.json
            self.assertIn('Error', resp_body)
            self.assertEqual(
                resp_body['Error'],
                'Company being retrieved does not exist'
            )

    def test_company_api_success(self):
        """Test company api successfully returns with data."""
        with app.test_client() as client, mock.patch(
            'app.app.DDB_TABLE',
            MockCompanyDynamoResource()
        ) as mock_table:
            resp = client.get(self.url.format(1))
            self.assertEqual(resp.status_code, 200)
            resp_body = resp.json
            expected_keys = [
                'companyID', 'companyName', 'employees',
                'lastRecord'
            ]
            for key in expected_keys:
                self.assertIn(key, resp_body)
            self.assertEqual(1, resp_body['companyID'])
            self.assertEqual('Test', resp_body['companyName'])
            self.assertNotEqual(len(resp_body['employees']), 0)
            self.assertIsNone(resp_body['lastRecord'])
            entry = resp_body['employees'].pop()
            query_entry = mock_table.user_item['Items'][0]
            for key in query_entry.keys():
                self.assertIn(key, entry)
                self.assertEqual(entry[key], query_entry[key])


class UserAPITestCases(TestCase):
    """Test cases for the User API."""
    url = '/users/{}'

    def test_user_api_invalid_method(self):
        """Test user api returns error for unimplemented method."""
        with app.test_client() as client:
            resp = client.post(self.url.format(1))
            self.assertEqual(resp.status_code, 405)

    def test_user_api_user_non_existent(self):
        """Test user api returns error when user is not existing."""
        with app.test_client() as client, mock.patch(
            'app.app.DDB_TABLE',
            MockEmptyDynamoResource()
        ):
            resp = client.get(self.url.format('ASDASD'))
            self.assertEqual(resp.status_code, 404)

    def test_user_api_user_id_success(self):
        """Test user api successfully returns user details"""
        with app.test_client() as client, mock.patch(
            'app.app.DDB_TABLE',
            MockUserDynamoResource()
        ):
            resp = client.get(self.url.format('123asddv32ef'))
            self.assertEqual(resp.status_code, 200)
            print(resp.json)

    def test_user_api_no_id_no_params(self):
        pass

    def test_user_api_no_id_one_key_missing(self):
        pass

    def test_user_api_no_id_one_user_non_existent(self):
        pass

    def test_user_api_no_id_success(self):
        pass



if __name__ == '__main__':
    loader = TestLoader()
    suite = loader.loadTestsFromTestCase(CompanyAPITestCases)
    suite.addTests(loader.loadTestsFromTestCase(UserAPITestCases))
    TextTestRunner(verbosity=3).run(suite)
