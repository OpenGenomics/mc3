cwlVersion: v1.0
class: Workflow

requirements:
  - class: SubworkflowFeatureRequirement
  - class: StepInputExpressionRequirement
  - class: InlineJavascriptRequirement

inputs:
  sampleID:
    type: string
  mergedMAF:
    type: File
  mark1dir:
    type: Directory
  mark2dir:
    type: Directory

steps:
  firstMarkPrep:
    run: ./utils/grep.cwl
    in:
      pattern: sampleID
      indir: mark1dir
    out:
      - grepout

outputs:
  testout: 
    type: File
    outputSource: firstMarkPrep/grepout

