.phony: test
test: install Meribah/local.properties 
	cd Meribah; ant installd test 

EMU:=$(shell pgrep -f mannadroid)
.phony: install  
install:	${HOME}/.android/avd/mannadroid.ini build
	[ "x$(EMU)" != "x" ] || setsid emulator @mannadroid &
	[ "x$(EMU)" != "x" ] || echo "Wait for emulator and try again."
	[ "x$(EMU)" != "x" ] 
	ant installd 

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
