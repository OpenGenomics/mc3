#!/bin/bash

PATH=$PATH:/opt/bin

set -e -x -o pipefail

dx-download-all-inputs --parallel

mkdir -p out/output_vcf
mkdir -p out/filtered_output_vcf

if [[ "$patient_id" != "" ]]
then
  radia_options="--patientId $patient_id $radia_options"
  radia_filter_options="--patientId $patient_id $radia_filter_optins"
fi

if [[ "$fasta_path" == *.gz ]]
then
  gunzip "$fasta_path"
  fasta_path=${fasta_path%.gz}
  fasta_name=${fasta_name%.gz}
fi

if [[ "$dnaTumorBai" != "" ]]
then
  dnaTumor="--dnaTumorFilename ${dnaTumor_path} --dnaTumorBaiFilename ${dnaTumorBai_path}"
else
  dnaTumor="--dnaTumorFilename ${dnaTumor_path}"
fi

if [[ "$dnaNormalBai" != "" ]]
then
  dnaNormal="--dnaNormalFilename ${dnaNormal_path} --dnaNormalBaiFilename ${dnaNormalBai_path}"
else
  dnaNormal="--dnaNormalFilename ${dnaNormal_path}"
fi

if [[ "$rnaTumorBam" != "" ]]
then
  if [[ "$rnaTumorBai" != "" ]]
  then
    rnaTumor="--rnaTumorFilename ${rnaTumor_path} --rnaTumorBaiFilename ${rnaTumorBai_path}"
  else
    rnaTumor="--rnaTumorFilename ${rnaTumor_path}"
  fi
fi

if [[ "$rnaNormalBam" != "" ]]
then
  if [[ "$rnaNormalBai" != "" ]]
  then
    rnaNormal="--rnaNormalFilename ${rnaNormal_path} --rnaNormalBaiFilename ${rnaNormalBai_path}"
  else
    rnaNormal="--rnaNormalFilename ${rnaNormal_path}"
  fi
fi


mkdir radiatemp
cd radiatemp
python ~/radia.py \
  $dnaTumor \
  $dnaNormal \
  $rnaTumor \
  $rnaNormal \
  --fastaFilename "${fasta_path}" \
  $radia_options \
  --outputDir ~/radiatemp/ \
  -o output.vcf \
  --scriptsDir ~/radia-1.1.5/scripts/ \
  --patientId 20c31348-e871-4abb-8ec6-5124f8d0170e \
  --number_of_procs `nproc`
mv output.vcf ~/out/output_vcf/output.radia.vcf
cd ..

mkdir radiafiltertemp
cd radiafiltertemp
python ~/radia_filter.py \
  --inputVCF ~/out/output_vcf/output.radia.vcf \
  --dnaNormalFilename "${dnaNormal_path}" \
  --dnaTumorFilename "${dnaTumor_path}" \
  --fastaFilename "${fasta_path}" \
  $radia_filter_options \
  --outputDir ~/radiafiltertemp/ \
  -o filtered.vcf \
  --scriptsDir /home/dnanexus/radia-1.1.5/scripts/ \
  --patientId 20c31348-e871-4abb-8ec6-5124f8d0170e \
  --number_of_procs `nproc`
mv filtered.vcf ~/out/filtered_output_vcf/filtered.radia.vcf
cd ..

dx-upload-all-outputs

