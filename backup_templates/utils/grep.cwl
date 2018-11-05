cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["grep", "-h", "-e"]
requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement
stdout: $(inputs.outfile)

inputs:
  pattern:
    type: string
    inputBinding:
      shellQuote: true
      position: 1
  infile:
    type: File
    inputBinding:
      shellQuote: false
      position: 2
  outfile:
    type: string
    default: grepout.txt


outputs:
  grepout:
    type: stdout
