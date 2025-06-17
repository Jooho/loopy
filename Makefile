IMG=quay.io/jooholee/loopy
IMG_TAG=latest

PYTEST_CONFIG ?= pytest.ini
TEST_ENV ?= local
PYTEST_ARGS ?= -n 3 --dist=loadscope

.PHONY: build push
build:
	docker build -t ${IMG}:${IMG_TAG} .
push:
	docker push ${IMG}:${IMG_TAG}

.PHONY: download-cli
download-cli:
	./hacks/download-cli.sh $${TEST_ENV}


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
e2e: download-cli	
	export PATH="$(CURDIR)/bin:$(PATH)" ;\
	echo "TEST_ENV is $(TEST_ENV)" 	;\
	echo "PATH is $$PATH" ;\
	TEST_ENV=$(TEST_ENV) ./hacks/setup-kind.sh ;\
	pytest -c "${PYTEST_CONFIG}" -n 5 --dist worksteal -m e2e


.PHONY: e2e-cluster-lifecycle 
e2e-cluster-lifecycle: download-cli	
	export PATH="$(CURDIR)/bin:$(PATH)" ;\
	if [ -n "$(NEW_PYTEST_ARGS)" ]; then \
		FINAL_PYTEST_ARGS="$(NEW_PYTEST_ARGS)"; \
	else \
		FINAL_PYTEST_ARGS="$(PYTEST_ARGS)"; \
	fi ;\
	pytest -c "${PYTEST_CONFIG}" $$FINAL_PYTEST_ARGS -m "(${CLUSTER_TYPE}) and cluster_lifecycle_tests"


.PHONY: update-test-data
update-test-data:
	python hacks/update_test_custom_context_json.py

.PHONY: py-lint
py-lint:
	black ./src ./tests 

.PHONY: precommit
precommit: py-lint fvt 
