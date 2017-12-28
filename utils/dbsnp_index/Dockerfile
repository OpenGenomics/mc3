FROM    ubuntu

RUN     apt-get update
RUN     apt-get install -y python wget python-pip python-dev zlib1g-dev libncurses-dev
RUN     pip install bx-python
WORKDIR /opt
RUN     wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2 && tar -xvjf samtools-1.3.1.tar.bz2 && rm -f samtools-1.3.1.tar.bz2
RUN     cd /opt/samtools-1.3.1/htslib-1.3.1/  && make 
