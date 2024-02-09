
.PHONY: download-cli
download-cli:
	./commons/scripts/download-cli.sh

.PHONY: install-lib
install-lib:
	pip install -r requirements.txt

.PHONY: init
init: download-cli install-lib

