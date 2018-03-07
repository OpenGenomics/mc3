cwlVersion: v1.0
class: CommandLineTool
label: ".bai file"
baseCommand: ["samtools"]
arguments: ["index"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/samtools"
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
          - .bai
        outputBinding:
          glob: $(inputs.to_index.basename)
