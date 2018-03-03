cwlVersion: v1.0
class: CommandLineTool
label: "index bgzip vcf"
baseCommand: ["tabix"]
arguments: ["-p","vcf"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/samtools:1.3.1"
    - class: InitialWorkDirRequirement
      listing: 
        - entry: $(inputs.vcf)
          writable: true

inputs:
    vcf:
        type: File
        inputBinding:
          position: 1
outputs:
    tabix:
        type: File
        secondaryFiles:
          - .tbi
        outputBinding:
          glob: $(inputs.vcf.basename)
