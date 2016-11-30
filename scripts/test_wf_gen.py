#!/usr/bin/env python

import os
import json
import uuid
import datetime
import argparse
import shutil
import subprocess
from glob import glob
import urllib

#these non-standard libraries are only used for some of the methods, so punt till
#later to start throwing exceptions
try:
    from nebula.docstore import from_url
    from nebula.docstore.util import sync_doc_dir
    from nebula.galaxy import GalaxyWorkflow
    from nebula.service import GalaxyService
    from nebula.tasks import TaskGroup, GalaxyWorkflowTask
    from nebula.target import Target
    import synapseclient
except ImportError:
    pass
    

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
    },
    "pair2" : {
        "participant_id" : "92c65e5a-3f07-49d9-ab69-46a0eb86ae88",
        "disease" : "READ",
        "normal" : {
            "barcode" : "TCGA-AG-3882-10A-01W-0901-10",
            "uuid" : "98bbddda-8ad1-4e4b-a702-e2d9026738d6",
            "file_name" : "TCGA_MC3.TCGA-AG-3882-10A-01W-0901-10.bam",
            "aliquot_id" : "2f4d9862-155b-4a81-909d-e0e652dd9159"            
        }, 
        "tumour" : {
            "barcode" : "TCGA-AG-3882-01A-01W-0899-10",
            "uuid" : "257dd1a3-7d73-4d54-ad93-e50b22212e7c",
            "file_name" : "TCGA_MC3.TCGA-AG-3882-01A-01W-0899-10.bam",
            "aliquot_id" : "1490465c-fa59-4e82-8911-ecfabfeade29"
        }
    },
    "pair3" : {
        "participant_id" : "5dc7e186-7e01-4a54-8ae8-350dace2297b",
        "disease" : "PRAD",
        "normal" : {
            "barcode" : "TCGA-J4-A83I-10B-01D-A362-08",
            "uuid" : "bcb73e69-89f0-4a5a-a606-519553c99270",
            "file_name" : "C529.TCGA-J4-A83I-10B-01D-A362-08.1.bam",
            "aliquot_id" : "13d07794-c0fa-4070-9dcd-9cee45840284"
        },
        "tumour" : {
            "barcode" : "TCGA-J4-A83I-01A-11D-A364-08",
            "uuid" : "952720a2-bf8b-4a02-a0f8-b59c9d44c73b",
            "file_name" : "C529.TCGA-J4-A83I-01A-11D-A364-08.1.bam",
            "aliquot_id" : "fdeb9e4e-d715-4565-9cb4-40525a0575ad"
        }
    },
    "pair4" : {
        "participant_id" : "84cb84d0-7c7e-453c-8cc5-65b5af941028",
        "disease" : "CESC",
        "normal" : {
            "barcode" : "TCGA-EA-A411-10A-01D-A243-09",
            "uuid" : "ec580fc3-68f5-49af-a14b-bfbcf2a62786",
            "file_name" : "TCGA_MC3.TCGA-EA-A411-10A-01D-A243-09.bam",
            "aliquot_id" : "13cc40ed-7de6-42ff-885b-bd6965e8d657"
        },
        "tumour" : {
            "barcode" : "TCGA-EA-A411-01A-11D-A243-09",
            "uuid" : "15785428-a11e-4357-bc5f-ef28a68d5788",
            "file_name" : "TCGA_MC3.TCGA-EA-A411-01A-11D-A243-09.bam",
            "aliquot_id" : "4612db5e-d3f3-48a6-9349-f94cbf9b8d3d"
        }
    },
    "pair5" : {
        "participant_id" : "9d84dff8-6c19-4881-93c6-56c98a3049b5",
        "disease" : "UCEC",
        "normal" : {
            "barcode" : "TCGA-AX-A2HA-11A-11D-A18P-09",
            "uuid" : "3349ee96-6dbd-4a05-86f3-8962d3f0d542",
            "file_name" : "TCGA_MC3.TCGA-AX-A2HA-11A-11D-A18P-09.bam",
            "aliquot_id" : "b953c4e5-e489-455a-98e8-a635e95c5d81"
        }, 
        "tumour" : {
            "barcode" : "TCGA-AX-A2HA-01A-12D-A18P-09",
            "uuid" : "36829e84-4dfe-4232-ad87-f8292c5e90a9",
            "file_name" : "TCGA_MC3.TCGA-AX-A2HA-01A-12D-A18P-09.bam",
            "aliquot_id" : "140451fd-80a7-4198-93fe-00debbda61c8"
        }
    },
    "pair6" : {
        "participant_id" : "6014f16b-5f3d-43ec-b8a7-7cf99583101a",
        "disease" : "KIRP",
        "normal" : {
            "barcode" : "TCGA-UZ-A9PS-10A-01D-A42M-10",
            "uuid" : "e77f1160-39a2-4373-bf0d-5265fb41f930",
            "file_name" : "TCGA-UZ-A9PS-10A-01D-A42M-10_Illumina.bam",
            "aliquot_id" : "57691588-0681-41ba-b333-4d612c7f0542"
        },
        "tumour" : {
            "barcode" : "TCGA-UZ-A9PS-01A-11D-A42J-10",
            "uuid" : "9248e05f-b628-427b-a04f-6187b76b34be",
            "file_name" : "TCGA-UZ-A9PS-01A-11D-A42J-10_Illumina.bam",
            "aliquot_id" : "acba931b-e52d-4487-b13a-7d8c91981263"
        } 
    },
    "pair7" : {
        "participant_id" : "7aece0e0-e57b-40b9-8ef3-8b98624b0e91",
        "disease" : "KIRC",
        "normal" : {
            "barcode" : "TCGA-B8-5546-11A-01D-1534-10",
            "uuid" : "c1aea022-7a07-48c2-b31c-e891af48076b",
            "file_name" : "TCGA_MC3.TCGA-B8-5546-11A-01D-1534-10.bam",
            "aliquot_id" : "24a28744-4b2a-45c3-acae-c504a1ffd8a0"
        },
        "tumour" : {
            "barcode" : "TCGA-B8-5546-01A-01D-1534-10",
            "uuid" : "10003d6f-da9a-449a-bdc6-086b235be6ed",
            "file_name" : "TCGA_MC3.TCGA-B8-5546-01A-01D-1534-10.bam",
            "aliquot_id" : "e3f75b12-27ee-4d38-bd72-f6e167a25da6"
        }
    },
    "pair8" : {
        "participant_id" : "2b82e941-1b16-444e-af41-24dbc0a7e8b5",
        "disease" : "GBM",
        "normal" : {
            "barcode" : "TCGA-12-1597-10A-01D-1495-08",
            "uuid" : "cb1f526c-9741-4839-89c5-0e84a939ad4e",
            "file_name" : "C484.TCGA-12-1597-10A-01D-1495-08.5.bam",
            "aliquot_id" : "ecbbe2f6-d86b-4498-be57-285695ea7eb2"
        }, 
        "tumour" : {
            "barcode" : "TCGA-12-1597-01B-01D-1495-08",
            "uuid" : "c9adfe63-cfe8-41aa-9ee5-b26ecb9c11da",
            "file_name" : "C484.TCGA-12-1597-01B-01D-1495-08.6.bam",
            "aliquot_id" : "7d35c610-cc06-4aa5-8c96-2f7b7465069f"
        }
    },
    "pair9" : {
        "participant_id" : "755d3bde-76c3-45c1-8427-8e4d5d686dc1",
        "disease" : "COAD",
        "normal" : {
            "barcode" : "TCGA-CK-6747-10A-01D-1835-10",
            "uuid" : "0c04ec83-e9eb-40c6-b99c-df9730fe8c61",
            "file_name" : "TCGA_MC3.TCGA-CK-6747-10A-01D-1835-10.bam",
            "aliquot_id" : "14cd6385-3a7e-4ec7-bf1e-698524efac6e"
        },
        "tumour" : {
            "barcode" : "TCGA-CK-6747-01A-11D-1835-10",
            "uuid" : "a315835a-ab33-4f62-adf9-94725bde5b49",
            "file_name" : "TCGA_MC3.TCGA-CK-6747-01A-11D-1835-10.bam",
            "aliquot_id" : "3e07ea99-283d-4404-9777-097d3030691b"
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
        "cosmic" : "b37_cosmic_v54_120711.vcf"
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

    mc3_workflow = GalaxyWorkflow(ga_file="workflows/Galaxy-Workflow-MC3_Pipeline_Test.ga")

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
                        "participant_uuid" : fake_metadata[donor_name]['participant_id'],
                        "disease_code" : fake_metadata[donor_name]['disease'],
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

def run_gencwl(args):
    
    tools_templates = {
        "mutect" : {
            "tumor" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.tumour.bam" % (x))) 
            },
            "normal" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.normal.bam" % (x)))
            },
            "reference" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "Homo_sapiens_assembly19.fasta"))},
            "cosmic" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "b37_cosmic_v54_120711.vcf")) },
            "dbsnp" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "dbsnp_132_b37.leftAligned.vcf")) },
            "tumor_lod" : 10.0
        }, 
        "muse" : {
            "tumor" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.tumour.bam" % (x))) 
            },
            "normal" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.normal.bam" % (x)))
            },
            "reference" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "Homo_sapiens_assembly19.fasta"))},
            "known" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "dbsnp_132_b37.leftAligned.vcf")) },
            "mode" : "wxs"
        },
        "somatic_sniper" : {
            "tumor" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.tumour.bam" % (x))) 
            },
            "normal" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.normal.bam" % (x)))
            },
            "reference" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "Homo_sapiens_assembly19.fasta"))},            
        },
        "varscan" : {
            "tumor" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.tumour.bam" % (x))) 
            },
            "normal" : lambda x, y: { 
                "class" : "File", 
                "path" : os.path.abspath(os.path.join(args.exome_dir, "testexome.%s.normal.bam" % (x)))
            },
            "reference" : { "class" : "File", "path" : os.path.abspath(os.path.join(args.data_dir, "Homo_sapiens_assembly19.fasta"))},                    
        }
    }

    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)
    
    for k,v in fake_metadata.items():
        for tool, tool_data in tools_templates.items():
            o = {}
            for t,d in tool_data.items():
                if callable(d):
                    o[t] = d(k, v)
                else:
                    o[t] = d
            outfile = os.path.join(args.outdir, "%s.%s.json" % (k, tool))
            with open(outfile, "w") as handle:
                handle.write(json.dumps(o))
                    
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
            if not os.path.exists(file_path + ".bai"):
                subprocess.check_call("samtools index %s" % (file_path), shell=True)
        if tmp[-1] == "vcf":
            subprocess.check_call("bgzip %s" % (file_path), shell=True)
            subprocess.check_call("tabix %s.gz" % (file_path), shell=True)
            

