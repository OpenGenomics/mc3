#!/bin/bash

set -e -x -o pipefail

dx-download-all-inputs --parallel

# Determine output name if not provided
if [ -z "$output" ]; then
    output="${tumorInputBamFile_prefix}.pindel"
    echo "output name was determined to be $output"
fi

# Prepare bam input argument
if [ -z "$normalInputBamFile" ]; then
    sampleArgs="-b $tumorInputBamFile_path -t $sampleTag -bi $tumorInputBaiFile_path"
    if [ -n "$tumorInsertSize" ]; then
        sampleArg="${sampleArg} -s tumorInsertSize"
    fi
else
    sampleArgs="-b $normalInputBamFile_path -b $tumorInputBamFile_path -t NORMAL -t TUMOR -bi $normalInputBaiFile_path -bi $tumorInputBaiFile_path"
    if [ -n "$tumorInsertSize" && -n "normalInsertSize" ]; then
        sampleArgs="${sampleArgs} -s normalInsertSize -s tumorInsertSize"
    fi
fi

# Prepare output argument
outputArgs="-o1 output_raw.txt -o2 output.vcf"
if [ -n "$normalInputBamFile" ]; then
    outputArgs="${outputArgs} -o3 output.somatic.vcf"
fi

# Prepare reporting argument
reportArgs=""
if [[ $reportInversions == "true" ]]; then
    reportArgs="${reportArgs} --report_inversions"
fi

if [[ $reportDuplications == "true" ]]; then
    reportArgs="${reportArgs} --report_duplications"
fi

if [[ $reportLongInsertions == "true" ]]; then
    reportArgs="${reportArgs} --report_long_insertions"
fi

if [[ $reportBreakpoints == "true" ]]; then
    reportArgs="${reportArgs} --report_breakpoints"
fi

if [[ $report_only_close_mapped_reads == "true" ]]; then
    reportArgs="${reportArgs} -S"
fi

if [[ $report_interchromosomal_events == "true" ]]; then
    reportArgs="${reportArgs} --report_interchromosomal_events"
fi

python ~/pindel.py \
-r $inputReferenceFile_path \
-R $referenceName \
$sampleArgs \
$outputArgs \
--number_of_procs `nproc` \
--window_size $window_size \
$reportArgs \
$advanced_opts

ls
mkdir -p out/outputRawFile
mkdir -p out/outputVcf

mv "output_raw.txt" "out/outputRawFile/${output}.raw.txt"
mv "output.vcf" "out/outputVcf/${output}.vcf"

if [ -f output.somatic.vcf ]; then
    mkdir -p out/outputSomaticVcf/
    mv "output.somatic.vcf" "out/outputSomaticVcf/${output}.somatic.vcf"
fi

dx-upload-all-outputs
