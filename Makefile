.phony: test
test: assets
	cd Meribah; ant debug install test 

.phony: build
build:
	ant debug install

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
