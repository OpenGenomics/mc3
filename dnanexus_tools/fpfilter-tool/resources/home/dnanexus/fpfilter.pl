#!/usr/bin/env perl

use warnings;
use strict;

use Getopt::Long;
use IO::File;
use File::Temp qw( tempdir );
use File::Spec;
use Cwd qw( abs_path cwd);

## Define filtering parameters ##

my $min_read_pos = 0.10;
my $max_read_pos = 1 - $min_read_pos;
my $min_var_freq = 0.05;
my $min_var_count = 4;

my $min_strandedness = 0.01;
my $max_strandedness = 1 - $min_strandedness;

my $max_mm_qualsum_diff = 50;
my $max_mapqual_diff = 30;
my $max_readlen_diff = 25;
my $min_var_dist_3 = 0.20;
my $max_var_mm_qualsum = 100;


## Parse arguments ##

my $output_basename;

my $vcf_file;
my $output_file;
my $bam_file;
my $bam_index;
my $sample;
my $bam_readcount_path = 'bam-readcount';
my $samtools_path = 'samtools';
my $ref_fasta;
my $help;


my $opt_result;
my @params = @ARGV;

$opt_result = GetOptions(
    'vcf-file=s' => \$vcf_file,
    'bam-file=s' => \$bam_file,
    'bam-index=s' => \$bam_index,
    'sample=s' => \$sample,
    'bam-readcount=s' => \$bam_readcount_path,
    'bam-readcount=s' => \$samtools_path,
    'reference=s' => \$ref_fasta,
    'output=s'   => \$output_file,
    'min-read-pos=f' => \$min_read_pos,
    'min-var-freq=f' => \$min_var_freq,
    'min-var-count=f' => \$min_var_count,
    'min-strandedness=f' => \$min_strandedness,
    'max-mm-qualsum-diff=f' => \$max_mm_qualsum_diff,
    'max-mapqual-diff=f' => \$max_mapqual_diff,
    'max-readlen-diff=f' => \$max_readlen_diff,
    'min-var-dist-3=f' => \$min_var_dist_3,
    'max_var_mm_qualsum=f' => \$max_var_mm_qualsum,
    'help' => \$help,
);

unless($opt_result) {
    die help_text();
}

if($help) {
    print STDOUT help_text();
    exit 0;
}

unless($vcf_file) {
    warn "You must provide a file to be filtered\n";
    die help_text();
}

unless(-s $vcf_file) {
    die "Can not find VCF file: $vcf_file\n";
}

unless($ref_fasta) {
    warn "You must provide a reference fasta for generating readcounts to use for filtering\n";
    die help_text();
}

unless(-s $ref_fasta) {
    die "Can not find valid reference fasta: $ref_fasta\n";
}

unless($bam_file) {
    die "You must provide a BAM file for generating readcounts\n";
    die help_text();
}

unless(-s $bam_file) {
    die "Can not find valid BAM file: $bam_file\n";
}

if($bam_index && !-s $bam_index) {
    die "Can not find valid BAM index file: $bam_index\n";
}

unless($output_file) {
    warn "You must provide an output file name: $output_file\n";
    die help_text();
}
else {
    $output_file = abs_path($output_file); #make sure we have full path as manipulating cwd below
}

unless($sample) {
    warn "You must provide a sample name\n";
    die help_text();
}

