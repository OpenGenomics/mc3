  .. class:: infomark

  **What it does**

  ::

  VarScan is a platform-independent mutation caller for targeted, exome, and whole-genome resequencing data generated on Illumina, SOLiD, Life/PGM, Roche/454, and similar instruments. The newest version, VarScan 2, is written in Java, so it runs on most  operating systems. It can be used to detect different types of variation:

  Germline variants (SNPs an dindels) in individual samples or pools of samples.
  Multi-sample variants (shared or private) in multi-sample datasets (with mpileup).
  Somatic mutations, LOH events, and germline variants in tumor-normal pairs.
  Somatic copy number alterations (CNAs) in tumor-normal exome data.


  **Input**

  ::

  mpileup normal file - The SAMtools mpileup file for normal
  mpileup tumor file - The SAMtools mpileup file for tumor


  **Parameters**

  ::

  min-coverage
  Minimum read depth at a position to make a call [8]

  min-coverage-normal
  Minimum coverage in normal to call somatic [8]

  min-coverage-tumor
  Minimum coverage in tumor to call somatic [6]

  min-var-freq
  Minimum variant frequency to call a heterozygote [0.10]

  min-freq-for-hom
  Minimum frequency to call homozygote [0.75]

  normal-purity
  Estimated purity (non-tumor content) of normal sample [1.00]

  tumor-purity
  Estimated purity (tumor content) of tumor sample [1.00]

  p-value
  Default p-value threshold for calling variants [0.99]

  somatic-p-value
  P-value threshold to call a somatic site [0.05]

  strand-filter
  If set to true, removes variants with >90% strand bias

  validation
  If set to true, outputs all compared positions even if non-variant

