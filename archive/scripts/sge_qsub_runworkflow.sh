#!/bin/bash
#$ -S /bin/bash
#$ -cwd
#$ -pe smp 32
#$ -l scratch=4000g


#Where Nebula is installed
NEBULA=`pwd`/nebula/

SERVICE=$1
TASK=$2

hostname > ${TASK}.host
echo "LOADING" > ${TASK}.state
for a in images/*.tar; do
	./scripts/docker_check_load.sh $a
done

export PYTHONPATH=$NEBULA

echo "RUNNING" > ${TASK}.state

$NEBULA/bin/nebula run \
$SERVICE \
$TASK 2> ${TASK}.err > ${TASK}.out

echo "DONE" > ${TASK}.state
