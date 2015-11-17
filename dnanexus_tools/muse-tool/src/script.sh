#!/bin/bash

PATH=$PATH:/opt/bin

set -e -x -o pipefail

dx-download-all-inputs --parallel

#samtools faidx "${reference_name}"
if [[ "$dbsnp" != "" ]]
then
  #tabix -p vcf "$dbsnp_path"
  gunzip "$dbsnp_path"
  dbsnp_path=${dbsnp_path%.gz}
  options="-D $dbsnp_path $options"
fi

#move bai to be in same directory as bam
mv "${tumor_bai_path}" ~/in/tumor_bam/
mv "${normal_bai_path}" ~/in/normal_bam/

muse.py \
  --tumor-bam "${tumor_bam_path}" \
  --tumor-bam-index "${tumor_bai_path/tumor_bai/tumor_bam}" \
  --normal-bam "${normal_bam_path}" \
  --normal-bam-index "${normal_bai_path/normal_bai/normal_bam}" \
  -f "${reference_path}" \
  -m "${muse}" \
  --mode "${mode}" \
  $options \
  -n `nproc`

ls
mkdir -p out/mutations
mv out.vcf "out/mutations/${tumor_bam_name%.bam}.muse.vcf"
dx-upload-all-outputs

