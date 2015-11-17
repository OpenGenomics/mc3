all: radiaremote radialocal

radiaremote:
	mkdir -p resources/usr/bin
	wget -O resources/usr/bin/blat http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64.v287/blat/blat
	chmod +x resources/usr/bin/blat
	mkdir -p resources/home/dnanexus/
	wget -O resources/home/dnanexus/v1.1.5.tar.gz https://github.com/ucscCancer/radia/archive/v1.1.5.tar.gz
	wget -O resources/home/dnanexus/snpEff_latest_core.zip http://downloads.sourceforge.net/project/snpeff/snpEff_latest_core.zip
	cd resources/home/dnanexus/; tar -xvzf v1.1.5.tar.gz
	cd resources/home/dnanexus/; unzip snpEff_latest_core.zip
	cd resources/home/dnanexus/; rm -rf v1.1.5.tar.gz snpEff_latest_core.zip snpEff/galaxy snpEff/examples

radialocal:
	mkdir -p resources/home/dnanexus
	cp ../../tools/radia-tool/radia.py resources/home/dnanexus
	cp ../../tools/radia-tool/radia_filter.py resources/home/dnanexus

clean:
	rm resources/usr/bin/blat
	rm -r resources/home/dnanexus/*
