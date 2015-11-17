#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Determine output name if not provided
if [ -z "$output" ]; then
    output="${tumor_prefix}.SomaticSniper.vcf"
    echo "output name was determined to be $output"
else
    output="${output%.vcf}.vcf"
fi

# Prepare optional argument string
optional_args=""
if [ -n "$mapq" ]; then
    optional_args="${optional_args} -q $mapq"
fi

if [ -n "$somaticq" ]; then
    optional_args="${optional_args} -Q $somaticq"
fi

if [[ "$loh" == "true" ]]; then
    optional_args="${optional_args} -L"
fi

if [[ "$gor" == "true" ]]; then
    optional_args="${optional_args} -G"
fi

if [[ "$dis_priors" == "true" ]]; then
    optional_args="${optional_args} -p"
fi

if [[ "use_priorp" == "true" ]]; then
    optional_args="${optional_args} -J"
fi

if [[ -n "$prior_p" ]]; then
    optional_args="${optional_args} -s $prior_p"
fi

python SomaticSniper.py \
    "${tumor_path}" \
    "${normal_path}" \
    mutations.vcf \
    -f "${reference_path}" \
    -t "${tumor_name}" \
    -n "${normal_name}" \
    -F vcf \
    $optional_args \
    --workdir ./


ls
mkdir -p out/vcf
mv "mutations.vcf" "out/vcf/${output}"

dx-upload-all-outputs

