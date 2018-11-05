cwlVersion: v1.0
class: CommandLineTool
label: "bgzip VCF"
baseCommand: ["bgzip"]
arguments: ["-c"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/samtools:1.3.1"
    - class: InitialWorkDirRequirement
      listing: [ $(inputs.unzipped) ]
stdout: $(inputs.unzipped.basename).gz

inputs:
    unzipped:
        type: File
        inputBinding:
            position: 1
outputs:
    bgzipped:
        type: File
        outputBinding:
          glob: $(inputs.unzipped.basename).gz
