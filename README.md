# mc3

The TCGA PanCancer Atlas MC3 set is a re-calling of uniform files to remove batch effects and enable pancancer analysis.

Workflows to reproduce work presented in the paper "Scalable Open Science Approach for Mutation Calling of Tumor Exomes Using Multiple Genomic Pipelines"
Ellrott K, Bailey MH, Saksena G, Covington KR, Kandoth C, Stewart C, Hess J,
Ma S, Chiotti KE, McLellan M, Sofia HJ, Hutter C, Getz G, Wheeler D, Ding L; MC3
Working Group; Cancer Genome Atlas Research Network. Cell Syst. 2018 Mar 28;6(3):271-281.e7. doi: 10.1016/j.cels.2018.03.002. PubMed PMID: 29596782.  (http://www.cell.com/cell-systems/fulltext/S2405-4712(18)30096-6)

Example run:

 # Running MC3

 ## Original Job list
 https://www.synapse.org/#!Synapse:syn4977808

 ## Obtain GDC download token
Instructions on how to obtain Controlled Data Access for TCGA data at https://gdc.cancer.gov/access-data/obtaining-access-controlled-data

 ## Obtain BAM files

 ../tools/gdc-download-tool/gdc-client download -t ../gdc.token fb0bed68-4f2c-400d-8460-a62310fa95bf

 ../tools/gdc-download-tool/gdc-client download -t ../gdc.token ded8b01f-5301-49c8-bfdc-fc8343291e6d

Example Variant Calling input
```json
{
    "tumor" : {
      "class" : "File",
      "path" : "/mnt/mc3/mc3/seq/ded8b01f-5301-49c8-bfdc-fc8343291e6d/C317.TCGA-AB-2901-03A-01W-0733-08.4.bam"
    },
    "normal" : {
      "class" : "File",
       "path" : "/mnt/mc3/mc3/seq/fb0bed68-4f2c-400d-8460-a62310fa95bf/C317.TCGA-AB-2901-11A-01W-0732-08.4.bam"
    },
    "centromere" : {
      "class" : "File",
      "path" : "/mnt/mc3/mc3/vcfs//centromere_hg19.bed"
    },
    "cosmic" : {
      "class" : "File",
        "path" : "/mnt/mc3/mc3/ref/b37_cosmic_v54_120711.vcf.gz"
    },
    "dbsnp" : {
        "class" : "File",
        "path" : "/mnt/mc3/mc3/ref/dbsnp_132_b37.leftAligned.vcf.gz"
    },
    "reference" : {
        "class" : "File",
        "path"  :  "/mnt/mc3/mc3/ref/Homo_sapiens_assembly19.fasta.gz"
    },
    "bed_file" : {
        "class" : "File",
        "path" : "/mnt/mc3/mc3/vcfs/gaf_20111020+broad_wex_1.1_hg19.bed"
    },
    "tumor_analysis_uuid" : "cf8c9b38-246d-46aa-b557-6c882e438161",
    "tumor_aliquot_uuid" : "bac6a6d2-8c40-43cd-ab4c-16d3f8a06eb6",
    "normal_analysis_uuid" : "c404dcfb-e580-4cf2-8fe6-6990ce2ce03a",
    "normal_aliquot_uuid" : "22f3f166-41a7-4058-a315-d72e1d7becd6",
    "platform" : "illumina",
    "center" : "OHSU"
}
```


Example Vcf2Maf input
```json
{
    "normalID" : "TCGA-AB-2901-11A-01W-0732-08",
    "tumorID" : "TCGA-AB-2901-03A-01W-0733-08",
   "museVCF" : {
     "class" : "File",
     "path" : "/mnt/mc3/mc3/test/C317.TCGA-AB-2901-03A-01W-0733-08.4.muse.tcga_filtered.reheadered.vcf"
   },
   "mutectVCF" : {
       "class" : "File",
       "path"  : "/mnt/mc3/mc3/vcfs/008ddf20-f7fb-4673-b2ed-b5d5212fbf09_TB_NT_bac6a6d2-8c40-43cd-ab4c-16d3f8a06eb6_22f3f166-41a7-4058-a315-d72e1d7becd6.oxoG.snp.capture.tcga.vcf",
   },
    "indelocatorVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/vcfs/008ddf20-f7fb-4673-b2ed-b5d5212fbf09_TB_NT_bac6a6d2-8c40-43cd-ab4c-16d3f8a06eb6_22f3f166-41a7-4058-a315-d72e1d7becd6.indel.capture.tcga.vcf"
    },
   "somaticsniperVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/C317.TCGA-AB-2901-03A-01W-0733-08.4.SomaticSniper.annotated.tcga_filtered.reheadered.vcf"
   },
   "varscansVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/C317.TCGA-AB-2901-03A-01W-0733-08.4.varscan.snp.annotated.tcga_filtered.reheadered.vcf",
   },
   "varscaniVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/C317.TCGA-AB-2901-03A-01W-0733-08.4.varscan.indel.annotated.tcga_filtered.reheadered.vcf"
   },
   "radiaVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/filtered.radia.tcga_filtered.reheadered.vcf"
   },
   "pindelVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/C317.TCGA-AB-2901-03A-01W-0733-08.4.pindel.somatic.tcga_filtered.reheadered.vcf"
   },
   "indelocatorVCF" : {
       "class" : "File",
       "path" : "/mnt/mc3/mc3/test/indelocator_filtered.reheadered.vcf"
   },
   "vepData" : {
       "class" : "Directory",
       "path" : "/mnt/mc3/mc3/vep-data"
   },
   "refFasta" : {
     "class" : "File",
     "path" : "Homo_sapiens_assembly19.fasta.gz"
   }
}
```
