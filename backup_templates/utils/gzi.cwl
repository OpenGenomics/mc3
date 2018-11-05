cwlVersion: v1.0
class: CommandLineTool
label: "gzi file"
baseCommand: ["samtools"]
arguments: ["faidx"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/samtools:1.3.1"
    - class: InitialWorkDirRequirement
      listing: 
        - entry: $(inputs.to_gzi)
          writable: true

inputs:
    to_gzi:
        type: File
        inputBinding:
            position: 1
outputs:
    gzi:
        type: File
        secondaryFiles:
          - .fai
          - .gzi
        outputBinding:
          glob: $(inputs.to_gzi.basename)
