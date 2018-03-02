FROM ubuntu

RUN apt-get --fix-missing update
RUN apt-get install -y g++ libbz2-dev liblzma-dev libncurses5-dev make python python-pip python-dev wget zlib1g-dev

WORKDIR /opt

RUN wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2 && tar -xvjf samtools-1.3.1.tar.bz2 && rm -f samtools-1.3.1.tar.bz2 && cd /opt/samtools-1.3.1/ && make && make install
RUN     cd /opt/samtools-1.3.1/htslib-1.3.1/  && make && make install
