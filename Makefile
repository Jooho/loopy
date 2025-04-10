IMG=quay.io/jooholee/loopy
IMG_TAG=latest

PYTEST_CONFIG ?= "tests/cli/pytest.ini"

.PHONY: build push
build:
	docker build -t ${IMG}:${IMG_TAG} .
push:
	docker push ${IMG}:${IMG_TAG}

.PHONY: download-cli
download-cli:
	./commons/scripts/download-cli.sh

.PHONY: install-lib
install-lib:
	pip install --upgrade pip
	pip install -r requirements.txt
	cat Dockerfile | grep "^RUN dnf" | sed 's/^RUN //'| sh -x

.PHONY: init
init: download-cli install-lib

.PHONY: unit
unit:  
	# pytest tests/cli/commands/test_roles.py
	# pytest tests/cli/commands/test_units.py
	pytest -m "cli" -c "${PYTEST_CONFIG}" -n 1 --dist worksteal 


.PHONY: update-test-data
update-test-data:
	python hacks/update_test_custom_context_json.py