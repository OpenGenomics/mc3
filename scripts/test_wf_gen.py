#!/usr/bin/env python

import os
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

fake_metadata = {
    "pair0" : {
        "participant_id" : "b2aac45b-2073-4c7a-adb9-769a4fdcc111",
        "disease" : "BRCA",
        "normal" : {
            "uuid" : "e5383ad1-30f6-4528-bbe5-0ec14d0e6e2f",
            "barcode" : "TCGA-E9-A1NH-11A-33D-A14G-09",
            "aliquot_id" : "0ee95056-a7cc-415c-a487-3ad08604dfc0",
            "file_name" : "TCGA_MC3.TCGA-E9-A1NH-11A-33D-A14G-09.bam"
        },
        "tumour" : {
            "barcode" : "TCGA-E9-A1NH-01A-11D-A14G-09",
            "uuid" : "4ab28e27-e860-4b3d-8abd-56b58930d2f6",
            "file_name" : "TCGA_MC3.TCGA-E9-A1NH-01A-11D-A14G-09.bam",
            "aliquot_id" : "13c312ec-0add-4758-ab8d-c193e2e08c6d"
        }
    }
}

def run_gen(args):
    syn = synapseclient.Synapse()
    syn.login()

    docstore = from_url(args.out_base)

    data_mapping = {
        "db_snp" : "dbsnp_132_b37.leftAligned.vcf",
        "centromere" : "centromere_hg19.bed",
        "reference_genome" : "Homo_sapiens_assembly19.fasta",
    }

    if args.ref_download:
        syn_sync(syn, REFDATA_PROJECT, docstore, data_mapping.values())

    dm = {}
    for k,v in data_mapping.items():
        hit = None
        for a in docstore.filter(name=v):
            hit = a[0]
        if hit is None:
            raise Exception("%s not found" % (v))
        dm[k] = { "uuid" : hit }

    if args.sample is not None:
        sync_doc_dir(
            os.path.join( os.path.dirname(__file__), "..", "testexomes" ), docstore,
            filter=lambda x: x['donorId'] in args.sample
        )
    else:
        sync_doc_dir( os.path.join( os.path.dirname(__file__), "..", "testexomes" ), docstore)

    tumor_uuids = {}
    normal_uuids = {}

    for id, ent in docstore.filter(sampleType="tumour"):
        tumor_uuids[ent['participant_id']] = id

    for id, ent in docstore.filter(sampleType="normal"):
        normal_uuids[ent['participant_id']] = id

    mc3_workflow = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-MC3_Pipeline.ga")

    reference_id = None
    for a in docstore.filter(name="Homo_sapiens_assembly19.fasta"):
        reference_id = a[0]

    tasks = TaskGroup()
    for donor in tumor_uuids:
        if donor in normal_uuids:
            print "participant", donor

            donor_name = None
            for k,v in fake_metadata.items():
                if v['participant_id'] == donor:
                    donor_name = k

            workflow_dm = dict(dm)
            workflow_dm['tumor_bam'] = { "uuid" : tumor_uuids[donor] }
            workflow_dm['normal_bam'] = { "uuid" : normal_uuids[donor] }

            task = GalaxyWorkflowTask("workflow_%s" % (donor),
                mc3_workflow,
                inputs=workflow_dm,
                parameters={
                    "reheader_config" : {
                        "platform" : "Illumina",
                        "center" : "OHSU",
                        "reference_genome" : "Homo_sapiens_assembly19.fasta",
                        "filedate" : datetime.datetime.now().strftime("%Y%m%d"),
                        "normal_analysis_uuid" : fake_metadata[donor_name]['normal']['uuid'],
                        "normal_bam_name" : fake_metadata[donor_name]['normal']['file_name'],
                        "normal_aliquot_uuid" : fake_metadata[donor_name]['normal']['aliquot_id'],
                        "normal_aliquot_barcode": fake_metadata[donor_name]['normal']['barcode'],
                        "tumor_analysis_uuid" : fake_metadata[donor_name]['tumour']['uuid'],
                        "tumor_bam_name" : fake_metadata[donor_name]['tumour']['file_name'],
                        "tumor_aliquot_uuid" : fake_metadata[donor_name]['tumour']['aliquot_id'],
                        "tumor_aliquot_barcode" : fake_metadata[donor_name]['tumour']['barcode'],
                    }
                },
                tags=[ "donor:%s" % (donor) ],
            )
            tasks.append(task)

    if not os.path.exists("%s.tasks" % (args.out_base)):
        os.mkdir("%s.tasks" % (args.out_base))
    for data in tasks:
        with open("%s.tasks/%s" % (args.out_base, data.task_id), "w") as handle:
            handle.write(json.dumps(data.to_dict()))

    if args.create_service:
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
                ["muTect", 8],
                ["delly", 4],
                ["gatk_bqsr", 12],
                ["gatk_indel", 12],
                ["bwa_mem", 12]
            ]
        )
        with open("%s.service" % (args.out_base), "w") as handle:
            s = service.get_config()
            if args.scratch:
                print "Using scratch", args.scratch
                s.set_docstore_config(cache_path=args.scratch, open_perms=True)
            s.store(handle)

