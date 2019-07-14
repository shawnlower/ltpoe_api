dev:
	FLASK_APP=ltpapi FLASK_ENV=development pipenv run flask run

test:
	pipenv run python -m pytest

integration:
	pipenv run python -m pytest -k integration -v
