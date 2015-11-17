**Reference**

  http://gmt.genome.wustl.edu/somatic-sniper/current/

-----

**What it does**

The purpose of this program is to identify single nucleotide positions that are different between tumor and normal
(or, in theory, any two bam files). It takes a tumor bam and a normal bam and compares the two to determine the
differences. It outputs a file in a format very similar to Samtools consensus format. It uses the genotype likelihood
model of MAQ (as implemented in Samtools) and then calculates the probability that the tumor and normal genotypes are
different. This probability is reported as a somatic score. The somatic score is the Phred-scaled probability (between 0 to 255)
that the Tumor and Normal genotypes are not different where 0 means there is no probability that the genotypes are different and
255 means there is a probability of 1 – 10(255/-10) that the genotypes are different between tumor and normal. This is consistent
with how the SAM format reports such probabilities.

Bam files must contain LB tag in @RG line.
Picard tools can be used to add lines to BAM headers.

-----

**Input**

Tumor Sample:

    bam tumor sample

Normal Sample:

    bam normal sample

Reference Genome:

    Fasta file of ref gnome

-----

**Options**

::

    -q INT    filtering reads with mapping quality less than INT [0]
    -Q INT    filtering somatic snv output with somatic quality less than  INT [15]
    -L FLAG   do not report LOH variants as determined by genotypes
    -G FLAG   do not report Gain of Reference variants as determined by genotypes
    -p FLAG   disable priors in the somatic calculation. Increases sensitivity for solid tumors
    -J FLAG   Use prior probabilities accounting for the somatic mutation rate
    -s FLOAT  prior probability of a somatic mutation (implies -J) [0.010000]
    -T FLOAT  theta in maq consensus calling model (for -c/-g) [0.850000]
    -N INT    number of haplotypes in the sample (for -c/-g) [2]
    -r FLOAT  prior of a difference between two haplotypes (for -c/-g) [0.001000]
    -n STRING normal sample id (for VCF header) [NORMAL]
    -t STRING tumor sample id (for VCF header) [TUMOR]


-----

**Output**

    Output file will be in VCF format.