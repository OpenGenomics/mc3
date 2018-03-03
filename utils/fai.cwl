cwlVersion: v1.0
class: CommandLineTool
label: ".fai file"
baseCommand: ["samtools"]
arguments: ["faidx"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/samtools:1.3.1"
    - class: InitialWorkDirRequirement
      listing: 
        - entry: $(inputs.to_index)
          writable: true

inputs:
    to_index:
        type: File
        inputBinding:
            position: 1
outputs:
    faidx:
        type: File
        secondaryFiles:
          - .fai
        outputBinding:
          glob: $(inputs.to_index.basename)
