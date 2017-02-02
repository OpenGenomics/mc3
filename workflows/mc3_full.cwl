cwlVersion: v1.0
class: Workflow
id: full_mc3

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

steps:
    normal_pileup:
      run: ../tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: normal
        reference: reference
      out:
        - output

    tumor_pileup:
      run: ../tools/samtools-pileup-tool/sam_pileup.cwl.yaml
      in:
        input: tumor
        reference: reference
      out:
        - output
    
    varscan:
      run: ../tools/varscan-tool/varscan_somatic.cwl.yaml
      in:
        tumor_pileup: tumor_pileup/output
        normal_pileup: normal_pileup/output
      out:
        - snp_vcf
        - indel_vcf
    
    muse:
      run: ../tools/muse-tool/muse.cwl.yaml
      in: 
        tumor: tumor
        normal: normal
        reference: reference
      out:
        - mutations
    
    mutect:
      run: ../tools/mutect-tool/mutect.cwl.yaml
      in: 
        tumor: tumor
        normal: normal
        reference: reference
      out:
        - mutations

    radia:
      run: ../tools/radia-tool/radia.cwl.yaml
      in: 
        tumor: tumor
        normal: normal
        reference: reference
      out:
        - mutations
    
    somaticsniper:
      run: ../tools/somaticsniper-tool/somatic_sniper.cwl.yaml
      in: 
        tumor: tumor
        normal: normal
        reference: reference
      out:
        - mutations
      
    pindel:
      run: ../tools/pindel-tool/pindel-somatic.cwl.yaml
      in: 
        tumor: tumor
        normal: normal
        reference: reference
      out:
        - mutations

    somaticsniper-fpfilter:
      run: ../tools/fpfilter-tool/fpfilter.cwl.yaml
      in: 
        vcf-file: somaticsniper/mutations
        bam-file: tumor
      out:
        - output 

    varscan-fpfilter:
      run: ../tools/fpfilter-tool/fpfilter.cwl.yaml
      in: 
        vcf-file: varscan/snp_vcf
        bam-file: tumor
      out:
        - output 


outputs:
  pindel-out:
    type: File
    outputSource: pindel/mutations
  varscan-out: 
    type: File
    outputSource: somaticsniper-fpfilter/output
  muse-out:
    type: File
    outputSource: muse/mutations
  mutect-out:
    type: File
    outputSource: mutect/mutations



