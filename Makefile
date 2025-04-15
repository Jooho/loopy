IMG=quay.io/jooholee/loopy
IMG_TAG=latest

PYTEST_CONFIG ?= "pytest.ini"

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
	pytest -c "${PYTEST_CONFIG}" -n 6 --dist worksteal 


.PHONY: update-test-data
update-test-data:
	python hacks/update_test_custom_context_json.py

.PHONY: py-lint
py-lint:
	black ./src ./test	

.PHONY: precommit
precommit: py-lint unit 
