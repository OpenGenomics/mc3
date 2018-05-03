cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["grep", "-e"]
requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement
stdout: $(inputs.pattern).txt

inputs:
  pattern:
    type: string
    inputBinding:
      position: 1
  infiles:
    type: File[]?
    doc: "Array of files to search for 'pattern'; do not provide input for 'indir'."
    inputBinding:
      position: 2
  indir:
    type: Directory?
    doc: "Directory of files to search for 'pattern'; do not provide input for 'infiles'."
    inputBinding:
      position: 2
      valueFrom: $(inputs.indir.listing)

outputs:
  grepout:
    type: stdout
