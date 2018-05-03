cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["cat"]
requirements:
  - class: ShellCommandRequirement
stdout: $(inputs.outfile)

inputs:
  infiles:
    type: File[]
    inputBinding:
      position: 1
  outfile:
    type: string
    default: catout.txt

outputs:
  catout:
    type: stdout
