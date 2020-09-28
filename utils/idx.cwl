cwlVersion: v1.0
class: CommandLineTool
label: ".idx file"
baseCommand: ["igvtools"]
arguments: ["index"]
requirements:
    - class: DockerRequirement
      dockerPull: "wgspipeline/igvtools:v0.0.1"
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
    idx:
        type: File
        secondaryFiles:
          - .idx
        outputBinding:
          glob: $(inputs.to_index.basename)

