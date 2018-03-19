cwlVersion: v1.0
class: Workflow
id: reference file prep

requirements:
  - class: StepInputExpressionRequirement

inputs: 
    zipped:
        type: File

steps:
    unzip_ref:
        run: ./utils/gzip.cwl
        in:
            zipped: zipped
        out:
            - unzipped
    index_ref:
        run: ./utils/fai.cwl
        in:
            to_index: unzip_ref/unzipped
        out:
            - faidx
    dict_ref:
        run: ./utils/dict.cwl
        in:
            to_dict: index_ref/faidx
        out:
            - dict

outputs:
    prepped_ref:
        type: File
        secondaryFiles:
            - ^.fai
            - .dict
        outputSource: dict_ref/dict
