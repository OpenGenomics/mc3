#!/usr/bin/env python

import os
import json
import argparse
import synqueue
import shutil
import synapseclient
import subprocess
from nebula.service import GalaxyService
from nebula.galaxy import GalaxyWorkflow
from nebula.docstore import from_url
from nebula.target import Target
from nebula.tasks import TaskGroup, GalaxyWorkflowTask
import tempfile

REFDATA_PROJECT="syn3241088"

config = {
    "table_id" : "syn4898104",
    "primary_col" : "participant_id",
    "assignee_col" : "assignee",
    "state_col" : "state"
}

def run_gen(args):
    syn = synapseclient.Synapse()
    syn.login()

    if args.alt_table is not None:
        config['table_id'] = args.alt_table

    docstore = from_url(args.out_base)

    if args.ref_download:
        #download reference files from Synapse and populate the document store
        for a in syn.chunkedQuery('select * from entity where parentId=="%s"' % (REFDATA_PROJECT)):
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

    data_mapping = {
        "dbsnp" : "dbsnp_132_b37.leftAligned.vcf",
        "cosmic" : "b37_cosmic_v54_120711.vcf",
        "gold_indels" : "Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf",
        "phase_one_indels" : "1000G_phase1.indels.hg19.sites.fixed.vcf"
    }

    dm = {}
    for k,v in data_mapping.items():
        hit = None
        for a in docstore.filter(name=v):
            hit = a[0]
        if hit is None:
            raise Exception("%s not found" % (v))
        dm[k] = { "uuid" : hit }

    workflow_2 = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-GATK_CGHub_2.ga")
    workflow_3 = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-GATK_CGHub_3.ga")

    ref_rename = {
        "HG19_Broad_variant" : "Homo_sapiens_assembly19"
    }

    tasks = TaskGroup()

    for ent in synqueue.listAssignments(syn, **config):
        bam_set = list( a[1] for a in ent['meta'].items() if a[0].startswith("id_") and isinstance(a[1], basestring)  )

        ref_set = set( a[1] for a in ent['meta'].items() if a[0].startswith("ref_assembly_") and isinstance(a[1], basestring) )
        assert(len(ref_set) == 1)
        ref_name = ref_set.pop()
        if ref_name in ref_rename:
            ref_name = ref_rename[ref_name]

        hit = None
        for a in docstore.filter(name=ref_name + ".fasta"):
            hit = a[0]
        for a in docstore.filter(name=ref_name + ".fa"):
            hit = a[0]
        if hit is None:
            raise Exception("%s not found" % (ref_name))
        workflow_dm = dict(dm)
        workflow_dm['reference_genome'] = { "uuid" : hit }
        if len(bam_set) == 2:
            task = GalaxyWorkflowTask("workflow_%s" % (ent['id']),
                workflow_2,
                inputs=workflow_dm,
                parameters={
                    'INPUT_BAM_1' : {
                        "uuid" : bam_set[0],
                        "gnos_endpoint" : "cghub.ucsc.edu",
                        "cred_file" : "/tool_data/files/cghub.key"
                    },
                    'INPUT_BAM_2' : {
                        "uuid" : bam_set[1],
                        "gnos_endpoint" : "cghub.ucsc.edu",
                        "cred_file" : "/tool_data/files/cghub.key"
                    }
                },
                tags=[ "donor:%s" % (ent['meta']['participant_id']) ],
                tool_tags = {
                    "BQSR_1" : {
                        "output_bam" : [ "original_bam:%s" % (bam_set[0]) ]
                    },
                    "BQSR_2" : {
                        "output_bam" : [ "original_bam:%s" % (bam_set[1]) ]
                    }

                }
            )
            tasks.append(task)
        elif len(bam_set) == 3:
            task = GalaxyWorkflowTask("workflow_%s" % (ent['id']),
                workflow_3,
                inputs=workflow_dm,
                parameters={
                    'INPUT_BAM_1' : {
                        "uuid" : bam_set[0],
                        "gnos_endpoint" : "cghub.ucsc.edu",
                        "cred_file" : "/tool_data/files/cghub.key"
                    },
                    'INPUT_BAM_2' : {
                        "uuid" : bam_set[1],
                        "gnos_endpoint" : "cghub.ucsc.edu",
                        "cred_file" : "/tool_data/files/cghub.key"
                    },
                    'INPUT_BAM_3' : {
                        "uuid" : bam_set[2],
                        "gnos_endpoint" : "cghub.ucsc.edu",
                        "cred_file" : "/tool_data/files/cghub.key"
                    }
                },
                tags=[ "donor:%s" % (ent['meta']['participant_id']) ],
                tool_tags = {
                    "BQSR_1" : {
                        "output_bam" : [ "original_bam:%s" % (bam_set[0]) ]
                    },
                    "BQSR_2" : {
                        "output_bam" : [ "original_bam:%s" % (bam_set[1]) ]
                    },
                    "BQSR_3" : {
                        "output_bam" : [ "original_bam:%s" % (bam_set[2]) ]
                    }
                }
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
            galaxy="bgruening/galaxy-stable",
            sudo=True,
            tool_data=args.tool_data,
            tool_dir=args.tool_dir,
            work_dir=args.work_dir,
            smp=[
                ["gatk_bqsr", 12],
                ["gatk_indel", 24]
            ]
        )
        with open("%s.service" % (args.out_base), "w") as handle:
            s = service.get_config()
            if args.scratch:
                print "Using scratch", args.scratch
                s.set_docstore_config(cache_path=args.scratch, open_perms=True)
            s.store(handle)

