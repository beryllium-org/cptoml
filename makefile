SHELL = bash
all:
	@echo -e "CPToml builder.\n\nUsage:\n\tmake mpy\n\tmake clean"
update_modules:
	@echo "Updating git submodules from remotes.."
	@git submodule update --init --recursive --remote .
	@echo -e "Submodules ready\n\nMake sure to git commit before procceding to make!!"
modules:
	@echo "Preparing git submodules.."
	@git submodule update --init --recursive .
	@echo "Submodules ready"
mpy: modules
	@python resources/make.py
clean:
	@if [ -e "cptoml.mpy" ]; then rm cptoml.mpy; fi
