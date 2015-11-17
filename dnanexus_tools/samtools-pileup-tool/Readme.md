**What it does**

Uses SAMTools_' pileup command to produce a pileup dataset from a provided BAM dataset. It generates only the simple pileup, and support for consensus calling pileup has been discontinued.

.. _SAMTools: http://samtools.sourceforge.net/samtools.shtml

------

**Samtools version**

Samtools v1.2 is used in this applet.

**Types of pileup datasets**

The description of pileup format below is largely based on information that can be found on SAMTools Pileup_ documentation page. The 6-column format is described below.

.. _Pileup: http://samtools.sourceforge.net/pileup.shtml

**Six column pileup**::

    1    2  3  4        5        6
 ---------------------------------
 chrM  412  A  2       .,       II
 chrM  413  G  4     ..t,     IIIH
 chrM  414  C  4     ...a     III2
 chrM  415  C  4     TTTt     III7

where::

  Column Definition
 ------- ----------------------------
       1 Chromosome
       2 Position (1-based)
       3 Reference base at that position
       4 Coverage (# reads aligning over that position)
       5 Bases within reads where (see Galaxy wiki for more info)
       6 Quality values (phred33 scale, see Galaxy wiki for more)
------

**Citation**

For the underlying tool, please cite `Li H, Handsaker B, Wysoker A, Fennell T, Ruan J, Homer N, Marth G, Abecasis G, Durbin R; 1000 Genome Project Data Processing Subgroup. The Sequence Alignment/Map format and SAMtools. Bioinformatics. 2009 Aug 15;25(16):2078-9. &lt;http://www.ncbi.nlm.nih.gov/pubmed/19505943&gt;`_
