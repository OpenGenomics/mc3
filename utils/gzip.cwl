cwlVersion: v1.0
class: CommandLineTool
label: "unzip dbsnp.vcf.gz"
baseCommand: [gzip]
stdout: $(inputs.dbsnp.nameroot)
arguments: ["-c","-d"]

inputs:

  dbsnp:
    type: File
    inputBinding:
      position: 1

outputs:

  output:
    type: File
    outputBinding:
      glob: $(inputs.dbsnp.nameroot)
