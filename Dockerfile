from python:3.8
RUN pip install --upgrade pip

WORKDIR /opt/pandora
ADD ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG COMPANIES_FILE_PATH=./resources/companies.json
ARG PEOPLE_FILE_PATH=./resources/people.json
ADD ./load_data.sh load_data.sh
ADD ./run_tests.sh run_tests.sh
ADD ./app app/
ADD ./scripts scripts/
ADD ./resources/fruits-veg.csv resources/fruits-veg.csv
ADD ./tests tests/
ADD $COMPANIES_FILE_PATH ./resources/companies.json
ADD $PEOPLE_FILE_PATH ./resources/people.json