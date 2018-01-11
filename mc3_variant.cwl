cwlVersion: v1.0
class: Workflow
id: full_mc3

requirements:
  - class: StepInputExpressionRequirement

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
  number_of_procs:
    type: int
    default: 6

steps:
    normal_pileup:
      run: ./tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: normal
        reference: reference
        noBaq:
          default: true
      out:
        - output

    tumor_pileup:
      run: ./tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: tumor
        reference: reference
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
        reference: reference
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
        reference: reference
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
       reference: reference
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
       reference: reference
     out:
       - mutations

    somaticsniper:
      run: ./tools/somaticsniper-tool/somatic_sniper.cwl.yaml
      in:
        tumor: tumor
        normal: normal
        reference: reference
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
        reference: reference
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

    somaticsniper-fpfilter:
      run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
      in:
        vcf-file: somaticsniper/mutations
        bam-file: tumor
        reference: reference
        output:
          default: somatic_sniper_fpfilter.vcf
      out:
        - filtered_vcf

    varscan-fpfilter:
      run: ./tools/fpfilter-tool/fpfilter.cwl.yaml
      in:
        vcf-file: varscan/snp_vcf
        bam-file: tumor
        reference: reference
        output:
          default: varscan_fpfilter.vcf
      out:
        - filtered_vcf

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