def run_upload(args):
    #syn = synapseclient.Synapse()
    #syn.login()

    docstore = from_url(args.out_base)

    donor_map = {}
    bam_map = {}

    for id, doc in docstore.filter(visible=True, state='ok', name=['OUTPUT_BAM_1', 'OUTPUT_BAM_2', 'OUTPUT_BAM_3']):
        print doc['name'], doc['tags']
        for t in doc['tags']:
            ts = t.split(":")
            if ts[0] == 'donor':
                if ts[1] not in donor_map:
                    donor_map[ts[1]] = []
                donor_map[ts[1]].append(id)
            if ts[0] == 'original_bam':
                bam_map[ts[1]] = id
    
    if not os.path.exists(args.out):
        os.mkdir(args.out)
    
    for key, value in bam_map.items():
        t = Target(uuid=value)
        path = docstore.get_filename(t)
        print "%s\t%s" % (value, path )
        os.symlink(path, os.path.join(args.out, "MC3." + key + ".bam"))

    #print donor_map
    #print bam_map


def run_list(args):
    syn = synapseclient.Synapse()
    syn.login()
    if args.alt_table is not None:
        config['table_id'] = args.alt_table
    synqueue.listAssignments(syn, display=True, **config)

def run_set(args):
    syn = synapseclient.Synapse()
    syn.login()
    if args.alt_table is not None:
        config['table_id'] = args.alt_table
    synqueue.setStates(syn, args.state, args.ids, **config)

def run_register(args):
    syn = synapseclient.Synapse()
    syn.login()
    if args.alt_table is not None:
        config['table_id'] = args.alt_table
    synqueue.registerAssignments(syn, args.count, **config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers( title='commands')

    parser_gen = subparsers.add_parser('gen')
    parser_gen.add_argument("--out-base", default="mc3_gatk")
    parser_gen.add_argument("--ref-download", action="store_true", default=False)
    parser_gen.add_argument("--create-service", action="store_true", default=False)
    parser_gen.add_argument("--scratch", default=None)
    parser_gen.add_argument("--work-dir", default=None)
    parser_gen.add_argument("--tool-data", default=os.path.abspath("tool_data"))
    parser_gen.add_argument("--tool-dir", default=os.path.abspath("tools"))
    parser_gen.add_argument("--alt-table", default=None)
    parser_gen.set_defaults(func=run_gen)

    parser_upload = subparsers.add_parser('upload-prep')
    parser_upload.add_argument("--out-base", default="mc3_gatk")
    parser_upload.add_argument("--out", default="upload")
    parser_upload.set_defaults(func=run_upload)

    parser_list = subparsers.add_parser('list')
    parser_list.add_argument("--alt-table", default=None)
    parser_list.set_defaults(func=run_list)

    parser_set = subparsers.add_parser('set')
    parser_set.add_argument("--alt-table", default=None)
    parser_set.add_argument("state")
    parser_set.add_argument("ids", nargs="+")
    parser_set.set_defaults(func=run_set)

    parser_register = subparsers.add_parser('register')
    parser_register.add_argument("--alt-table", default=None)
    parser_register.add_argument("--count", type=int, default=1)
    parser_register.set_defaults(func=run_register)


    args = parser.parse_args()

    args.func(args)