my %filters;
$filters{'position'} = [sprintf("PB%0.f",$min_read_pos*100), "Average position on read less than " . $min_read_pos . " or greater than " . $max_read_pos . " fraction of the read length"];
$filters{'strand_bias'} = [sprintf("SB%0.f",$min_strandedness*100), "Reads supporting the variant have less than " . $min_strandedness . " fraction of the reads on one strand, but reference supporting reads are not similarly biased"];
$filters{'min_var_count'} = [ "MVC".$min_var_count, "Less than " . $min_var_count . " high quality reads support the variant"];
$filters{'min_var_freq'} = [ sprintf("MVF%0.f",$min_var_freq*100), "Variant allele frequency is less than " . $min_var_freq];
$filters{'mmqs_diff'} = [ sprintf("MMQSD%d",$max_mm_qualsum_diff), "Difference in average mismatch quality sum between variant and reference supporting reads is greater than " . $max_mm_qualsum_diff];
$filters{'mq_diff'} = [ sprintf("MQD%d",$max_mapqual_diff), "Difference in average mapping quality sum between variant and reference supporting reads is greater than " . $max_mapqual_diff];
$filters{'read_length'} = [ sprintf("RLD%d",$max_readlen_diff), "Difference in average clipped read length between variant and reference supporting reads is greater than " . $max_readlen_diff];
$filters{'dist3'} = [ sprintf("DETP%0.f",$min_var_dist_3*100), "Average distance of the variant base to the effective 3' end is less than " . $min_var_dist_3];
$filters{'var_mmqs'} = [ sprintf("MMQS%d",$max_var_mm_qualsum), "The average mismatch quality sum of reads supporting the variant is greater than " . $max_var_mm_qualsum] if($max_var_mm_qualsum);
$filters{'no_var_readcount'} = [ "NRC", "Unable to grab readcounts for variant allele"];
$filters{'incomplete_readcount'} = [ "IRC", "Unable to grab any sort of readcount for either the reference or the variant allele"];

my $vcf_header;
my @vcf_lines;

my %rc_for_snp; # store info on snp positions and VCF line
my %rc_for_indel; #store info on indel positions and VCF line

my ($workdir, $working_fasta, $working_bam) = setup_workdir($ref_fasta, $bam_file, $bam_index);

my $starting_dir = cwd();

my $input = IO::File->new($vcf_file) or die "Unable to open input file $vcf_file: $!\n";
$vcf_header = parse_vcf_header($input);
add_filters_to_vcf_header($vcf_header, values %filters);
add_process_log_to_header($vcf_header, $vcf_file, @params);

my $header_line = $vcf_header->[-1];
chomp $header_line;
my @header_fields = split "\t", $header_line;

while(my $entry = $input->getline) {
    push @vcf_lines, $entry;
    chomp $entry;

    my %fields;
    @fields{@header_fields} = split("\t", $entry);
    
    my $filter_sample = $fields{$sample};
    unless($filter_sample) {
        die "Unable to find field for $sample\n";
    }
    my @sample_fields = split /:/, $filter_sample;
    unless(@sample_fields) {
        die "Unable to parse field for $sample\n";
    }
    my $index = 0;
    my %format_keys = map { $_ => $sample_fields[$index++] } split /:/, $fields{FORMAT};
    #these are in order ACGT
    my @alleles = ($fields{REF}, split /,/, $fields{ALT});
    my %gt_alleles = map {$_ => 1} grep { $_ > 0 } split /\//, $format_keys{GT};
    my @used_alleles;
    for my $allele_index (keys %gt_alleles) {
        push @used_alleles, $alleles[$allele_index];
    }
    my ($var) = sort @used_alleles; #follow existing convention of fp filter using alphabetical order to choose a single base on triallelic sites
    $var = q{} unless defined $var; #in the case where there is no variant allele, set this to the empty string. Later it will be filtered as NRC or IRC
    $var = uc($var);
    my $ref = uc($fields{REF});
    my $chrom = $fields{'#CHROM'};
    my $pos = $fields{POS};

    if(length($ref) > 1 || length($var) > 1) {
        #it's an indel or mnp
        if(length($ref) == length($var)) {
            die "MNPs unsupported\n";
        }
        elsif(length($ref) > length($var)) {
            #it's a deletion
            $pos += 1;
            ($ref, $var) = ($var, $ref);
            $ref = substr($var, 1, 1);
            $var = "-" . substr($var, 1);
        }
        else {
            #it's an insertion
            substr($var, 0, 1, "+");
        }
        $rc_for_indel{$chrom}{$pos}{$ref}{$var} = \$vcf_lines[-1];
    }
    else {
        #it's a SNP
        $rc_for_snp{$chrom}{$pos}{$ref}{$var} = \$vcf_lines[-1];
    }
}

