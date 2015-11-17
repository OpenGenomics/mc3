#!/usr/bin/env python2.7

"""Tool to read a TCGA Variant Call Format (VCF) file and output an
equivalent file with a different header.

Returns exit code 1 for bad parameters and 2 for header errors detected.
"""


import argparse
import sys

import yaml
import datetime
import itertools


__version__ = '1.0.0'

# these are the new params
# {'config': {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", Platform="{platform}", 
# Source="dbGAP",Accession="dbGaP", softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan', 
# 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 'software_version': '2.4.0'}, 
# 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, 
# InputVCFSource=<varscan>,InputVCFVer=<4.1>, InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}}

# key config
# value {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", 
# Platform="{platform}", Source="dbGAP",Accession="dbGaP", softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan', 
# 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 'software_version': '2.4.0'}, 
# 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, 
# InputVCFSource=<varscan>,InputVCFVer=<4.1>, InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}

# this is args.parameter {}
# not a duplicate
# {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", Platform="{platform}", Source="dbGAP",Accession="dbGaP", 
# softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan', 
# 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 'software_version': '2.4.0'}, 
# 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, 
# InputVCFSource=<varscan>,InputVCFVer=<4.1>, InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}

# these are the new params
# {'samples': {'TUMOR': {'aliquot_uuid': 'f23b3d0d-26a5-4adf-8aec-4994d094465b', 'aliquot_barcode': 'TCGA-W5-AA33-01A-11D-A417-09', 'platform': 'Illumina', 'analysis_uuid': 'cd5d8895-6b13-450f-993b-bff9943dc0d9', 
# 'description': 'Primary Tumor', 'bam_name': '9a6ebf433eb4bcb93be593f74ffa1d3b.bam'}, 'NORMAL': {'aliquot_uuid': '02e2d8b9-8b5a-4bae-8615-76c46d68f44c', 'aliquot_barcode': 'TCGA-W5-AA33-10A-01D-A41A-09', 'platform': 'Illumina', 
# 'analysis_uuid': '3118c963-8446-4d4a-8146-6d46f1465780', 'reference_genome': 'hg19', 'description': 'Normal sample', 'bam_name': '741377430d1d6a7a567f5425abc41ac2.bam'}}, 'config': {'fixed_headers': [['fileformat', False, 'VCFv4.1'], 
# ['tcgaversion', False, '1.1'], ['phasing', False, 'none'], ['reference', False, 'hg19']]}}

# key samples
# value {'TUMOR': {'aliquot_uuid': 'f23b3d0d-26a5-4adf-8aec-4994d094465b', 'aliquot_barcode': 'TCGA-W5-AA33-01A-11D-A417-09', 'platform': 'Illumina', 'analysis_uuid': 'cd5d8895-6b13-450f-993b-bff9943dc0d9', 
# 'description': 'Primary Tumor', 'bam_name': '9a6ebf433eb4bcb93be593f74ffa1d3b.bam'}, 'NORMAL': {'aliquot_uuid': '02e2d8b9-8b5a-4bae-8615-76c46d68f44c', 'aliquot_barcode': 'TCGA-W5-AA33-10A-01D-A41A-09', 
# 'platform': 'Illumina', 'analysis_uuid': '3118c963-8446-4d4a-8146-6d46f1465780', 'reference_genome': 'hg19', 'description': 'Normal sample', 'bam_name': '741377430d1d6a7a567f5425abc41ac2.bam'}}

# this is args.parameter {'config': {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", 
# Platform="{platform}", Source="dbGAP",Accession="dbGaP", softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 
# 'fixed_sample_params': {'software_name': 'varscan', 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"',
 # 'software_version': '2.4.0'}, 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, 
 # '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, InputVCFSource=<varscan>,InputVCFVer=<4.1>, 
 # InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}}

# not a duplicate
# {'TUMOR': {'aliquot_uuid': 'f23b3d0d-26a5-4adf-8aec-4994d094465b', 'aliquot_barcode': 'TCGA-W5-AA33-01A-11D-A417-09', 'platform': 'Illumina', 'analysis_uuid': 'cd5d8895-6b13-450f-993b-bff9943dc0d9', 
# 'description': 'Primary Tumor', 'bam_name': '9a6ebf433eb4bcb93be593f74ffa1d3b.bam'}, 'NORMAL': {'aliquot_uuid': '02e2d8b9-8b5a-4bae-8615-76c46d68f44c', 'aliquot_barcode': 'TCGA-W5-AA33-10A-01D-A41A-09', 
# 'platform': 'Illumina', 'analysis_uuid': '3118c963-8446-4d4a-8146-6d46f1465780', 'reference_genome': 'hg19', 'description': 'Normal sample', 'bam_name': '741377430d1d6a7a567f5425abc41ac2.bam'}}

