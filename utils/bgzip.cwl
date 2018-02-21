cwlVersion: v1.0
class: CommandLineTool
label: "bgzip VCF"
baseCommand: ["bgzip"]
requirements:
    - class: DockerRequirement
      dockerImageId: "samtools:1.3.1"
stdout: $(inputs.file.basename).gz

inputs:
    file:
        type: File
        inputBinding:
            position: 1
outputs:
    bgzipped_file:
        type: File
        outputBinding:
          glob: $(inputs.file.basename).gz
