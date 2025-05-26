IMG=quay.io/jooholee/loopy
IMG_TAG=latest

PYTEST_CONFIG ?= "pytest.ini"
TEST_ENV ?= "local"

.PHONY: build push
build:
	docker build -t ${IMG}:${IMG_TAG} .
push:
	docker push ${IMG}:${IMG_TAG}

.PHONY: download-cli
download-cli:
	./hacks/download-cli.sh

.PHONY: download-cli-for-ci
download-cli-for-ci:
	./hacks/download-cli-for-ci.sh

.PHONY: install-lib
install-lib:
	pip install --upgrade pip
	pip install -r requirements.txt
	cat Dockerfile | grep "^RUN dnf" | sed 's/^RUN //'| sh -x

.PHONY: init
init: download-cli install-lib

.PHONY: fvt
fvt:  
	pytest -c "${PYTEST_CONFIG}" -n 1 -m fvt
	

.PHONY: e2e 
e2e: download-cli-for-ci	
	export PATH="$(CURDIR)/bin:$(PATH)" ;\
	echo "TEST_ENV is $(TEST_ENV)" 	;\
	echo "PATH is $$PATH" ;\
	TEST_ENV=$(TEST_ENV) ./hacks/setup-kind.sh ;\
	pytest -c "${PYTEST_CONFIG}" -n 5 --dist worksteal -m e2e

.PHONY: update-test-data
update-test-data:
	python hacks/update_test_custom_context_json.py

.PHONY: py-lint
py-lint:
	black ./src ./tests 

.PHONY: precommit
precommit: py-lint fvt 
