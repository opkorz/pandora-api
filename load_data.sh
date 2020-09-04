#!/bin/bash

# load data into dynamoDB tables
python scripts/load_data.py `pwd`/resources/companies.json `pwd`/resources/people.json