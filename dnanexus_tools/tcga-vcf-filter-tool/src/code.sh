#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Set output file name
if [ -z "${output_vcf}"]; then
    output_vcf="${input_vcf_prefix}.tcga_filtered.vcf"
else
    output_vcf="${output_vcf}.vcf"
fi

echo $filter_text > filter.txt
if [[ "$filterRejects" == "true" ]]; then
	python vcf-filter.py --filter "${input_vcf_path}" filter.txt "${output_vcf}"
else
	python vcf-filter.py "${input_vcf_path}" filter.txt "${output_vcf}"
fi


mkdir -p out/output_vcf
mv "${output_vcf}" "out/output_vcf/"

dx-upload-all-outputs
