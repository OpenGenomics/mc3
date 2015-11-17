#!/usr/bin/env python

import os
import csv
import json
import uuid
import datetime
import argparse
import shutil
import subprocess
from nebula.docstore import from_url
from nebula.docstore.util import sync_doc_dir
from nebula.galaxy import GalaxyWorkflow
from nebula.service import GalaxyService
from nebula.tasks import TaskGroup, GalaxyWorkflowTask
from nebula.target import Target

from glob import glob

import synapseclient
import urllib

REFDATA_PROJECT="syn3241088"

def syn_sync(syn, project, docstore, filter=None):
    #download reference files from Synapse and populate the document store
    for a in syn.chunkedQuery('select * from entity where parentId=="%s"' % (project)):
        if filter is None or a['entity.name'] in filter or a['entity.name'].replace(".gz", "") in filter:
            ent = syn.get(a['entity.id'])

            id = ent.annotations['uuid'][0]
            t = Target(uuid=id)
            docstore.create(t)
            path = docstore.get_filename(t)
            name = ent.name
            if 'dataPrep' in ent.annotations:
                if ent.annotations['dataPrep'][0] == 'gunzip':
                    subprocess.check_call("gunzip -c %s > %s" % (ent.path, path), shell=True)
                    name = name.replace(".gz", "")
                else:
                    print "Unknown DataPrep"
            else:
                shutil.copy(ent.path, path)
            docstore.update_from_file(t)
            meta = {}
            meta['name'] = name
            meta['uuid'] = id
            if 'dataPrep' in meta:
                del meta['dataPrep']
            docstore.put(id, meta)

ref_rename = {
    "HG19_Broad_variant" : "Homo_sapiens_assembly19"
}

