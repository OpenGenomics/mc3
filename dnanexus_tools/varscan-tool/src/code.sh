#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Prepare optional command args
if [ -n "${min_coverage_normal}" ]; then
    min_coverage_normal="--min-coverage-normal $min_coverage_normal"
fi

if [ -n "${min_coverage_tumor}" ]; then
    min_coverage_tumor="--min-coverage-tumor $min_coverage_tumor"
fi

if [ -n "${normal_purity}" ]; then
    normal_purity="--normal-purity $normal_purity"
fi

if [ -n "${tumor_purity}" ]; then
    tumor_purity="--tumor-purity $tumor_purity"
fi

if [[ "$strand_filter" == "true" ]]; then
    strand_filter="--strand-filter"
else
    strand_filter=""
fi

if [[ "$validation" == "true" ]]; then
    validation="--validation"
else
    validation=""
fi

# Determine output name if not provided
if [ -z "$output" ]; then
    output="$tumor_pileup_prefix"
    output="${output%.pileup}"
    output="${output%.mpileup}.varscan"
    echo "output name was determined to be $output"
fi

# Varscan call through wrapper
python VarScanSomaticVcf.py \
    "${normal_pileup_path}" \
    "${tumor_pileup_path}" \
    --min-coverage $min_coverage \
    $min_coverage_normal \
    $min_coverage_tumor \
    --min-var-freq $min_var_freq \
    --min-freq-for-hom $min_freq_for_hom \
    $normal_purity \
    $tumor_purity \
    --p-value $p_value \
    --somatic-p-value $somatic_p_value \
    $strand_filter \
    $validation \


ls
mkdir -p out/snp_vcf
mkdir -p out/indel_vcf

mv "somatic_output.snp.vcf" "out/snp_vcf/${output}.snp.vcf"
mv "somatic_output.indel.vcf" "out/indel_vcf/${output}.indel.vcf"

dx-upload-all-outputs
