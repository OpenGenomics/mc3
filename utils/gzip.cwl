cwlVersion: v1.0
class: CommandLineTool
label: "unzip unzip_file.vcf.gz"
baseCommand: [gzip]
stdout: $(inputs.unzip_file.nameroot)
arguments: ["-c","-d"]

inputs:

  unzip_file:
    type: File
    inputBinding:
      position: 1

outputs:

  output:
    type: File
    outputBinding:
      glob: $(inputs.dbsnp.nameroot)