if(%rc_for_snp) {
    filter_sites_in_hash(\%rc_for_snp, $bam_readcount_path, $working_bam, $working_fasta, $workdir);
}
else {
    print STDERR "No SNP sites identified\n";
}

if(%rc_for_indel) {
    filter_sites_in_hash(\%rc_for_indel, $bam_readcount_path, $working_bam, $working_fasta, $workdir, '-i');
}
else {
    print STDERR "No Indel sites identified\n";
}

## Open the output files ##
my $filtered_vcf = IO::File->new("$output_file","w") or die "Can't open output file $output_file: $!\n";
print $filtered_vcf @$vcf_header;
print $filtered_vcf @vcf_lines;

chdir $starting_dir or die "Unable to go back to starting dir\n";
exit(0);

################################################################################

=head3	read_counts_by_allele

    Retrieve relevant read counts for a certain allele 


=cut

sub read_counts_by_allele {
    (my $line, my $allele) = @_;

    my @lineContents = split(/\t/, $line);
    my $numContents = @lineContents;

    for(my $colCounter = 5; $colCounter < $numContents; $colCounter++) {
        my $this_allele = $lineContents[$colCounter];
        my @alleleContents = split(/\:/, $this_allele);
        if($alleleContents[0] eq $allele) {
            my $numAlleleContents = @alleleContents;

            return("") if($numAlleleContents < 8);

            my $return_string = "";
            my $return_sum = 0;
            for(my $printCounter = 1; $printCounter < $numAlleleContents; $printCounter++) {
                $return_sum += $alleleContents[$printCounter];
                $return_string .= "\t" if($return_string);
                $return_string .= $alleleContents[$printCounter];
            }

            return($return_string);

        }
    }

    return("");
}


