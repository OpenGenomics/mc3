cwlVersion: v1.0
class: Workflow
id: variant_mc3

requirements:
  - class: StepInputExpressionRequirement
  - class: SubworkflowFeatureRequirement

inputs:
  tumor:
    type: File
    secondaryFiles:
      - .bai
  normal:
    type: File
    secondaryFiles:
      - .bai
  reference:
    type: File
    secondaryFiles:
      - .fai
  dbsnp:
    type: File
    secondaryFiles:
      - .tbi
  cosmic:
    type: File
    secondaryFiles:
      - .tbi
  centromere:
    type: File
  bed_file:
    type: File
  number_of_procs:
    type: int
    default: 6
  tumor_analysis_uuid:
    type: string
  tumor_bam_name:
    type: string
    default: tumor.nameroot
  tumor_aliquot_uuid:
    type: string
  tumor_aliquot_name:
    type: string
  normal_analysis_uuid:
    type: string
  normal_bam_name:
    type: string
    default: normal.nameroot
  normal_aliquot_uuid:
    type: string
  normal_aliquot_name:
    type: string
  platform:
    type: string
  center:
    type: string

steps:
    prep_ref:
      in:
        zipped: reference

      run:
        class: Workflow
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
      out:
        - prepped_ref

    normal_pileup:
      run: ./tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: normal
        reference: prep_ref/prepped_ref
        noBaq:
          default: true
      out:
        - output

    tumor_pileup:
      run: ./tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: tumor
        reference: prep_ref/prepped_ref
        noBaq:
          default: true
      out:
        - output

    varscan:
      run: ./tools/varscan-tool/varscan_somatic.cwl.yaml
      in:
        tumor_pileup: tumor_pileup/output
        normal_pileup: normal_pileup/output
        min_coverage:
          default: 3
        min_var_freq:
          default: 0.08
        p_value:
          default: 0.10
      out:
        - snp_vcf
        - indel_vcf

    muse:
      run: ./tools/muse-tool/muse.cwl.yaml
      in:
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
        known: dbsnp
        mode: { default: wxs }
        ncpus: number_of_procs
      out:
        - mutations

    mutect:
      run: ./tools/mutect-tool/mutect.cwl.yaml
      in:
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
        cosmic: cosmic
        dbsnp: dbsnp
        ncpus: number_of_procs
      out:
        - mutations

    radia:
     run: ./tools/radia-tool/radia.cwl
     in:
       tumor: tumor
       normal: normal
       reference: prep_ref/prepped_ref
       number_of_procs: number_of_procs
     out:
       - mutations

    radia-filter:
     run: ./tools/radia-tool/radia_filter.cwl
     in:
       inputVCF: radia/mutations
       tumor: tumor
       normal: normal
       patientId:
         default: tumor.nameroot
       reference: prep_ref/prepped_ref
     out:
       - mutations

    somaticsniper:
      run: ./tools/somaticsniper-tool/somatic_sniper.cwl.yaml
      in:
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
        mapq:
          default: 1
        gor:
          default: true
        loh:
          default: true
      out:
        - mutations

    pindel:
      run: ./tools/pindel-tool/pindel-somatic.cwl.yaml
      in:
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
        centromere: centromere
        balance_cutoff:
          default: 0
        window_size:
          default: 0.1
        min_perfect_match_around_BP:
          default: 6
        max_range_index:
          default: 1
        procs: number_of_procs
      out:
        - somatic_vcf

    indelocator:
      run: ./tools/indelocator-tool/indelocator.cwl
      in:
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
        bed_file: bed_file
      out:
        - mutations

    somaticsniper-fpfilter:
      run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
      in:
        vcf-file: somaticsniper/mutations
        bam-file: tumor
        reference: prep_ref/prepped_ref
        output:
          default: somatic_sniper_fpfilter.vcf
      out:
        - filtered_vcf

    varscan-fpfilter:
      run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
      in:
        vcf-file: varscan/snp_vcf
        bam-file: tumor
        reference: prep_ref/prepped_ref
        output:
          default: varscan_fpfilter.vcf
      out:
        - filtered_vcf

    rehead_varscani:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: varscan/indel_vcf
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_varscans:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: varscan-fpfilter/filtered_vcf
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_muse:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: muse/mutations
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_mutect:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: mutect/mutations
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_radia:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: radia-filter/mutations
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_somaticsniper:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: somaticsniper-fpfilter/filtered_vcf
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

    rehead_pindel:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        input_vcf: pindel/somatic_vcf
        tumor_analysis_uuid: tumor_analysis_uuid
        tumor_bam_name: tumor_bam_name
        tumor_aliquot_uuid: tumor_aliquot_uuid
        tumor_aliquot_name: tumor_aliquot_name
        normal_analysis_uuid: normal_analysis_uuid
        normal_bam_name: normal_bam_name
        normal_aliquot_uuid: normal_aliquot_uuid
        normal_aliquot_name: normal_aliquot_name
        platform: platform
        center: center
      out:
        - rehead_vcf

outputs:
  pindelVCF:
    type: File
    outputSource: pindel/somatic_vcf
  somaticsniperVCF:
    type: File
    outputSource: somaticsniper-fpfilter/filtered_vcf
  varscansVCF:
    type: File
    outputSource: varscan-fpfilter/filtered_vcf
  varscaniVCF:
    type: File
    outputSource: varscan/indel_vcf
  museVCF:
    type: File
    outputSource: muse/mutations
  mutectVCF:
    type: File
    outputSource: mutect/mutations
  radiaVCF:
    type: File
    outputSource: radia-filter/mutations
  pindelVCF_rehead:
    type: File
    outputSource: rehead_pindel/rehead_vcf
  somaticsniperVCF_rehead:
    type: File
    outputSource: rehead_somaticsniper/rehead_vcf
  varscansVCF_rehead:
    type: File
    outputSource: rehead_varscans/rehead_vcf
  varscaniVCF_rehead:
    type: File
    outputSource: rehead_varscani/rehead_vcf
  museVCF_rehead:
    type: File
    outputSource: rehead_muse/rehead_vcf
  mutectVCF_rehead:
    type: File
    outputSource: rehead_mutect/rehead_vcf
  radiaVCF_rehead:
    type: File
    outputSource: rehead_radia/rehead_vcf
