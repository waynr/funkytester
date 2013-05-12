#!/bin/bash


eval `resize`

while test 1 ;do
	./bin/ge_pytest.py -c tests/ge_evsc/conf/default.yaml
done