sub help_text {
    return <<HELP;
fpfilter - Filtering for Illumina Sequencing

SYNOPSIS
fpfilter [options] [file ...]

OPTIONS
--vcf-file              the input VCF file. Must have a GT field.
--bam-file              the BAM file of the sample you are filtering on. Typically the tumor.
--sample                the sample name of the sample you want to filter on in the VCF file.
--reference             a fasta containing the reference sequence the BAM file was aligned to.
--output                the filename of the output VCF file
--min-read-pos          minimum average relative distance from start/end of read 
--min-var-freq          minimum variant allele frequency
--min-var-count         minimum number of variant-supporting reads
--min-strandedness      minimum representation of variant allele on each strand
--max-mm-qualsum-diff   maximum difference of mismatch quality sum between variant and reference reads (paralog filter)
--max_var_mm_qualsum    maximum mismatch quality sum of reference-supporting reads
--max-mapqual-diff      maximum difference of mapping quality between variant and reference reads
--max-readlen-diff      maximum difference of average supporting read length between variant and reference reads (paralog filter)
--min-var-dist-3        minimum average distance to effective 3prime end of read (real end or Q2) for variant-supporting reads
--help                  this message

DESCRIPTION
This program will filter a VCF with a variety of filters as detailed in the VarScan2 paper (http://www.ncbi.nlm.nih.gov/pubmed/22300766). It requires the bam-readcount utility (https://github.com/genome/bam-readcount). 

This filter was calibrated on 100bp PE Illumina reads. It is likely to be overly stringent for longer reads and may be less effective on shorter reads.

AUTHORS
Dan Koboldt     Original code
Dave Larson     Modifications for VCF and exportation.

HELP
}

### methods copied from elsewhere begin here...
sub parse_vcf_header {
    my $input_fh = shift;

    my @header;
    my $header_end = 0;
    while (!$header_end) {
        my $line = $input_fh->getline;
        if ($line =~ m/^##/) {
            push @header, $line;
        } elsif ($line =~ m/^#/) {
            push @header, $line;
            $header_end = 1;
        } else {
            die "Missed the final header line with the sample list? Last line examined: $line Header so far: " . join("\n", @header) . "\n";
        }
    }
    return \@header;
}

sub generate_region_list {
    my ($hash, $region_fh) = @_; #input_fh should be a filehandle to the VCF
    print STDERR "Printing variants to temporary region_list file...\n";
    for my $chr (keys %$hash) {
        for my $pos (sort { $a <=> $b } keys %{$hash->{$chr}}) {
            print $region_fh "$chr\t$pos\t$pos\n";
        }
    }
}

sub _simplify_indel_allele {
    my ($ref, $var) = @_;
    #these could be padded e.g. G, GT for a T insertion or GCC G for a 2bp deletion
    #they could also be complex e.g. GCCCGT, GCGT for a 2bp deletion
    #they could also represent an insertion deletion event e.g. GCCCGT GCGGGGT; these cannot be represented in genome bed. Throw an error or warn.
    #
    #I think the algorithm should be trim end (no updating of coords required)
    #trim beginning and return number of bases trimmed

    my @ref_array = map { uc } split //, $ref;
    my @var_array = map { uc } split //, $var;

    while(@ref_array and @var_array and $ref_array[-1] eq $var_array[-1]) {
        pop @ref_array;
        pop @var_array;
    }

    my $right_shift = 0;
    while(@ref_array and @var_array and $ref_array[0] eq $var_array[0]) {
        shift @ref_array;
        shift @var_array;
        $right_shift++;
    }

    return (join("",@ref_array), join("",@var_array), $right_shift);
}

sub filter_site {
    my ($ref_result, $var_result) = @_;
    #this will return a list of filter names
    my @filter_names;
    if($ref_result && $var_result) {
        ## Parse out the bam-readcounts details for each allele. The fields should be: ##
        #num_reads : avg_mapqual : avg_basequal : avg_semq : reads_plus : reads_minus : avg_clip_read_pos : avg_mmqs : reads_q2 : avg_dist_to_q2 : avgRLclipped : avg_eff_3'_dist
        my ($ref_count, $ref_map_qual, $ref_base_qual, $ref_semq, $ref_plus, $ref_minus, $ref_pos, $ref_subs, $ref_mmqs, $ref_q2_reads, $ref_q2_dist, $ref_avg_rl, $ref_dist_3) = split(/\t/, $ref_result);
        my ($var_count, $var_map_qual, $var_base_qual, $var_semq, $var_plus, $var_minus, $var_pos, $var_subs, $var_mmqs, $var_q2_reads, $var_q2_dist, $var_avg_rl, $var_dist_3) = split(/\t/, $var_result);

        my $ref_strandedness = my $var_strandedness = 0.50;
        $ref_dist_3 = 0.5 if(!$ref_dist_3);

        ## Use conservative defaults if we can't get mismatch quality sums ##
        $ref_mmqs = 50 if(!$ref_mmqs);
        $var_mmqs = 0 if(!$var_mmqs);
        my $mismatch_qualsum_diff = $var_mmqs - $ref_mmqs;

        ## Determine map qual diff ##

        my $mapqual_diff = $ref_map_qual - $var_map_qual;


        ## Determine difference in average supporting read length ##

        my $readlen_diff = $ref_avg_rl - $var_avg_rl;


        ## Determine ref strandedness ##

        if(($ref_plus + $ref_minus) > 0) {
            $ref_strandedness = $ref_plus / ($ref_plus + $ref_minus);
            $ref_strandedness = sprintf("%.2f", $ref_strandedness);
        }

        ## Determine var strandedness ##

        if(($var_plus + $var_minus) > 0) {
            $var_strandedness = $var_plus / ($var_plus + $var_minus);
            $var_strandedness = sprintf("%.2f", $var_strandedness);
        }

        if($var_count && ($var_plus + $var_minus)) {
            ## We must obtain variant read counts to proceed ##

            my $var_freq = $var_count / ($ref_count + $var_count);

            ## FAILURE 1: READ POSITION ##
            if(($var_pos < $min_read_pos) || ($var_pos > $max_read_pos)) {
                #$stats{'num_fail_pos'}++;
                push @filter_names, $filters{'position'}->[0];
            }

            ## FAILURE 2: Variant is strand-specific but reference is NOT strand-specific ##
            if(($var_strandedness < $min_strandedness || $var_strandedness > $max_strandedness) && ($ref_strandedness >= $min_strandedness && $ref_strandedness <= $max_strandedness)) {
                #$stats{'num_fail_strand'}++;
                push @filter_names, $filters{'strand_bias'}->[0];
            }

            ## FAILURE : Variant allele count does not meet minimum ##
            if($var_count < $min_var_count) {
                #$stats{'num_fail_varcount'}++;
                push @filter_names, $filters{'min_var_count'}->[0];
            }

            ## FAILURE : Variant allele frequency does not meet minimum ##
            if($var_freq < $min_var_freq) {
                #$stats{'num_fail_varfreq'}++;
                push @filter_names, $filters{'min_var_freq'}->[0];
            }

            ## FAILURE 3: Paralog filter for sites where variant allele mismatch-quality-sum is significantly higher than reference allele mmqs
            if($mismatch_qualsum_diff> $max_mm_qualsum_diff) {
                #$stats{'num_fail_mmqs'}++;
                push @filter_names, $filters{'mmqs_diff'}->[0];
            }

            ## FAILURE 4: Mapping quality difference exceeds allowable maximum ##
            if($mapqual_diff > $max_mapqual_diff) {
                #$stats{'num_fail_mapqual'}++;
                push @filter_names, $filters{'mq_diff'}->[0];
            }

            ## FAILURE 5: Read length difference exceeds allowable maximum ##
            if($readlen_diff > $max_readlen_diff) {
                #$stats{'num_fail_readlen'}++;
                push @filter_names, $filters{'read_length'}->[0];
            }

            ## FAILURE 5: Read length difference exceeds allowable maximum ##
            if($var_dist_3 < $min_var_dist_3) {
                #$stats{'num_fail_dist3'}++;
                push @filter_names, $filters{'dist3'}->[0];
            }

            if($max_var_mm_qualsum && $var_mmqs > $max_var_mm_qualsum) {
                #$stats{'num_fail_var_mmqs'}++;
                push @filter_names, $filters{'var_mmqs'}->[0];
            }

            ## SUCCESS: Pass Filter ##
            if(@filter_names == 0) {
                #$stats{'num_pass_filter'}++;
                ## Print output, and append strandedness information ##
                @filter_names = ('PASS');
            }

        }
        else {
            push @filter_names, $filters{'no_var_readcount'}->[0];
        }
    }
    else {
        #$stats{'num_no_readcounts'}++;
        #print $fail_fh "$line\tno_readcounts\n";
        push @filter_names, $filters{'incomplete_readcount'}->[0];
    }
    return @filter_names;
}

sub add_filters_to_vcf_header {
    my ($parsed_header, @filter_refs) = @_;
    my $column_header = pop @$parsed_header;
    for my $filter_ref (@filter_refs) {
        my ($filter_name, $filter_description) = @$filter_ref;
        my $filter_line = qq{##FILTER=<ID=$filter_name,Description="$filter_description">\n};
        push @$parsed_header, $filter_line;
    }
    push @$parsed_header, $column_header;
}

sub add_process_log_to_header {
    my ($parsed_header, $input, @params) = @_;
    my $column_header = pop @$parsed_header;
    my $param_string = join(" ", @params);
    push @$parsed_header, qq{##vcfProcessLog=<InputVCF=<$input>, InputVCFSource=<fpfilter>, InputVCFVer=<6.0>, InputVCFParam=<"$param_string"> InputVCFgeneAnno=<.>>\n}, $column_header;
}

sub filter_sites_in_hash {
    my ($hash, $bam_readcount_path, $bam_file, $ref_fasta, $working_dir, $optional_param) = @_;
    #done parsing vcf
    $optional_param ||= '';
    my $list_name = File::Spec->catfile($working_dir, "regions.txt");
    my $list_fh = IO::File->new($list_name,"w") or die "Unable to open file for coordinates\n";
    generate_region_list($hash, $list_fh);
    $list_fh->close();

## run bam-readcount
    my $bam_readcount_cmd = "$bam_readcount_path -f $ref_fasta -l $list_name -w 0 -b 20 $optional_param $bam_file|";
    my $rc_results = IO::File->new($bam_readcount_cmd) or die "Unable to open pipe to bam-readcount cmd: $bam_readcount_cmd\n";
    while(my $rc_line = $rc_results->getline) {
        chomp $rc_line;
        my ($chrom, $position) = split(/\t/, $rc_line);
        if($hash->{$chrom}{$position}) {
            for my $ref (keys %{$hash->{$chrom}{$position}}) {
                for my $var (keys %{$hash->{$chrom}{$position}{$ref}}) {
                    my $ref_result = read_counts_by_allele($rc_line, $ref);
                    my $var_result = read_counts_by_allele($rc_line, $var);
                    my @filters = filter_site($ref_result, $var_result);

                    my $vcf_line_ref = $hash->{$chrom}{$position}{$ref}{$var};
                    my @fields = split "\t", $$vcf_line_ref;
                    if($fields[6] eq '.' || $fields[6] eq 'PASS') {
                        $fields[6] = join(";", @filters);
                    }
                    else {
                        $fields[6] = join(";", $fields[6], @filters) if($filters[0] ne 'PASS');
                    }
                    $$vcf_line_ref = join("\t", @fields);
                }
            }
        }
        else {
            die "Unknown site for rc\n";
        }
    }
    unless($rc_results->close) {
        die "Error running bam-readcount\n";
    }
}

sub setup_workdir {
    my ($reference, $bam_file, $bam_index) = @_;
    $reference = abs_path($reference);
    $bam_file = abs_path($bam_file);
    $bam_index = abs_path($bam_index) if $bam_index;

    my $dir = File::Temp->newdir('fpfilterXXXXX', TMPDIR => 1, CLEANUP => 1, DIR => './') or 
        die "Unable to create working directory\n";

    #symlink in necessary files to run
    my $working_reference =  File::Spec->catfile($dir, "reference.fa");
    symlink $reference, $working_reference;

    my $fa_index = $reference . ".fai";
    unless(-e $fa_index) {
        index_fasta($working_reference);
    }
    else {
        symlink $fa_index, File::Spec->catfile($dir, "reference.fa.fai");
    }

    my $working_bam = File::Spec->catfile($dir, "tumor.bam");
    my $working_bam_index = File::Spec->catfile($dir, "tumor.bam.bai");
    symlink $bam_file, $working_bam;
    if($bam_index) {
        symlink $bam_index, $working_bam_index;
    }
    elsif(-e $bam_file . ".bai") {
        symlink $bam_file . ".bai", $working_bam_index;
    }
    else {
        index_bam($working_bam);
    }
    return ($dir, $working_reference, $working_bam);
}

sub index_fasta {
    my ($fasta) = @_;

    print STDERR "Indexing fasta...\n";
    my @args = ($samtools_path, "faidx", $fasta);
    system(@args) == 0
        or die "Unable to index $fasta: $?\n";
}

sub index_bam {
    my ($bam) = @_;

    print STDERR "Indexing BAM...\n";
    my @args = ($samtools_path, "index", $bam);
    system(@args) == 0
        or die "Unable to index $bam: $?\n";
}
