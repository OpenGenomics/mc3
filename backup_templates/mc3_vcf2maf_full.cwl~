cwlVersion: v1.0
class: Workflow

requirements:
  - class: SubworkflowFeatureRequirement
  - class: StepInputExpressionRequirement
  - class: MultipleInputFeatureRequirement

inputs:
  tumorID:
    type: string
  normalID:
    type: string
  tumor:
    type: File
  normal:
    type: File
  bed_file:
    type: File?
  centromere:
    type: File
  cosmic:
    type: File
  dbsnp:
    type: File
  refFasta:
    type: File
  vepData:
    type: Directory
  markSamples:
    type: Directory
  markVariants:
    type: Directory

steps:
  call_variants:
    run: mc3_variant.cwl
    in:
      tumor: tumor
      normal: normal
      centromere: centromere
      bed_file: bed_file
      cosmic: cosmic
      dbsnp: dbsnp
      reference: refFasta
      tumorID: tumorID
      normalID: normalID
    out:
      - pindelVCF
      - somaticsniperVCF
      - varscansVCF
      - varscaniVCF
      - museVCF
      - mutectVCF
      - radiaVCF
      - indelocatorVCF

  convert:
    run: mc3_vcf2maf.cwl
    in:
      normalID: normalID
      tumorID: tumorID
      museVCF: call_variants/museVCF
      mutectVCF: call_variants/mutectVCF
      somaticsniperVCF: call_variants/somaticsniperVCF
      varscansVCF: call_variants/varscansVCF
      varscaniVCF: call_variants/varscaniVCF
      radiaVCF: call_variants/radiaVCF
      pindelVCF: call_variants/pindelVCF
      indelocatorVCF: call_variants/indelocatorVCF
      refFasta: refFasta
      vepData: vepData
      tumor_bam_name:
        source: tumor
        valueFrom: $(self.basename)
      normal_bam_name:
        source: normal
        valueFrom: $(self.basename)

    out:
      - outmaf

  markfiles:
    run: markfiles.cwl
    in:
      sampleID: tumorID
      mergedMAF: convert/outmaf
      markSamples: markSamples
      markVariants: markVariants
    out:
      - markedMAF

outputs:
  outmaf:
    type: File
    outputSource: markfiles/markedMAF    
