#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Set output file name
if [ -z "${output_vcf}" ]; then
    output_vcf="${input_vcf_prefix}.reheadered.vcf"
else
    output_vcf="${output_vcf}.vcf"
fi

cat << EOF > config.yml
config:
    sample_line_format:
        SAMPLE=<
        ID={id},
        Description="{description}",
        SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode},
        AnalysisUUID={analysis_uuid},File="{bam_name}",
        Platform="{platform}",
        Source="dbGAP",Accession="dbGaP",
        softwareName=<{software_name}>,
        softwareVer=<{software_version}>,
        softwareParam=<{software_params}>
        >
    fixed_sample_params:
      software_name:      '${software_name}'
      software_version:   '${software_version}'
      software_params:    '"${software_params}"'
    fixed_headers:  # name, assert, value
        - [fileformat,  False,   'VCFv4.1']
        - [tcgaversion, False,   '1.1']
        - [phasing,     False,  'none']  # TODO: Think about this one.
        - [center,      False,  '"${center}"']
        - [vcfProcessLog,   False,  '<InputVCF=<${input_vcf_name}>, InputVCFSource=<${software_name}>,InputVCFVer=<4.1>, InputVCFParam=<"${software_params}">>']
EOF

if [ -z "$info_file" ]; then
    # Append sample information to yml if info_file not provided
    cat << EOF >> config.yml
        - [reference, False, '${reference_genome}']
        - [participant_uuid,  False,  '${participant_uuid}']
        - [disease_code, False, '${disease_code}']
samples:
    NORMAL:
        description:     'Normal sample'
        analysis_uuid:   ${normal_analysis_uuid}
        bam_name:        ${normal_bam_name}
        aliquot_uuid:    ${normal_aliquot_uuid}
        aliquot_barcode: ${normal_aliquot_barcode}
        platform:        ${platform}
    PRIMARY:
        description:    'Primary Tumor'
        analysis_uuid:   ${tumor_analysis_uuid}
        bam_name:        ${tumor_bam_name}
        aliquot_uuid:    ${tumor_aliquot_uuid}
        aliquot_barcode: ${tumor_aliquot_barcode}
        platform:        ${platform}
EOF
    # End of yml creation
    python ~/tcga-vcf-reheader.py "${input_vcf_path}" "${output_vcf}" config.yml
else
    # Pass info_file as input to vcf-reader.py
    python ~/tcga-vcf-reheader.py "${input_vcf_path}" "${output_vcf}" config.yml "${info_file_path}"
fi

cat config.yml

ls
mkdir -p out/output_vcf
mv "${output_vcf}" "out/output_vcf/"

dx-upload-all-outputs
