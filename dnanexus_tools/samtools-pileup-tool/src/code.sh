#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

function change_boolean_str() {
    case $1 in
        true) echo yes ;;
        false) echo no ;;
        *) echo "Unexpected boolean value \"$1\"" 1>&2; exit 1 ;;
    esac
}

if [ -z "$output1" ]; then
    output1="$input1_prefix"
    echo "output name was determined to be $output1"
fi

# Removed consensus calling mode since it's not used in varscan pipeline
# and the wrapper is latently broken (-c flag not supported in v1.2 samtools)
python ~/sam_pileup.py \
    --input1="${input1_path}" \
    --output1="${output1}" \
    --ref=history \
    --ownFile="${reference_path}" \
    --bamIndex="${input1_index_path}" \
    --lastCol="$(change_boolean_str "${lastCol}")" \
    --indels="$(change_boolean_str "${indels}")" \
    --nobaq="$(change_boolean_str "${noBaq}")" \
    --mapqMin="${minMapq}" \
    --cpus=`nproc`

ls
mkdir -p out/pileup
mv "${output1}" "out/pileup/${output1}.pileup"

dx-upload-all-outputs