def run_gen(args):
    syn = synapseclient.Synapse()
    syn.login()

    docstore = from_url(args.out_base)

    data_mapping = {
        "db_snp" : "dbsnp_132_b37.leftAligned.vcf",
        "centromere" : "centromere_hg19.bed",
        "cosmic" : "b37_cosmic_v54_120711.vcf"
    }

    ref_genomes = [
        "Homo_sapiens_assembly19.fasta",
        "GRCh37-lite.fa",
        "GRCh37-lite-+-HPV_Redux-build.fa",
        "GRCh37-lite_WUGSC_variant_1.fa.gz",
        "GRCh37-lite_WUGSC_variant_2.fa.gz",
        "hg19_M_rCRS.fa.gz"
    ]

    if args.ref_download:
        syn_sync(syn, REFDATA_PROJECT, docstore, data_mapping.values() + ref_genomes)

    dm = {}
    for k,v in data_mapping.items():
        hit = None
        for a in docstore.filter(name=v):
            hit = a[0]
        if hit is None:
            raise Exception("%s not found" % (v))
        dm[k] = { "uuid" : hit }

    mc3_dna_workflow = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-MC3_Pipeline_CGHub_DNA.ga")
    mc3_dnarna_workflow = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-MC3_Pipeline_CGHub_DNA_RNA.ga")

    rna_hit = None
    for a in docstore.filter(name="hg19_M_rCRS.fa"):
        rna_hit = a[0]

    tasks = TaskGroup()
    assembly_hits = {}
    with open(args.joblist) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            if row['normal_assembly'] != row['tumor_assembly']:
                print "Row Mispatch", row['normal_assembly'], row['tumor_assembly']
                #raise Exception("Mismatch reference")
            ref_name = row['normal_assembly']
            if ref_name in ref_rename:
                ref_name = ref_rename[ref_name]
            if ref_name in assembly_hits:
                hit = assembly_hits[ref_name]
            else:
                hit = None
                for a in docstore.filter(name=ref_name + ".fasta"):
                    hit = a[0]
                for a in docstore.filter(name=ref_name + ".fa"):
                    hit = a[0]
                if hit is None:
                    raise Exception("%s not found" % (ref_name))
                assembly_hits[ref_name] = hit
            workflow_dm = dict(dm)
            workflow_dm['reference_genome'] = { "uuid" : hit }
            
            params = {
                'tumor_bam' : {
                    "uuid" : row['tumor_analysis_id'],
                    "gnos_endpoint" : "cghub.ucsc.edu",
                    "cred_file" : "/tool_data/files/cghub.key"
                },
                'normal_bam' : {
                    "uuid" : row['normal_analysis_id'],
                    "gnos_endpoint" : "cghub.ucsc.edu",
                    "cred_file" : "/tool_data/files/cghub.key"
                },
                "reheader_config" : {
                    "platform" : "Illumina",
                    "center" : "OHSU",
                    "reference_genome" : ref_name,
                    "participant_uuid" : row['participant_id'],
                    "disease_code" : row['disease'],
                    "filedate" : datetime.datetime.now().strftime("%Y%m%d"),
                    "normal_analysis_uuid" : row['normal_analysis_id'],
                    "normal_bam_name" : row['normal_filename'],
                    "normal_aliquot_uuid" : row['normal_aliquot_id'],
                    "normal_aliquot_barcode": row['normal_barcode'],
                    "tumor_analysis_uuid" : row['tumor_analysis_id'],
                    "tumor_bam_name" : row['tumor_filename'],
                    "tumor_aliquot_uuid" : row['tumor_aliquot_id'],
                    "tumor_aliquot_barcode" : row['tumor_barcode'],
                }
            }
            
            if row['rna_analysis_id'] != "NA":
                params['rna_tumor_bam'] = {
                    "uuid" : row['rna_analysis_id'],
                    "gnos_endpoint" : "cghub.ucsc.edu",
                    "cred_file" : "/tool_data/files/cghub.key"
                }
                workflow_dm['rna_reference_genome'] = { "uuid" : rna_hit }
                task = GalaxyWorkflowTask("workflow_%s" % (row['job_id']),
                    mc3_dnarna_workflow,
                    inputs=workflow_dm,
                    parameters=params,
                    tags=[ "donor:%s" % (row['participant_id']) ],
                )            
            else: 
                task = GalaxyWorkflowTask("workflow_%s" % (row['job_id']),
                    mc3_dna_workflow,
                    inputs=workflow_dm,
                    parameters=params,
                    tags=[ "donor:%s" % (row['participant_id']) ],
                )
            tasks.append(task)

    if not os.path.exists("%s.tasks" % (args.out_base)):
        os.mkdir("%s.tasks" % (args.out_base))
    for data in tasks:
        with open("%s.tasks/%s" % (args.out_base, data.task_id), "w") as handle:
            handle.write(json.dumps(data.to_dict()))

    service = GalaxyService(
        docstore=docstore,
        galaxy=args.galaxy,
        sudo=args.sudo,
        tool_data=args.tool_data,
        tool_dir=args.tool_dir,
        work_dir=args.work_dir,
        smp=[
            ["gatk_bqsr", 12],
            ["gatk_indel", 24],
            ["MuSE", 8],
            ["pindel", 8],
            ["mutect", 8],
            ["delly", 4],
            ["gatk_bqsr", 12],
            ["gatk_indel", 12],
            ["bwa_mem", 12],
            ["radia", 8],
            ['radia_filter', 8]
        ]
    )
    with open("%s.service" % (args.out_base), "w") as handle:
        s = service.get_config()
        if args.scratch:
            print "Using scratch", args.scratch
            s.set_docstore_config(cache_path=args.scratch, open_perms=True)
        s.store(handle)


def run_extract(args):
    docstore = from_url(args.out_base)
    
    for id, ent in docstore.filter(file_ext="vcf", name=[
        "muse.vcf", "pindel.vcf", "radia.dna-rna.vcf", "radia.dna.vcf", "somatic_sniper.vcf", 
        "varscan.indel.vcf", "varscan.snp.vcf", "mutect.vcf"
    ]):
        t = Target(uuid=ent['id'])
        if docstore.size(t) > 0:
            donor = None
            for e in ent['tags']:
                tmp = e.split(":")
                if tmp[0] == 'donor':
                    donor = tmp[1]
            if donor is not None:
                donor_dir = os.path.join(args.out_dir, donor)
                if not os.path.exists(donor_dir):
                    os.makedirs(donor_dir)
                print "Found", donor, ent['name']
                shutil.copy( docstore.get_filename(t), os.path.join(donor_dir, ent['name']) )

