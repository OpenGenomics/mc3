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
      run: ./utils/reference_prep.cwl
      in:
        zipped: reference
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

    fpfilter:
      run: mc3_vcf_postfilter.cwl
      in:
        rawRadia: radia/mutations
        rawVarscans: varscan/snp_vcf
        rawSomsniper: somaticsniper/mutations
        rawMuse: muse/mutations
        rawPindel: pindel/somatic_vcf
        rawIndelocator: indelocator/mutations
        tumor: tumor
        normal: normal
        reference: prep_ref/prepped_ref
      out:
        - filteredRadiaVCF
        - fpfilteredSomaticsniperVCF
        - fpfilteredVarscansVCF
        - filteredMuseVCF
        - filteredPindelVCF
        - filteredIndelocatorVCF

    rehead_vcfs:
      run: ./tools/tcgavcf-tool/tcga-vcf-reheader.cwl
      in:
        varscani_vcf: varscan/indel_vcf
        varscans_vcf: fpfilter/fpfilteredVarscansVCF
        muse_vcf: fpfilter/filteredMuseVCF
        mutect_vcf: mutect/mutations
        somsniper_vcf: fpfilter/fpfilteredSomaticsniperVCF
        radia_vcf: fpfilter/filteredRadiaVCF
        pindel_vcf: fpfilter/filteredPindelVCF
        indelocator_vcf: fpfilter/filteredIndelocatorVCF
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
        - reheaded_varscani
        - reheaded_varscans
        - reheaded_muse
        - reheaded_mutect
        - reheaded_radia
        - reheaded_somsniper
        - reheaded_pindel
        - reheaded_indelocator

outputs:
  pindelVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_pindel
  somaticsniperVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_somsniper
  varscansVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_varscans
  varscaniVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_varscani
  museVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_muse
  mutectVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_mutect
  radiaVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_radia
  indelocatorVCF:
    type: File
    outputSource: rehead_vcfs/reheaded_indelocator
