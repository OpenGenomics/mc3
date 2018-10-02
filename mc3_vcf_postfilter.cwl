
cwlVersion: v1.0
class: Workflow


inputs:
  rawRadia:
    type: File
  rawVarscans:
    type: File
  rawSomsniper:
    type: File
  rawMuse:
    type: File
  rawPindel:
    type: File
  rawIndelocator:
    type: File
  tumor:
    type: File
  normal:
    type: File
  reference:
    type: File
  tumorID:
    type: string
  normalID:
    type: string

steps:
  filterRadia:
    run: ./tools/radia-tool/radia_filter.cwl
    in:
      inputVCF: rawRadia
      tumor: tumor
      normal: normal
      patientId:
        default: tumorID
      reference: reference
    out:
      - mutations

  fpfilterSomaticSniper:
    run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
    in:
      vcf-file: rawSomsniper
      bam-file: tumor
      reference: reference
      output:
        default: somatic_sniper_fpfilter.vcf
    out:
      - filtered_vcf

  fpfilterVarscans:
    run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
    in:
      vcf-file: rawVarscans
      bam-file: tumor
      reference: reference
      output:
        default: varscan_fpfilter.vcf
    out:
      - filtered_vcf

  filterMuse:
    run: ./tools/muse-tool/muse.filter.cwl
    in:
      vcf: rawMuse
      output_name:
        default: muse_filtered.vcf
    out:
      - output_vcf

  filterPindel:
    run: ./tools/vcf-tools/filter_vcf.cwl
    in:
      vcf: rawPindel
      output_name:
        default: pindel_filtered.vcf
      cutoff:
        default: 3
    out:
      - output_vcf

  filterIndelocator:
    run: tools/vcf-tools/filter_vcf.cwl
    in:
      vcf: rawIndelocator
      output_name:
        default: indelocator_filtered.vcf
      cutoff:
        default: 3
      tumorID: tumorID
      normalID: normalID
    out:
      - output_vcf

outputs:
  filteredRadiaVCF:
    type: File
    outputSource:
      filterRadia/mutations
  fpfilteredSomaticsniperVCF:
    type: File
    outputSource:
      fpfilterSomaticSniper/filtered_vcf
  fpfilteredVarscansVCF:
    type: File
    outputSource:
      fpfilterVarscans/filtered_vcf
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
