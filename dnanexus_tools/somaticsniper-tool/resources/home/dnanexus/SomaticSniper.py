#!/usr/bin/env python

import argparse
import os
import logging
import subprocess
from datetime import date
from urlparse import urlparse, urlunparse

"""This script runs SomaticSniper"""

def sniper_argparser():
    parser = argparse.ArgumentParser(description='Run SomaticSniper')
    parser.add_argument('-f', metavar='REFERENCE', required=True, help='reference sequence in the FASTA format')
    parser.add_argument('-q', required=False, metavar='MAPQ', type=int, help='filtering reads with mapping quality less than [%(default)s]', default=0)
    parser.add_argument('-Q', required=False, metavar='SOMATICQ', type=int, help='filtering somatic snv output with somatic quality less than [%(default)s]', default=15)
    parser.add_argument('-L', required=False, action='store_true', help='do not report LOH variants as determined by genotypes')
    parser.add_argument('-G', required=False, action='store_true', help='do not report Gain of Reference variants as determined by genotypes')
    parser.add_argument('-p', required=False, action='store_true', help='disable priors in the somatic calculation. Increases sensitivity for solid tumors')
    parser.add_argument('-J', required=False, action='store_true', help='Use prior probabilities accounting for the somatic mutation rate')
    parser.add_argument('-s', required=False, metavar='SOMATIC_PRIOR',type=float, help='prior probability of a somatic mutation (implies -J) [%(default)s]', default=0.01)
    parser.add_argument('-r', required=False, metavar='GERMLINE_PRIOR', type=float, help='prior of a difference between two haplotypes [%(default)s]', default=0.001)
    parser.add_argument('-n', required=False, metavar='NORMAL_NAME', help='normal sample id (for VCF header) [%(default)s]', default='NORMAL')
    parser.add_argument('-t', required=False, metavar='TUMOR_NAME', help='tumor sample id (for VCF header) [%(default)s]', default='TUMOR')
    parser.add_argument('-F', required=False, metavar='FORMAT', choices=('classic', 'vcf', 'bed'), help='select output format [%(default)s]', default='vcf')
    parser.add_argument('tumor_bam', help='tumor BAM file')
    parser.add_argument('normal_bam', help='normal BAM file')
    parser.add_argument('output', help='Output file')

    group = parser.add_argument_group('wrapper specific options')
    group.add_argument('--workdir', default='/tmp/', help='Working directory of the wrapper')
    group.add_argument('--reference-id', dest='reference_id', help='TCGA name of the reference', choices=['hg18', 'hg19', 'GRCh37', 'GRCh37-lite', '36', '36.1', '37'])
    group.add_argument('--tumor-uuid', dest='tumor_uuid', help='Tumor Sample uuid')
    group.add_argument('--tumor-barcode', dest='tumor_barcode', help='TCGA Tumor Sample barcode')
    group.add_argument('--tumor-accession', dest='tumor_accession', help='Tumor CGHub analysis id')
    group.add_argument('--tumor-platform', dest='tumor_platform', help='Tumor sequencing platform')
    group.add_argument('--tumor-source', dest='tumor_source', help='Tumor File Source')
    group.add_argument('--normal-uuid', dest='normal_uuid', help='Normal Sample uuid')
    group.add_argument('--normal-barcode', dest='normal_barcode', help='TCGA Normal Sample barcode')
    group.add_argument('--normal-accession', dest='normal_accession', help='Normal CGHub analysis id')
    group.add_argument('--normal-platform', dest='normal_platform', help='Normal sequencing platform')
    group.add_argument('--normal-source', dest='normal_source', help='Normal File Source')
    group.add_argument('--individual', dest='individual', help='Individual barcode being analyzed')
    group.add_argument('--center', dest='center', help='Center name')
    group.add_argument('--sniper-exe', dest='sniper_exe', default='bam-somaticsniper', help='SomaticSniper Exec Name')
    return parser

