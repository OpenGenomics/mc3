FROM java:7

RUN apt-get update
RUN apt-get install -y zip wget

# We'll be working in /opt from now on
WORKDIR /opt
RUN wget https://github.com/broadinstitute/picard/releases/download/1.122/picard-tools-1.122.zip
RUN unzip picard-tools-1.122.zip && rm -f picard-tools-1.122.zip

# Link the picard tools to /opt/picard
RUN ln -s picard-tools-1.122 picard
