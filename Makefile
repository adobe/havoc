VENV_DIR="havoc_venv"
PWD=$(shell pwd)

BIN=${VENV_DIR}/bin/python havoc/app.py

run:
	${BIN} \
		--template=tests/templates/haproxy.havoc.tmpl \
		--haproxy-cfg=tests/haproxy.cfg \
		--pools=rtb-bidder-generic,rtb-bidder-display \
		--debug

run_cli:
	${BIN} \
		--cli \
		--template tests/templates/haproxy.havoc.tmpl \
		--haproxy-cfg tests/haproxy.cfg \
		--pools "rtb-bidder-generic,rtb-bidder-display" \
		--debug

run_dry:
	${BIN} --cli --dry-run --template=tests/templates/haproxy.havoc.tmpl --pools=rtb-bidder-generic,rtb-bidder-display --debug

run_dry_conf:
	${BIN} --debug --cli --dry-run --config tests/havoc.yaml

run_help:
	${BIN} --help

run_10sec:
	if [ -f ${PWD}/tests/havoc.pid ] ; then rm tests/havoc.pid ; fi
	${BIN} --daemonize \
		--interval 10sec \
		--pidfile ${PWD}/tests/havoc.pid \
		--logfile ${PWD}/tests/havoc.log \
		--template ${PWD}/tests/templates/haproxy.havoc.tmpl \
		--haproxy-cfg ${PWD}/tests/haproxy.cfg \
		--pools "rtb-bidder-generic,rtb-bidder-display" \
		--debug

kill:
	if [ -f ${PWD}/tests/havoc.pid ] ; then kill -9 `cat ${PWD}/tests/havoc.pid` ; fi

lint:
	${VENV_DIR}/bin/pylint havoc/*.py

venv:
	virtualenv -p python3 havoc_venv

install:
	${VENV_DIR}/bin/pip install -r requirements.txt

setup:
	${VENV_DIR}/bin/python setup.py install

.PHONY: clean
clean:
	if [ -d ${VENV_DIR} ] ; then rm -rf ${VENV_DIR} ; fi
