.phony: test
test: build 
	cd Meribah; ant test 

.phony: build
build: assets local.properties ${HOME}/.android/avd/manna.ini 
	#[ -f ${HOME}/.android/avd/manna.ini ] || exit
	ant debug install

${HOME}/.android/avd/manna.ini: 
	#You need to create an avd for Manna dev as follows:
	#android create avd -n manna -t <target>
	#where <target> is one of the targets on your system
	#List targets with: android list targets

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
