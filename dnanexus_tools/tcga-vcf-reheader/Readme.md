# tcga-vcf-reheader-tool

Tool to read a TCGA Variant Call Format (VCF) file and output an equivalent file with a different header

## Requirements

* Python 2.7
* PyYAML

## Usage

`tcga-vcf-reheader.py input_file_path output_file_path parameter_file_path`

* input_file_path: the VCF to read
* output_file_path: the VCF to write
* parameter_file_path: a YAML file describing the additions/changes to the header

Currently only changes to the `##SAMPLE` lines are supported. Any existing `##SAMPLE` lines will be replaced by the ones specified in the YAML file.

**WARNING:** This tool will **completely replace** any existing ##SAMPLE lines. If the parameter file names different samples than were used in the VCF, the resulting output will be a misleading chimeric monster.

## Contributors

* Kyle Ellrott <kellrott@soe.ucsc.edu>
* Walker Hale <hale@bcm.edu>
* Dave Larson <dlarson@genome.wustl.edu>
* Lee Lichtenstein <lichtens@broadinstitute.org>

## Sample YAML config file (with samples info)
```
config:
    sample_line_format:
        SAMPLE=<
        ID={id},
        Description="{description}",
        SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_name}
        AnalysisUUID={analysis_uuid},File="{bam_name}",
        Platform="illumina",
        Source="dbGAP",Accession="dbGaP",
        softwareName=<{software_name}>,
        softwareVer=<{software_version}>,
        softwareParam=<{software_params}>
        >
    fixed_sample_params:
        software_name:      'muTect,CallIndelsPipeline'
        software_version:   '119,65'
        software_params:    '.'
    fixed_headers:  # name, assert, value
        - [fileformat,  True,   'VCFv4.1']
        - [fileDate,    False,  '20140315']
        - [tcgaversion, True,   '1.1']
        - [center,      False,  '"broad.mit.edu"']
        - [phasing,     False,  'none']  # TODO: Think about this one.
samples:
    NORMAL:
        description:    '"Normal sample"'
        analysis_uuid:  3118c963-8446-4d4a-8146-6d46f1465780
        bam_name:       741377430d1d6a7a567f5425abc41ac2.bam
        aliquot_uuid:   02e2d8b9-8b5a-4bae-8615-76c46d68f44c
        aliquot_name:   TCGA-W5-AA33-10A-01D-A41A-09
    PRIMARY:
        description:    '"Primary Tumor"'
        analysis_uuid:  cd5d8895-6b13-450f-993b-bff9943dc0d9
        bam_name:       9a6ebf433eb4bcb93be593f74ffa1d3b.bam
        aliquot_uuid:   f23b3d0d-26a5-4adf-8aec-4994d094465b
        aliquot_name:   TCGA-W5-AA33-01A-11D-A417-09
```
