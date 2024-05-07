IMG=quay.io/jooholee/loopy
IMG_TAG=latest

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
	pip install -r requirements.txt

.PHONY: init
init: download-cli install-lib
