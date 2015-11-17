#!/usr/bin/env python

import argparse
import os
import logging
import subprocess
import re
import sys
from datetime import date
from urlparse import urlparse, urlunparse

"""Run VarScan somatic VCF"""

def argparser():
    parser = argparse.ArgumentParser(description='Run VarScan somatic with VCF output')
    parser.add_argument('normal_pileup', help='normal pileup file')
    parser.add_argument('tumor_pileup', help='tumor pileup file')

    parser.add_argument('--min-coverage', help='minimum coverage')
    parser.add_argument('--min-coverage-normal', help='minimum coverage in the normal')
    parser.add_argument('--min-coverage-tumor', help='minimum coverage in the tumor')
    parser.add_argument('--min-var-freq', help='minumum vaf for a variant')
    parser.add_argument('--min-freq-for-hom', help='minimum vaf to call a variant homozygous')
    parser.add_argument('--normal-purity', help='normal purity')
    parser.add_argument('--tumor-purity', help='tumor purity')
    parser.add_argument('--p-value', help='maximum p-value to call a variant')
    parser.add_argument('--somatic-p-value', help='maximum p-value to call a somatic variant')
    parser.add_argument('--strand-filter', action='store_true', help='apply filter on strand bias')
    parser.add_argument('--validation', action='store_true', help='run in validation mode')
    parser.add_argument('--jar-file', default='/opt/VarScan.jar', help='path to VarScan jar file')
    return parser

def wrapper_specific_arguments():
    return set(('tumor_pileup', 'normal_pileup', 'jar_file'))

def create_opts(namespace_dict):
    args = []
    flag_opts = set(('strand_filter','validation'))
    wrapper_arguments = wrapper_specific_arguments()

    for option, value in namespace_dict.items():
        if option in wrapper_arguments or value == None:
            continue
        if (option in flag_opts):
            if value:
                args.append("--" + option + ' 1')
        else:
            args.append("--" + option.replace('_','-') + " " + str(value))
    return " ".join(args)

def create_cmdline(namespace_dict):
    return " ".join([
        "java -Xmx7g -jar",
        namespace_dict['jar_file'],
        "somatic",
        namespace_dict['normal_pileup'],
        namespace_dict['tumor_pileup'],
        "temp_output",
        "--output-vcf 1",
        create_opts(namespace_dict)])

def reheader_vcf(options, original_vcf_file, new_vcf_file):
    outfile = open(new_vcf_file, 'w')
    original = open(original_vcf_file, 'r')
    for line in original:
        if line.startswith("#"):
            if line.startswith("##INFO"):
                outfile.write(fix_info_header_for_tcga(line))
            if line.startswith("##FORMAT"):
                outfile.write(fix_format_header_for_tcga(line))
            if line.startswith("#CHROM"):
                # Hacked a bit below, but these will use our look up tables
                # to add these to the header
                outfile.write(add_format_header_for_tcga('BQ'))
                outfile.write(add_format_header_for_tcga('SS'))
                outfile.write(add_filter_header('str10')) #add in header for strand filter since VarScan doesn't itself
                outfile.write(line)
        else:
            if re.search('SOMATIC', line):
                outfile.write(fix_body(line))
    outfile.close()
    original.close()

def add_format_header_for_tcga(key):
    LUT = { 
               'BQ': '##FORMAT=<ID=BQ,Number=.,Type=Integer,Description="Average base quality for reads supporting alleles">',
               'SS': '##FORMAT=<ID=SS,Number=1,Type=Integer,Description="Variant status relative to non-adjacent Normal,0=wildtype,1=germline,2=somatic,3=LOH,4=post-transcriptional modification,5=unknown">',
             }
    return LUT[key] + '\n'

def add_filter_header(key):
    LUT = { 
               'str10': '##FILTER=<ID=str10,Description="Fails VarScan Strand Filter">',
             }
    return LUT[key] + '\n'

def fix_info_header_for_tcga(line):
    """Move SS from INFO to FORMAT"""
    fixLUT = { 'DP': '##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth across samples">',
               'SS': '##INFO=<ID=SS,Number=1,Type=Integer,Description="Variant status relative to non-adjacent Normal,0=wildtype,1=germline,2=somatic,3=LOH,4=post-transcriptional modification,5=unknown">'
             }
    for key in fixLUT:
        if line.startswith('##INFO=<ID=' + key + ','):
            return fixLUT[key] + '\n'
    return line

def fix_format_header_for_tcga(line):
    fixLUT = { 'DP': '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read depth at this position in the sample">',
               'DP4': '##FORMAT=<ID=DP4,Number=4,Type=Integer,Description="Number of high-quality ref-forward, ref-reverse, alt-forward and alt-reverse bases">',
               'GQ': '##FORMAT=<ID=GQ,Number=.,Type=Integer,Description="Conditional Phred-scaled genotype quality">',
               'BQ': '##FORMAT=<ID=BQ,Number=.,Type=Integer,Description="Average base quality for reads supporting alleles">',
               'MQ': '##FORMAT=<ID=GMQ,Number=1,Type=Integer,Description="Average mapping quality across all reads">',
               'SS': '##FORMAT=<ID=SS,Number=1,Type=Integer,Description="Variant status relative to non-adjacent Normal,0=wildtype,1=germline,2=somatic,3=LOH,4=post-transcriptional modification,5=unknown">',
               'AD': '##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Depth of reads supporting alleles 0/1/2/3...">'
             }
    for key in fixLUT:
        if line.startswith('##FORMAT=<ID=' + key + ','):
            return fixLUT[key] + '\n'
    return line

def fix_body(line):
    """Move SS from INFO to FORMAT. Add BQ null value to each entry"""
    line = line.strip()
    fields = line.split('\t')
    p = re.compile('SS=(\d+)')
    m = p.search(fields[7])
    if m == None:
        raise ValueError("Couldn't find SS string in INFO line for line: " + line)

    fields[8] = fields[8] + ':BQ:SS'
    for i, field in enumerate(fields[9:]):
        fields[i+9] = fields[i+9] + ':.:' + m.group(1)
    return '\t'.join(fields) + '\n'

def execute(options):
    cmd = create_cmdline(options)

    logging.info("RUNNING: %s" % (cmd))
    print "running", cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()
    if len(stderr):
        print stderr
    return p.returncode

if __name__ == "__main__":
    parser = argparser()
    args = parser.parse_args()
    arg_dict = vars(args)

    execute(arg_dict)
    reheader_vcf(arg_dict, 'temp_output.snp.vcf', 'somatic_output.snp.vcf')
    reheader_vcf(arg_dict, 'temp_output.indel.vcf', 'somatic_output.indel.vcf')