def run_extract(args):
    docstore = from_url(args.out_base)
    
    for id, ent in docstore.filter(file_ext="vcf", name=[
        "mutect.vcf", "muse.vcf", "pindel.vcf", "radia.vcf", "somatic_sniper.vcf", 
        "varscan.indel.vcf", "varscan.snp.vcf"
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
    "mutect",
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

    parser_gencwl = subparsers.add_parser('gen-cwl')
    parser_gencwl.add_argument("--outdir", default="cwl_job")
    parser_gencwl.add_argument("--exome-dir", default="testexomes")
    parser_gencwl.add_argument("--data-dir", default="data")
    parser_gencwl.set_defaults(func=run_gencwl)

    parser_download = subparsers.add_parser('download')
    parser_download.set_defaults(func=run_download)

    parser_extract = subparsers.add_parser('extract')
    parser_extract.add_argument("--out-base", default="test_mc3")
    parser_extract.add_argument("--out-dir", default="output")
    parser_extract.set_defaults(func=run_extract)

    parser_stats = subparsers.add_parser('stats')
    parser_stats.set_defaults(func=run_stats)
    parser_stats.add_argument("out_dir")

    parser_errors = subparsers.add_parser('errors')
    parser_errors.add_argument("--within", type=int, default=None)
    parser_errors.add_argument("--full", action="store_true", default=False)
    parser_errors.add_argument("--out-base", default="test_mc3")
    parser_errors.set_defaults(func=run_errors)
    
    args = parser.parse_args()

    args.func(args)
