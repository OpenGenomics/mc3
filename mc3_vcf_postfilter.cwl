
cwlVersion: v1.0
class: Workflow


inputs:
  museVCF:
    type: File
  pindelVCF:
    type: File
  indelocatorVCF:
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
    run: tools/vcf-tools/filter_vcf.cwl
    in:
      vcf: pindelVCF
      output_name:
        default: pindel.filtered.vcf
      cutoff:
        default: 3
    out:
      - output_vcf
  filterIndelocator:
    run: tools/vcf-tools/filter_vcf.cwl
    in:
      vcf: indelocatorVCF
      output_name:
        default: indelocator.filtered.vcf
      cutoff:
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
  filteredIndelocatorVCF:
    type: File
    outputSource:
      filterIndelocator/output_vcf
