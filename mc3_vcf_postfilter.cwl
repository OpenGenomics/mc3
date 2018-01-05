
cwlVersion: v1.0
class: Workflow


inputs:
  museVCF:
    type: File
  pindelVCF:
    type: File

steps:
  filterMuse:
    run: tools/muse-tool/muse.filter.cwl
    in:
      vcf: museVCF
      output_name:
        default: muse.filtered.vcf
    out:
      - output_vcf
  filterPindel:
    run: tools/vcftools-tools/filter_vcf.cwl
    in:
      vcf: pindelVCF
      output_name:
        default: pindel.filtered.vcf
      ad:
        default: 3
    out:
      - output_vcf

outputs:
  filteredMuseVCF:
    type: File
    outputSource:
      filterMuse/output_vcf
  filteredPindelVCF:
    type: File
    outputSource:
      filterPindel/output_vcf
      