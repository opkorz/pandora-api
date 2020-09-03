# Pandora Challenge
Pandora is a mysterious planet. Those types of planets can support human life, for that reason the president of the Handsome Jack decides to send some people to colonise this new planet and
reduce the number of people in their own country. After 10 years, the new president wants to know how the new colony is growing, and wants some information about his citizens. Hence he hired you to build a rest API to provide the desired information.

The government from Pandora will provide you two json files (located at resource folder) which will provide information about all the citizens in Pandora (name, age, friends list, fruits and vegetables they like to eat...) and all founded companies on that planet.
Unfortunately, the systems are not that evolved yet, thus you need to clean and organise the data before use.
For example, instead of providing a list of fruits and vegetables their citizens like, they are providing a list of favourite food, and you will need to split that list (please, check below the options for fruits and vegetables).

## New Features
Your API must provides these end points:
- Given a company, the API needs to return all their employees. Provide the appropriate solution if the company does not have any employees.
- Given 2 people, provide their information (Name, Age, Address, phone) and the list of their friends in common which have brown eyes and are still alive.
- Given 1 people, provide a list of fruits and vegetables they like. This endpoint must respect this interface for the output: `{"username": "Ahi", "age": "30", "fruits": ["banana", "apple"], "vegetables": ["beetroot", "lettuce"]}` 

## Prerequisites
- Docker Engine >= 19.03.0+
- docker-compose >= 1.10.0

## Setup
To be able to build the api image, you'll need to run:
```
docker-compose build pandora --build-arg COMPANIES_FILE_PATH=/path/to/companies.json --build-arg PEOPLE_FILE_PATH=/path/to/people.json
```
or
```
docker build -t pandora-build . --build-arg --build-arg COMPANIES_FILE_PATH=/path/to/companies.json --build-arg PEOPLE_FILE_PATH=/path/to/people.json
```
If you mix up the 2 paths, data will not be loaded properly

## Running the API
You can run the API by running this command:
```
docker-compose up (-d) if you want to run in daemon
```
This command will load data into the data store and the API will deploy on port 5000 of your localhost

## API Endpoints
- `/companies/<int:company_id>` - This endpoint will return a company's details and its employees
- `/users/<string:user_id>` - This endpoint will return some of the user's details including their favourite fruits and vegetables
- `/users/` - Requiring the query parameters `user1` and `user2` corresponding to user IDs, this will endpoint will return the two user's details and common friends that has brown eyes and are still alive.

## Sample API calls
### Company API
```
curl "http://localhost:5000/companies/1"
```
### User API with ID
```
curl "http://localhost:5000/users/595eeb9b96d80a5bc7afb106"
```
### User API with query parameters
```
curl "http://localhost:5000/users/?user1=595eeb9b96d80a5bc7afb106&user2=595eeb9b1e0d8942524c98ad"
```