cwlVersion: v1.0
class: CommandLineTool
label: "unzip file"
baseCommand: [gzip]
stdout: $(inputs.zipped.nameroot)
arguments: ["-c","-d"]

inputs:

  zipped:
    type: File
    inputBinding:
      position: 1

outputs:

  unzipped:
    type: File
    outputBinding:
      glob: $(inputs.zipped.nameroot)
