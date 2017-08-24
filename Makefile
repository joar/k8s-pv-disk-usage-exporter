.PHONY: default
default:

.PHONY: mypy
mypy:
	env MYPYPATH=$(shell pwd)/stubs \
		mypy \
		--ignore-missing-imports \
		disk_usage_exporter \
		--html-report \
		scratch/mypy-report