def tcga_header_arguments():
    return set(('reference_id', 'center',
        'tumor_uuid', 'tumor_barcode', 'tumor_accession', 'tumor_platform',
        'normal_uuid', 'normal_barcode', 'normal_accession', 'normal_platform',
        'individual'))

def check_if_tcga_header_specified(args):
    arg_keys = set([ key for key in args.keys() if args[key] != None])
    tcga_header_specified = arg_keys.intersection(tcga_header_arguments())
    if len(tcga_header_specified) > 0 and len(tcga_header_specified) < len(tcga_header_arguments()):
        raise RuntimeError("must specify all TCGA header arguments or none at all")
    return True

def wrapper_specific_arguments():
    return set(('f', 'tumor_bam', 'normal_bam', 'output', 'workdir', 'sniper_exe', 'normal_source', 'tumor_source')) | tcga_header_arguments()

def create_sniper_opts(namespace_dict):
    args = []
    flag_opts = set(('L','G','p','J'))
    wrapper_arguments = wrapper_specific_arguments()

    for option, value in namespace_dict.items():
        if option in wrapper_arguments:
            continue
        if (option in flag_opts):
            if value:
                args.append("-" + option)
        else:
            args.append("-" + option + " " + str(value))
    return " ".join(args)

def create_sniper_cmdline(namespace_dict, reference, tumor_bam, normal_bam, temp_output_file):
    return " ".join([
        namespace_dict['sniper_exe'],
        create_sniper_opts(namespace_dict),
        "-f " + reference,
        tumor_bam,
        normal_bam,
        temp_output_file])

def create_workspace(workdir, reference, tumor_bam, normal_bam):

    new_ref = symlink_workspace_file(workdir, reference, "ref_genome.fasta")
    if not os.path.exists(reference + ".fai"):
        print "Indexing", new_ref
        subprocess.check_call( ["/usr/bin/samtools", "faidx", new_ref] )
    else:
        symlink_workspace_file(workdir, reference + ".fai" , "ref_genome.fasta.fai"),
    return (
            symlink_workspace_file(workdir, tumor_bam, "tumor.bam"),
            symlink_workspace_file(workdir, normal_bam, "normal.bam"),
            new_ref
            )

def symlink_workspace_file(workdir, original_file, new_file):
    symlink_name = os.path.join(os.path.abspath(workdir), new_file)
    os.symlink(os.path.abspath(original_file), symlink_name)
    return symlink_name

def reheader_vcf(options, original_vcf_file, new_vcf_file):
    outfile = open(new_vcf_file, 'w')
    outfile.write("##fileformat=VCFv4.1\n")
    outfile.write("##fileDate=" + str(date.today().strftime("%Y%m%d")) + "\n")
    outfile.write("##tcgaversion=1.1.1\n")
    if options['reference_id'] is not None:
        outfile.write(reference_header_line(options['reference_id'], options['f']))
    outfile.write("##phasing=none\n")
    if options['center'] is not None:
        outfile.write('##center="' + options['center'] + "\"\n")

    outfile.write(sample_header_line(
        options['t'],
        options['tumor_uuid'],
        options['tumor_barcode'],
        options['individual'],
        options['tumor_bam'],
        options['tumor_platform'],
        options['tumor_accession'],
        options['tumor_source']))
    outfile.write(sample_header_line(
        options['n'],
        options['normal_uuid'],
        options['normal_barcode'],
        options['individual'],
        options['normal_bam'],
        options['normal_platform'],
        options['normal_accession'],
        options['normal_source']))
    outfile.write(vcfprocesslog_header_line(options))

    original = open(original_vcf_file, 'r')
    for line in original:
        if line.startswith("##"):
            if line.startswith("##FORMAT"):
                outfile.write(fix_format_header_for_tcga(line))
        else:
            outfile.write(fix_mq(line))
    outfile.close()

