cwlVersion: v1.0
class: Workflow

requirements:
  - class: SubworkflowFeatureRequirement

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
  filter:
    run: mc3_vcf_postfilter.cwl
    in:
      museVCF: museVCF
      pindelVCF: pindelVCF
    out:
      - filteredMuseVCF
      - filteredPindelVCF
    
  convert:
    run: mc3_vcf2maf.cwl
    in:
      normalID: normalID
      tumorID: tumorID
      museVCF: filter/filteredMuseVCF
      mutectVCF: mutectVCF
      somaticsniperVCF: somaticsniperVCF
      varscansVCF: varscansVCF
      varscaniVCF: varscaniVCF
      radiaVCF: radiaVCF
      pindelVCF: filter/filteredPindelVCF
      indelocatorVCF: indelocatorVCF
      refFasta: refFasta
      vepData: vepData
    out:
      - outmaf

outputs:
  outmaf:
    type: File
    outputSource: convert/outmaf

      
