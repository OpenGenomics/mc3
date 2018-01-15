cwlVersion: v1.0
class: Workflow

requirements:
  - class: InlineJavascriptRequirement
  - class: StepInputExpressionRequirement
  - class: MultipleInputFeatureRequirement

inputs:
  normalID:
    type: string
  tumorID:
    type: string
  museVCF:
    type: File
  mutectVCF:
    type: File
  somaticsniperVCF:
    type: File
  varscansVCF:
    type: File
  varscaniVCF:
    type: File
  radiaVCF:
    type: File
  pindelVCF:
    type: File
  indelocatorVCF:
    type: File
  refFasta:
    type: File
  vepData:
    type: Directory

steps:

  sort_muse:
    in:
      vcf: museVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_muse:
    in:
      inputVCF: sort_muse/output_vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_mutect:
    in:
      vcf: mutectVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_mutect:
    in:
      inputVCF: sort_mutect/output_vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_somaticsniper:
    in:
      vcf: somaticsniperVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_somaticsniper:
    in:
      inputVCF: sort_somaticsniper/output_vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_varscans:
    in:
      vcf: varscansVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_varscans:
    in:
      inputVCF: sort_varscans/output_vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_varscani:
    in:
      vcf: varscaniVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_varscani:
    in:
      inputVCF: sort_varscani/output_vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_radia:
    in:
      vcf: radiaVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_radia:
    in:
      inputVCF: sort_radia/output_vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_indelocator:
    in:
      vcf: indelocatorVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_indelocator:
    in:
      inputVCF: sort_indelocator/output_vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_pindel:
    in:
      vcf: pindelVCF
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  normalize_pindel:
    in:
      inputVCF: sort_pindel/output_vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID:
        default: PRIMARY
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  merge_vcf:
    in:
      keys:
        default:
          - MUSE
          - MUTECT
          - SOMATICSNIPER
          - VARSCANS
          - VARSCANI
          - RADIA
          - INDELOCATOR
          - PINDEL
      vcfs:
        - normalize_muse/vcf
        - normalize_mutect/vcf
        - normalize_somaticsniper/vcf
        - normalize_varscans/vcf
        - normalize_varscani/vcf
        - normalize_radia/vcf
        - normalize_indelocator/vcf
        - sort_pindel/output_vcf

      vepData: vepData
    out: [output_vcf]
    run: tools/vcf-tools/merge_vcfs.cwl

  vcf2maf:
    in:
      inputVCF: merge_vcf/output_vcf
      refFasta: refFasta
      vepData: vepData
      tumorID: tumorID
      normalID: normalID
      vcfNormalID:
        default: NORMAL
      vcfTumorID:
        default: PRIMARY
      retainInfo:
        default:
          - COSMIC
          - CENTERS
          - CONTEXT
          - DBVS
    out:
      - maf
      - vepvcf
    run: tools/vcf2maf-tools/vcf2maf.cwl

outputs:
  outmaf:
    type: File
    outputSource: vcf2maf/maf
  vepvcf:
    type: File
    outputSource: vcf2maf/vepvcf
