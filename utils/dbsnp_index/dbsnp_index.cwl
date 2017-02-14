cwlVersion: v1.0
class: CommandLineTool
label: "index gzip tabix"
baseCommand: "/opt/samtools-1.3.1/htslib-1.3.1/tabix"
arguments: ["-p", "vcf"]

requirements:
    - class: DockerRequirement
      dockerImageId: "samtools:1.3.1"
#/opt/samtools-1.3.1/htslib-1.3.1/tabix -p vcf dbsnpfile.gz > dbsnpfile.gz.tbi
    
inputs:
    vcf:
        type: File
        inputBinding:
            valueFrom:
                $(self.basename)
            position: 1
outputs:
    indexed_vcf:
        type: File
        secondaryFiles: .tbi
        outputBinding:
            glob: $(inputs.vcf.basename)
