cwlVersion: v1.0
class: CommandLineTool
label: ".dict file"
baseCommand: ["java","-jar", "/opt/picard/CreateSequenceDictionary.jar"]
arguments: ["OUTPUT=$(inputs.to_dict.nameroot).dict"]
requirements:
    - class: DockerRequirement
      dockerPull: "opengenomics/picard-tool:1.122"
    - class: InitialWorkDirRequirement
      listing: 
        - entry: $(inputs.to_dict)
          writable: true

inputs:
    to_dict:
        type: File
        inputBinding:
            prefix: "REFERENCE="
            separate: false
        secondaryFiles:
            - .fai

outputs:
    dict:
        type: File
        secondaryFiles:
          - .fai
          - ^.dict
        outputBinding:
          glob: $(inputs.to_dict.basename)
