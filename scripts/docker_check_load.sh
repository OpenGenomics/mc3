#!/bin/bash

DOCKER_CMD="docker" #change to 'sudo docker' if needed
DOCKER_IMAGE=$1

python << EOF
import re, tarfile, json, subprocess
t = tarfile.TarFile("$DOCKER_IMAGE")
meta_str = t.extractfile('repositories').read()
meta = json.loads(meta_str)
tag, tag_value = meta.items()[0]
rev, rev_value = tag_value.items()[0]
cmd = "$DOCKER_CMD images --no-trunc"
proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
stdo, stde = proc.communicate()
found = False
for line in stdo.split("\n"):
    tmp = re.split(r'\s+', line)
    if tmp[0] == tag and tmp[1] == rev and tmp[2] == rev_value:
        found = True
        print "Image Already loaded"
if not found:
    print "Loading image"
    cmd = "cat $DOCKER_IMAGE | $DOCKER_CMD load"
    subprocess.check_call(cmd, shell=True)
EOF
