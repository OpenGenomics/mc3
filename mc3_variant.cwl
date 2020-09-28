cwlVersion: v1.0
class: Workflow
id: variant_mc3

requirements:
  - class: StepInputExpressionRequirement
  - class: SubworkflowFeatureRequirement
  - class: InlineJavascriptRequirement

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
    type: File?
  number_of_procs:
    type: int
    default: 6
  tumorID:
    type: string
  normalID:
    type: string

steps:
  prep_ref:
    run: ./utils/reference_prep.cwl
    in:
      zipped: reference
    out:
      - prepped_ref

  normal_pileup:
    run: ./tools/samtools-pileup-tool/sam_pileup.cwl
    in:
      input: normal
      reference: prep_ref/prepped_ref
      noBaq:
        default: true
    out:
      - output

  tumor_pileup:
    run: ./tools/samtools-pileup-tool/sam_pileup.cwl
    in:
      input: tumor
      reference: prep_ref/prepped_ref
      noBaq:
        default: true
    out:
      - output

  varscan:
    run: ./tools/varscan-tool/varscan_somatic.cwl
    in:
      tumor_pileup: tumor_pileup/output
      normal_pileup: normal_pileup/output
      min_coverage:
        default: 3
      min_var_freq:
        default: 0.08
      p_value:
        default: 0.1
    out:
      - snp_vcf
      - indel_vcf

  muse:
    run: ./tools/muse-tool/muse.cwl
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
    run: ./tools/mutect-tool/mutect.cwl
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

  somaticsniper:
    run: ./tools/somaticsniper-tool/somatic_sniper.cwl
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
    run: ./tools/pindel-tool/pindel-somatic.cwl
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

  reformat_indelocator:
    run: ./tools/indelocator-tool/reformat_vcf.cwl
    in:
      input_vcf: indelocator/mutations
      output_vcf:
        valueFrom: $(inputs.input_vcf.nameroot).reformatted.vcf
    out:
      - mutations

  fpfilter:
    run: mc3_vcf_postfilter.cwl
    in:
      rawRadia: radia/mutations
      rawVarscans: varscan/snp_vcf
      rawSomsniper: somaticsniper/mutations
      rawMuse: muse/mutations
      rawPindel: pindel/somatic_vcf
      rawIndelocator: reformat_indelocator/mutations
      tumor: tumor
      normal: normal
      reference: prep_ref/prepped_ref
      tumorID: tumorID
      normalID: normalID

    out:
      - filteredRadiaVCF
      - fpfilteredSomaticsniperVCF
      - fpfilteredVarscansVCF
      - filteredMuseVCF
      - filteredPindelVCF
      - filteredIndelocatorVCF

outputs:
  pindelVCF:
    type: File
    outputSource: fpfilter/filteredPindelVCF
  somaticsniperVCF:
    type: File
    outputSource: fpfilter/fpfilteredSomaticsniperVCF
  varscansVCF:
    type: File
    outputSource: fpfilter/fpfilteredVarscansVCF
  varscaniVCF:
    type: File
    outputSource: varscan/indel_vcf
  museVCF:
    type: File
    outputSource: fpfilter/filteredMuseVCF
  mutectVCF:
    type: File
    outputSource: mutect/mutations
  radiaVCF:
    type: File
    outputSource: fpfilter/filteredRadiaVCF
  indelocatorVCF:
    type: File
    outputSource: fpfilter/filteredIndelocatorVCF
