FROM    java

RUN     apt-get update
RUN     apt-get install -y wget samtools build-essential git-core cmake zlib1g-dev libncurses-dev

WORKDIR /opt
ENV     JAVA_JAR_PATH   /opt
RUN     wget http://archive.broadinstitute.org/cancer/cga/sites/default/files/data/tools/indelocator/IndelGenotyper.36.3336-GenomeAnalysisTK.jar && mv IndelGenotyper.36.3336-GenomeAnalysisTK.jar IndelGenotyper.jar

