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
  markSamples:
    type: Directory
  markVariants:
    type: Directory

steps:
  firstMarkPrep:
    run: ./utils/dirgrep.cwl
    in:
      pattern: sampleID
      infiles: markSamples
    out:
      - grepout

  firstMap:
    run: ./tools/markfiles-tool/key-map.cwl
    in:
      markList: firstMarkPrep/grepout
      mergedMAF: mergedMAF
      outMAF:
        valueFrom: $(inputs.mergedMAF.nameroot).map1.maf
    out:
      - mappedMAF

  firstSort:
    run:
      class: CommandLineTool
      requirements:
        - class: ShellCommandRequirement
      arguments:
        - {valueFrom: "sort -o", position: 1, shellQuote: false}
      inputs:
        toSort:
          type: File
          inputBinding:
            position: 3
        outSort:
          type: string
          inputBinding:
            position: 2
      outputs:
        sortedMAF:
          type: File
          outputBinding:
            glob: $(inputs.outSort)
    in:
      toSort: firstMap/mappedMAF
      outSort: 
        valueFrom: $(inputs.toSort.nameroot).sort1.maf
    out:
      - sortedMAF

  firstReduce:
    run: ./tools/markfiles-tool/key-reduce.cwl
    in:
      mappedMAF: firstSort/sortedMAF
      origMAF: mergedMAF
      appendFlag:
        default: true
      outMAF: 
        valueFrom: $(inputs.mappedMAF.nameroot).reduce1.maf
    out:
      - reducedMAF

  secondMarkPrep:
    run: ./utils/dirgrep.cwl
    in:
      pattern: sampleID
      infiles: markVariants
    out:
      - grepout

  secondMap:
    run: ./tools/markfiles-tool/key-map.cwl
    in:
      markList: secondMarkPrep/grepout
      mergedMAF: firstReduce/reducedMAF
      useNorm: 
        default: 1
      outMAF:
        valueFrom: $(inputs.mergedMAF.nameroot).map2.maf
    out:
      - mappedMAF

  secondSort:
    run:
      class: CommandLineTool
      requirements:
        - class: ShellCommandRequirement
      arguments:
        - {valueFrom: "sort -o", position: 1, shellQuote: false}
      inputs:
        toSort:
          type: File
          inputBinding:
            position: 3
        outSort:
          type: string
          inputBinding:
            position: 2
      outputs:
        sortedMAF:
          type: File
          outputBinding:
            glob: $(inputs.outSort)
    in:
      toSort: secondMap/mappedMAF
      outSort:
        valueFrom: $(inputs.toSort.nameroot).sort2.maf
    out:
      - sortedMAF

  secondReduce:
    run: ./tools/markfiles-tool/key-reduce.cwl
    in:
      mappedMAF: secondSort/sortedMAF
      origMAF: mergedMAF
      appendFlag:
        default: true
      outMAF:
        valueFrom: $(inputs.origMAF.nameroot).marked.maf
    out:
      - reducedMAF

outputs:
  markedMAF:
    type: File
    outputSource: secondReduce/reducedMAF