def run_download(args):
    basedir = os.path.dirname( os.path.dirname(__file__) )
    exome_dir = os.path.join(basedir, "testexomes")
    if not os.path.exists(exome_dir):
        os.mkdir( exome_dir )

    files = [
        "testexome.pair0.normal.bam",
        "testexome.pair0.tumour.bam",
        "testexome.pair2.normal.bam",
        "testexome.pair2.tumour.bam",
        "testexome.pair3.normal.bam",
        "testexome.pair3.tumour.bam",
        "testexome.pair4.normal.bam",
        "testexome.pair4.tumour.bam",
        "testexome.pair5.normal.bam",
        "testexome.pair5.tumour.bam",
        "testexome.pair6.normal.bam",
        "testexome.pair6.tumour.bam",
        "testexome.pair7.normal.bam",
        "testexome.pair7.tumour.bam",
        "testexome.pair8.normal.bam",
        "testexome.pair8.tumour.bam",
        "testexome.pair9.normal.bam",
        "testexome.pair9.tumour.bam",
        "testexome0.truth.vcf",
        "testexome2.truth.vcf",
        "testexome3.truth.vcf",
        "testexome4.truth.vcf",
        "testexome5.truth.vcf",
        "testexome6.truth.vcf",
        "testexome7.truth.vcf",
        "testexome8.truth.vcf",
        "testexome9.truth.vcf",
    ]

    for f in files:
        file_path = os.path.join(exome_dir, f)
        if not os.path.exists(file_path):
            print "Downloading: %s to %s" % (f, file_path)
            urllib.urlretrieve( "http://hgwdev.sdsc.edu/~kellrott/mc3/testexomes/" + f, file_path )
        tmp = os.path.basename(file_path).split(".")
        if tmp[-1] == "bam":
            if tmp[1] in fake_metadata:
                with open(file_path + ".json", "w") as handle:
                    handle.write(json.dumps( {
                        "uuid" : fake_metadata[tmp[1]][tmp[2]]['uuid'],
                        "sampleType" : tmp[2],
                        "participant_id" : fake_metadata[tmp[1]]['participant_id']
                    }))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers( title='commands')

    parser_gen = subparsers.add_parser('gen')
    parser_gen.add_argument("--out-base", default="test_mc3")
    parser_gen.add_argument("--ref-download", action="store_true", default=False)
    parser_gen.add_argument("--create-service", action="store_true", default=False)
    parser_gen.add_argument("--scratch", default=None)
    parser_gen.add_argument("--sudo", action="store_true", default=False)
    parser_gen.add_argument("--work-dir", default=None)
    parser_gen.add_argument("--tool-data", default=os.path.abspath("tool_data"))
    parser_gen.add_argument("--tool-dir", default=os.path.abspath("tools"))
    parser_gen.add_argument("--alt-table", default=None)
    parser_gen.add_argument("--galaxy", default="bgruening/galaxy-stable")
    parser_gen.add_argument("--sample", action="append", default=None)
    parser_gen.set_defaults(func=run_gen)

    parser_download = subparsers.add_parser('download')
    parser_download.set_defaults(func=run_download)


    args = parser.parse_args()

    args.func(args)
