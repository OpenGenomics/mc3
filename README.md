# mc3

The TCGA PanCancer Atlas MC3 set is a re-calling of uniform files to remove batch effects and enable pancancer analysis.

Example run:

 # Running MC3

 ## Original Job list
 https://www.synapse.org/#!Synapse:syn4977808

 ## Obtain GDC download token

 ## Obtain BAM files

 ../tools/gdc-download-tool/gdc-client download -t ../gdc.token fb0bed68-4f2c-400d-8460-a62310fa95bf

 ../tools/gdc-download-tool/gdc-client download -t ../gdc.token ded8b01f-5301-49c8-bfdc-fc8343291e6d
 
Example Variant Calling input
```json
{
    "tumor" : {
      "class" : "File",
      "path" : "/mnt/mc3/mc3/test_in/ded8b01f-5301-49c8-bfdc-fc8343291e6d/C317.TCGA-AB-2901-03A-01W-0733-08.4.bam"
    },
    "normal" : {
      "class" : "File",
       "path" : "/mnt/mc3/mc3/test_in/fb0bed68-4f2c-400d-8460-a62310fa95bf/C317.TCGA-AB-2901-11A-01W-0732-08.4.bam"
    },
    "centromere" : {
      "class" : "File",
      "path" : "/mnt/mc3/mc3/test_in/data/centromere_hg19.bed"
    },
    "cosmic" : {
      "class" : "File",
        "path" : "/mnt/mc3/mc3/test_in/data/b37_cosmic_v54_120711.vcf.gz"
    },
    "dbsnp" : {
        "class" : "File",
        "path" : "/mnt/mc3/mc3/test_in/data/dbsnp_132_b37.leftAligned.vcf.gz"
    },
    "reference" : {
        "class" : "File",
        "path"  :  "/mnt/mc3/mc3/test_in/data/Homo_sapiens_assembly19.fasta"
    }
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

