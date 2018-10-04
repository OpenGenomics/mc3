
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
  tumor_analysis_uuid:
    type: string?
  tumor_bam_name:
    type: string
  tumor_aliquot_uuid:
    type: string?
  normal_analysis_uuid:
    type: string?
  normal_bam_name:
    type: string
  normal_aliquot_uuid:
    type: string?
  platform:
    type: string?
  center:
    type: string?

steps:

  sort_muse:
    in:
      vcf: museVCF
      output_name: 
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_muse:
    in:
      inputVCF: sort_muse/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID: 
        valueFrom: TUMOR
      vcfNormalID: 
        valueFrom: NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_mutect:
    in:
      vcf: mutectVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_mutect:
    in:
      inputVCF: sort_mutect/output_vcf
      refFasta: refFasta
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      addFilters:
        default: false
      vcfTumorID: tumorID
      vcfNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_somaticsniper:
    in:
      vcf: somaticsniperVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_somaticsniper:
    in:
      inputVCF: sort_somaticsniper/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID: 
        valueFrom: TUMOR
      vcfNormalID: 
        valueFrom: NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_varscans:
    in:
      vcf: varscansVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_varscans:
    in:
      inputVCF: sort_varscans/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID: 
        valueFrom: TUMOR
      vcfNormalID: 
        valueFrom: NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_varscani:
    in:
      vcf: varscaniVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_varscani:
    in:
      inputVCF: sort_varscani/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID: 
        valueFrom: TUMOR
      vcfNormalID: 
        valueFrom: NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_radia:
    in:
      vcf: radiaVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_radia:
    in:
      inputVCF: sort_radia/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID: 
        valueFrom: DNA_TUMOR
      vcfNormalID: 
        valueFrom: DNA_NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_indelocator:
    in:
      vcf: indelocatorVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_indelocator:
    in:
      inputVCF: sort_indelocator/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: false
      vcfTumorID: tumorID
      vcfNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  sort_pindel:
    in:
      vcf: pindelVCF
      output_name:
        valueFrom: $(inputs.vcf.nameroot).sort.vcf
    out:
      - output_vcf
    run: tools/vcf-tools/vcfsort.cwl

  standardize_pindel:
    in:
      inputVCF: sort_pindel/output_vcf
      outputVCF:
        valueFrom: $(inputs.inputVCF.nameroot).vep.vcf
      refFasta: refFasta
      addFilters:
        default: true
      vcfTumorID: 
        valueFrom: TUMOR
      vcfNormalID: 
        valueFrom: NORMAL
      newTumorID: tumorID
      newNormalID: normalID
    out: [vcf]
    run: tools/vcf2maf-tools/vcf2vcf.cwl

  rehead_vcfs:
    run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
    in:
      muse_vcf: standardize_muse/vcf
      mutect_vcf: standardize_mutect/vcf
      somsniper_vcf: standardize_somaticsniper/vcf
      varscani_vcf: standardize_varscani/vcf
      varscans_vcf: standardize_varscans/vcf
      radia_vcf: standardize_radia/vcf
      pindel_vcf: standardize_pindel/vcf
      indelocator_vcf: standardize_indelocator/vcf
      tumor_analysis_uuid: tumor_analysis_uuid
      tumor_bam_name: tumor_bam_name
      tumor_aliquot_uuid: tumor_aliquot_uuid
      tumor_aliquot_name: tumorID
      normal_analysis_uuid: normal_analysis_uuid
      normal_bam_name: normal_bam_name
      normal_aliquot_uuid: normal_aliquot_uuid
      normal_aliquot_name: normalID
      platform: platform
      center: center
    out:
      - reheaded_varscani
      - reheaded_varscans
      - reheaded_muse
      - reheaded_mutect
      - reheaded_radia
      - reheaded_somsniper
      - reheaded_pindel
      - reheaded_indelocator

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
        - rehead_vcfs/reheaded_muse
        - rehead_vcfs/reheaded_mutect
        - rehead_vcfs/reheaded_somsniper
        - rehead_vcfs/reheaded_varscans
        - rehead_vcfs/reheaded_varscani
        - rehead_vcfs/reheaded_radia
        - rehead_vcfs/reheaded_indelocator
        - rehead_vcfs/reheaded_pindel
    out: [output_vcf]
    run: tools/vcf-tools/merge_vcfs.cwl

  vcf2maf:
    in:
      inputVCF: merge_vcf/output_vcf
      refFasta: refFasta
      vepData: vepData
      tumorID: tumorID
      normalID: normalID
      vcfTumorID:
        valueFrom: PRIMARY
      vcfNormalID:
        valueFrom: NORMAL
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
