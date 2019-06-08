dev:
	FLASK_APP=ltpapi FLASK_ENV=development flask run

test:
	python -m pytest

integration:
	python -m pytest -k integration -v