def sample_header_line(sample_id, uuid, barcode, individual, file_name, platform, accession, source):
    meta = []
    if sample_id is not None:
        meta.append( ("ID", sample_id) )
    if uuid is not None:
        meta.append( ("SampleUUID", uuid))
    if barcode is not None:
        meta.append( ("SampleTCGABarcode", barcode))
    if individual is not None:
        meta.append( ("Individual", individual))
    if file_name is not None:
        meta.append( ("File", file_name))
    if platform is not None:
        meta.append( ("Platform", platform))
    if source is not None:
        meta.append( ("Source", source))
    if accession is not None:
        meta.append( ("Accession", accession) )

    return "##SAMPLE=<%s>\n" % ( ",".join( list( "%s=%s" % (k, v) for k,v in meta) ))

def fix_format_header_for_tcga(line):
    fixLUT = { 'DP': '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read depth at this position in the sample">',
               'DP4': '##FORMAT=<ID=DP4,Number=4,Type=Integer,Description="Number of high-quality ref-forward, ref-reverse, alt-forward and alt-reverse bases">',
               'GQ': '##FORMAT=<ID=GQ,Number=.,Type=Integer,Description="Conditional Phred-scaled genotype quality">',
               'BQ': '##FORMAT=<ID=BQ,Number=.,Type=Integer,Description="Average base quality for reads supporting alleles">',
               'MQ': '##FORMAT=<ID=GMQ,Number=1,Type=Integer,Description="Average mapping quality across all reads">',
               'SS': '##FORMAT=<ID=SS,Number=1,Type=Integer,Description="Variant status relative to non-adjacent Normal,0=wildtype,1=germline,2=somatic,3=LOH,4=post-transcriptional modification,5=unknown">',
               }
    for key in fixLUT:
        if line.startswith('##FORMAT=<ID=' + key + ','):
            return fixLUT[key] + '\n'
    return line

def fix_mq(line):
    return line.replace(':MQ:', ':GMQ:')

def vcfprocesslog_header_line(options):
    input_vcf = "InputVCF=<.>"  #no VCF is put into this program so empty
    source = "InputVCFSource=<bam-somaticsniper>"
    version = "InputVCFVer=<1.0.5>" #Sniper version, could be different if exe specified differently. This should be done better.
    param = 'InputVCFParam=<"' + create_sniper_opts(options) + '">'
    anno = "InputVCFgeneAnno=<.>"
    return "##vcfProcessLog=<" + ",".join([input_vcf, source, version, param, anno]) + ">\n"

def reference_header_line(reference_name, reference_path):
    reference_url = None
    reference_parse_result = urlparse(reference_path)
    if(reference_parse_result.scheme == ''):
        #assuming we've been given a file path
        reference_url = urlunparse(tuple(["file"]) + reference_parse_result[1:])
    else:
        reference_url = reference_path #could just unparse this, but that might reconstruct the string oddly, let's not change what was passed to us

    header_line = "##reference=<ID=" + reference_name + ',Source=' + reference_url + ">\n"
    return header_line

def execute(options, ref, tumor, normal, temp_output_file):
    cmd = create_sniper_cmdline(options, ref, tumor, normal, temp_output_file)

    logging.info("RUNNING: %s" % (cmd))
    print "running", cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()
    if len(stderr):
        print stderr
    return p.returncode

if __name__ == "__main__":
    parser = sniper_argparser()
    args = parser.parse_args()
    arg_dict = vars(args)
    check_if_tcga_header_specified(arg_dict) #this will throw if we're not ok with TCGA header args

    (workspace_tumor, workspace_normal, workspace_ref) = create_workspace(args.workdir, args.f, args.tumor_bam, args.normal_bam)
    print (workspace_tumor, workspace_normal, workspace_ref)
    temp_output_file = os.path.join(args.workdir, "raw_output.vcf")

    execute(arg_dict, workspace_ref, workspace_tumor, workspace_normal, temp_output_file)
    reheader_vcf(arg_dict, temp_output_file, args.output)