# key config
# value {'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['phasing', False, 'none'], ['reference', False, 'hg19']]}
# this is args.parameter {'samples': {'TUMOR': {'aliquot_uuid': 'f23b3d0d-26a5-4adf-8aec-4994d094465b', 'aliquot_barcode': 'TCGA-W5-AA33-01A-11D-A417-09', 'platform': 'Illumina', 'analysis_uuid': 'cd5d8895-6b13-450f-993b-bff9943dc0d9', 
# 'description': 'Primary Tumor', 'bam_name': '9a6ebf433eb4bcb93be593f74ffa1d3b.bam'}, 'NORMAL': {'aliquot_uuid': '02e2d8b9-8b5a-4bae-8615-76c46d68f44c', 'aliquot_barcode': 'TCGA-W5-AA33-10A-01D-A41A-09', 
# 'platform': 'Illumina', 'analysis_uuid': '3118c963-8446-4d4a-8146-6d46f1465780', 'reference_genome': 'hg19', 'description': 'Normal sample', 'bam_name': '741377430d1d6a7a567f5425abc41ac2.bam'}}, 
# 'config': {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", Platform="{platform}", 
# Source="dbGAP",Accession="dbGaP", softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan',
 # 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 'software_version': '2.4.0'}, 
 # 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, 
 # InputVCFSource=<varscan>,InputVCFVer=<4.1>, InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}}

# config is a duplicate
# before the merge occurs
# {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", Platform="{platform}", Source="dbGAP",Accession="dbGaP", 
# softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan', 
# 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 
# 'software_version': '2.4.0'}, 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['center', False, '"wustl.edu"'], ['phasing', False, 'none'], ['vcfProcessLog', False, 
# '<InputVCF=</home/jac/galaxy/galaxy_og/database/files/000/dataset_309.dat>, InputVCFSource=<varscan>,InputVCFVer=<4.1>, 
# InputVCFParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>']]}

#  after the merge occurs
# {'sample_line_format': 'SAMPLE=< ID={id}, Description="{description}", SampleUUID={aliquot_uuid},SampleTCGABarcode={aliquot_barcode}, AnalysisUUID={analysis_uuid},File="{bam_name}", Platform="{platform}", 
# Source="dbGAP",Accession="dbGaP", softwareName=<{software_name}>, softwareVer=<{software_version}>, softwareParam=<{software_params}> >', 'fixed_sample_params': {'software_name': 'varscan', 
# 'software_params': '"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05"', 'software_version': '2.4.0'},
 # 'fixed_headers': [['fileformat', False, 'VCFv4.1'], ['tcgaversion', False, '1.1'], ['phasing', False, 'none'], ['reference', False, 'hg19']]} after the merge occurs



def main():
    args = parse_args()
    args.parameter_map = {}
    # define center and sample specific parameters
    for path in args.parameter_file_path:
        with open(path) as yaml_file:
            new_params = yaml.load(yaml_file)
            for k,v in new_params.items():
                if k in args.parameter_map:
                    for key in args.parameter_map[k]:
                        if key in v:
                            args.parameter_map[k][key] = list(itertools.chain(args.parameter_map[k][key], v[key]))
                    # args.parameter_map[k] = dict(args.parameter_map[k], **v)
                else:
                    args.parameter_map[k] = v
    # TODO: Configure logging
    errors = run(args)
    if errors:
        sys.exit(2)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file_path', help='the VCF to read')
    parser.add_argument('output_file_path', help='the VCF to write')
    parser.add_argument('parameter_file_path', nargs="+", help='the YAML with details')
    args = parser.parse_args()
    return args


def run(args):
    """Main entry point for testing and higher-level automation"""
    CONFIG = args.parameter_map['config']
    fixed_headers = CONFIG['fixed_headers']
    with open(args.input_file_path) as fin:
        with open(args.output_file_path, 'w') as fout:
            write_fixed_headers(fout, fixed_headers)
            write_sample_lines(fout, CONFIG, args.parameter_map['samples'])
            errors = process_headers(fin, fout, fixed_headers)
            for raw_line in fin:
                fout.write(raw_line)
    return errors


def write_fixed_headers(fout, fixed_headers):
    # append fileDate
    fixed_headers.append(['fileDate', False, datetime.date.today().strftime('%Y%m%d')])
    for name, ignored, value in fixed_headers:
        write_meta_line(fout, name, value)


def write_sample_lines(fout, config, samples):
    SAMPLE_LINE_FORMAT = '##' + config['sample_line_format'].replace(' ', '')
    for id, params in samples.items():
        sample_line = SAMPLE_LINE_FORMAT.format(
            id=id, **dict(params, **config['fixed_sample_params'])
        )
        write_stripped_line(fout, sample_line)


def process_headers(fin, fout, fixed_headers):
    """Keep processing until we write the data header line."""
    filtered_headers = set(item[0] for item in fixed_headers)
    filtered_headers.add("SAMPLE")
    expected_values = {
        name: value for name, asserted, value in fixed_headers if asserted
    }
    errors = False
    for raw_line in fin:
        if raw_line.startswith('##'):
            # TODO: This will break if the metadata header is bad.
            name, value = raw_line[2:].rstrip().split('=', 1)
            if name in filtered_headers:
                if name in expected_values:
                    if value != expected_values[name]:
                        errors = True
                        # TODO: propper logging
                        sys.stderr.write(
                            'tcga-vcf-reheader: mismatch {}={}\n'.format(
                                name, value
                            )
                        )
            else:  # Just some other header...
                fout.write(raw_line)
        else:
            break
    fout.write(raw_line.replace('TUMOR','PRIMARY').replace('DNA_NORMAL', 'NORMAL').replace('DNA_PRIMARY', 'PRIMARY'))  # raw_line should now be the data header line.
    return errors


def write_meta_line(fout, name, value):
    fout.write('##{}={}\n'.format(name, value))


def write_stripped_line(fout, line):
    """Just adds the newline."""
    fout.write(line)
    fout.write('\n')


if __name__ == '__main__':
    main()
