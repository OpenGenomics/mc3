#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

if [ -z "${output}" ]; then
    annotated_output="${vcf_prefix}.annotated.vcf"
    filtered_output="${vcf_prefix}.filtered.vcf"
else
    annotated_output="${output}_annotated.vcf"
    filtered_output="${output}_filtered.vcf"
fi

samtools index "${bam_path}"

# Call to fpfilter
perl ~/fpfilter.pl \
    --vcf-file "${vcf_path}" \
    --bam-file "${bam_path}" \
    --bam-index "${bam_path}.bai" \
    --sample "${sample}" \
    --reference "${reference_path}" \
    --output "${annotated_output}" \
    --min-read-pos "${min_read_pos}" \
    --min-var-freq "${min_var_freq}" \
    --min-var-count "${min_var_count}" \
    --min-strandedness "${min_strandness}" \
    --max-mm-qualsum-diff "${max_mm_qualsum_diff}" \
    --max_var_mm_qualsum "${max_var_mm_qualsum}" \
    --max-mapqual-diff "${max_mapqual_diff}" \
    --max-readlen-diff "${max_readlen_diff}" \
    --min-var-dist-3 "${min_var_dist_3}"


# fpfilter output annotates the FILTER column, we grep
# the lines with PASS to get the entries which passed fpfilter

ls
mkdir -p out/annotated_output

mv "${annotated_output}" "out/annotated_output/"

dx-upload-all-outputs