SNP_METHOD = [
    "muse",
    "radia",
    "somatic_sniper",
    "varscan.snp",
]

INDEL_METHOD = [
    "pindel",
    "varscan.indel"
]

def run_stats(args):
    import evaluator
    rev_map = {}
    for k, v in fake_metadata.items():
        rev_map[v['participant_id']] = k
    
    basedir = os.path.dirname( os.path.dirname(__file__) )
    exome_dir = os.path.join(basedir, "testexomes")
    
    out_scores = {}
    for donor_dir in glob(os.path.join(args.out_dir, "*")):
        donor = os.path.basename(donor_dir)
        if rev_map[donor] not in out_scores:
            out_scores[rev_map[donor]] = {}
        for vcf_file in glob( os.path.join(donor_dir, "*.vcf")):
            method = os.path.basename(vcf_file).replace(".vcf", "")
            vtype = None
            if method in SNP_METHOD:
                vtype = "SNV"
            if method in INDEL_METHOD:
                vtype = "INDEL"
            truth_file = os.path.join(exome_dir, "testexome" + rev_map[donor][-1:] + ".truth.vcf.gz" )
            scores = evaluator.evaluate(vcf_file, truth_file, vtype=vtype, truthmask=False)
            out_scores[rev_map[donor]][method] = scores
    print out_scores
    
    totals = {}
    for v in out_scores.values():
        for method, values in v.items():
            if method not in totals:
                totals[method] = []
            totals[method].append( values )
    for method, values in totals.items():
        out = []
        for i in range(3):
            out.append( "%s" % (sum( j[i] for j in values  ) / float(len(values) )) )
        print method, "\t".join(out)

def check_within(datestr, max_hours):
    delta = datetime.datetime.now() - datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%f")
    age =  delta.days * 24 + delta.seconds / 3600
    if age < max_hours:
        return True
    return False


def run_errors(args):

    doc = from_url(args.out_base)

    for id, entry in doc.filter():
        if entry.get('state', '') == 'error':
            if args.within is None or 'update_time' not in entry or check_within(entry['update_time'], args.within):
                print "Dataset", id, entry.get("job", {}).get("tool_id", ""), entry.get('update_time', ''), entry.get("tags", "")
                if args.full:
                    if 'provenance' in entry:
                        print "tool:", entry['provenance']['tool_id']
                        print "-=-=-=-=-=-=-"
                    print entry['job']['stdout']
                    print "-------------"
                    print entry['job']['stderr']
                    print "-=-=-=-=-=-=-"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers( title='commands')

    parser_gen = subparsers.add_parser('gen')
    parser_gen.add_argument("--out-base", default="mc3_run")
    parser_gen.add_argument("--ref-download", action="store_true", default=False)
    parser_gen.add_argument("--scratch", default=None)
    parser_gen.add_argument("--sudo", action="store_true", default=False)
    parser_gen.add_argument("--work-dir", default=None)
    parser_gen.add_argument("--tool-data", default=os.path.abspath("tool_data"))
    parser_gen.add_argument("--tool-dir", default=os.path.abspath("tools"))
    parser_gen.add_argument("--galaxy", default="bgruening/galaxy-stable")
    parser_gen.add_argument("joblist")
    parser_gen.set_defaults(func=run_gen)

    parser_extract = subparsers.add_parser('extract')
    parser_extract.add_argument("--out-base", default="mc3_run")
    parser_extract.add_argument("--out-dir", default="output")
    parser_extract.set_defaults(func=run_extract)

    parser_stats = subparsers.add_parser('stats')
    parser_stats.set_defaults(func=run_stats)
    parser_stats.add_argument("out_dir")

    parser_errors = subparsers.add_parser('errors')
    parser_errors.add_argument("--within", type=int, default=None)
    parser_errors.add_argument("--full", action="store_true", default=False)
    parser_errors.add_argument("--out-base", default="mc3_run")
    parser_errors.set_defaults(func=run_errors)
    
    args = parser.parse_args()

    args.func(args)
