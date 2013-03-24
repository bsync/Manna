.phony: test
test: local.properties Meribah/local.properties emulator assets
	cd Meribah; ant debug install test 

.phony: install  
install:	${HOME}/.android/avd/default.ini emulator build
	ant installd 

EMU:=$(shell pgrep -f mannadroid)
.phony: emulator
emulator: ${HOME}/.android/avd/mannadroid.ini
	[ "x$(EMU)" != "x" ] || setsid emulator @mannadroid &
	[ "x$(EMU)" != "x" ] || echo "Wait for emulator and try again."
	[ "x$(EMU)" != "x" ] 

.phony: build
build: assets local.properties 
	ant debug 

${HOME}/.android/avd/mannadroid.ini: 
	#You need to create an avd for Manna dev as follows:
	#android create avd -n mannadroid -t <target>
	#where <target> is one of the targets on your system
	#List targets with: android list targets
	[ -f ${HOME}/.android/avd/mannadroid.ini ] 

Meribah/local.properties:
	(cd Meribah; android update test-project -p . -m ..)

local.properties:
	android update project -p .

assets: .flags/xmlwriter chaptize.pl
	perl chaptize.pl
	touch assets

.flags/xmlwriter: .flags .flags/cpanminus
	cpanm XML::Writer
	touch $@

.flags/cpanminus: .flags
	cpan App::cpanminus
	touch $@

.flags:
	mkdir .flags

.phony: clean
clean:
	rm -rf bin/classes Meribah/bin/classes
