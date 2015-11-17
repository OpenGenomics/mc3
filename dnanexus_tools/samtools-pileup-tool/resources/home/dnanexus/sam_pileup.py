#!/usr/bin/env python

"""
Creates a pileup file from a bam file and a reference.

usage: %prog [options]
   -p, --input1=p: bam file
   -o, --output1=o: Output pileup
   -O, --outputdir=O: Output pileup directory
   -R, --ref=R: Reference file type
   -n, --ownFile=n: User-supplied fasta reference file
   -b, --bamIndex=b: BAM index file
   -g, --index=g: Path of the indexed reference genome
   -s, --lastCol=s: Print the mapping quality as the last column
   -i, --indels=i: Only output lines containing indels
   -M, --mapqMin=i: Filter reads by min MAPQ
   -B, --nobaq=s: disable BAQ computation
   -c, --consensus=c: Call the consensus sequence using MAQ consensu model
   -T, --theta=T: Theta paramter (error dependency coefficient)
   -N, --hapNum=N: Number of haplotypes in sample
   -r, --fraction=r: Expected fraction of differences between a pair of haplotypes
   -I, --phredProb=I: Phred probability of an indel in sequencing/prep
   -C, --cpus=C: Number of CPUs to use
   -w, --workdir=w: Working directory

"""

import os, shutil, subprocess, sys, tempfile
from multiprocessing import Pool
from functools import partial
#from galaxy import eggs
#import pkg_resources; pkg_resources.require( "bx-python" )
from bx.cookbook import doc_optparse

def stop_err( msg ):
    sys.stderr.write( '%s\n' % msg )
    sys.exit()


def get_bam_seqs(inputBamFile, min_size=1):
	cmd = "samtools idxstats %s" % (inputBamFile)
	process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	stdout, stderr = process.communicate()
	seqs = []
	for line in stdout.split("\n"):
		tmp = line.split("\t")
		if len(tmp) == 4 and int(tmp[2]) >= min_size and tmp[0] not in ['*']:
			seqs.append(tmp[0])
	return seqs

def run_cmd(cmd, tmpDir):
    tmp = tempfile.NamedTemporaryFile( dir=tmpDir ).name
    tmp_stderr = open( tmp, 'wb' )
    print "Running", cmd
    proc = subprocess.Popen( args=cmd, shell=True, cwd=tmpDir, stderr=tmp_stderr.fileno() )
    returncode = proc.wait()
    tmp_stderr.close()
    #did it succeed?
    # get stderr, allowing for case where it's very large
    tmp_stderr = open( tmp, 'rb' )
    stderr = ''
    buffsize = 1048576
    try:
        while True:
            stderr += tmp_stderr.read( buffsize )
            if not stderr or len( stderr ) % buffsize != 0:
                break
    except OverflowError:
        pass
    tmp_stderr.close()
    return (returncode, stderr)

def __main__():
    #Parse Command Line
    options, args = doc_optparse.parse( __doc__ )
    # output version # of tool
    try:
        tmp = tempfile.NamedTemporaryFile().name
        tmp_stdout = open( tmp, 'wb' )
        proc = subprocess.Popen( args='samtools 2>&1', shell=True, stdout=tmp_stdout )
        tmp_stdout.close()
        returncode = proc.wait()
        stdout = None
        for line in open( tmp_stdout.name, 'rb' ):
            if line.lower().find( 'version' ) >= 0:
                stdout = line.strip()
                break
        if stdout:
            sys.stdout.write( 'Samtools %s\n' % stdout )
        else:
            raise Exception
    except:
        sys.stdout.write( 'Could not determine Samtools version\n' )
    #prepare file names
    if options.workdir is None:
        tmpDir = tempfile.mkdtemp()
    else:
        tmpDir = tempfile.mkdtemp(dir=options.workdir)
    tmpf0 = tempfile.NamedTemporaryFile( dir=tmpDir )
    tmpf0_name = tmpf0.name
    print tmpf0_name
    tmpf0.close()
    tmpf0bam_name = '%s.bam' % tmpf0_name
    tmpf0bambai_name = '%s.bam.bai' % tmpf0_name
    tmpf1 = tempfile.NamedTemporaryFile( dir=tmpDir )
    tmpf1_name = tmpf1.name
    tmpf1.close()
    if options.outputdir is not None:
        os.mkdir(options.outputdir)
    #link bam and bam index to working directory (can't move because need to leave original)
    os.symlink( os.path.abspath(options.input1), tmpf0bam_name )
    os.symlink( os.path.abspath(options.bamIndex), tmpf0bambai_name )
    #get parameters for pileup command
    if options.lastCol == 'yes':
        lastCol = '-s'
    else:
        lastCol = ''
    if options.indels == 'yes':
        indels = '-i'
    else:
        indels = ''
    #opts = '%s %s -M %s' % ( lastCol, indels, options.mapCap )
    opts = ''
    if options.nobaq == 'yes':
        opts += " -B "
    if options.consensus == 'yes':
        opts += ' -c -T %s -N %s -r %s -I %s' % ( options.theta, options.hapNum, options.fraction, options.phredProb )
    if options.mapqMin:
        opts += ' -q %s' % (options.mapqMin)
    #prepare basic pileup command
    cmd = 'samtools mpileup %s %s -f %s %s > %s'
    cmd_list = None
    try:
        # have to nest try-except in try-finally to handle 2.4
        try:
            #index reference if necessary and prepare pileup command
            if options.ref == 'indexed':
                if not os.path.exists( "%s.fai" % options.index ):
                    raise Exception, "Indexed genome %s not present, request it by reporting this error." % options.index
                if options.outputdir is None:
                    cmd = cmd % ( opts, "", options.index, tmpf0bam_name, os.path.abspath(options.output1) )
                else:
                    cmd_list = []
                    for seq in get_bam_seqs(tmpf0bam_name, 0):
                        cmd_list.append( cmd % ( opts, "-r %s" % (seq), options.index, tmpf0bam_name, os.path.join(os.path.abspath(options.outputdir), os.path.basename(seq)) ) )
            elif options.ref == 'history':
                os.symlink( os.path.abspath(options.ownFile), tmpf1_name )
                cmdIndex = 'samtools faidx %s' % ( tmpf1_name )
                print cmdIndex
                tmp = tempfile.NamedTemporaryFile( dir=tmpDir ).name
                tmp_stderr = open( tmp, 'wb' )
                proc = subprocess.Popen( args=cmdIndex, shell=True, cwd=tmpDir, stderr=tmp_stderr.fileno() )
                returncode = proc.wait()
                tmp_stderr.close()
                # get stderr, allowing for case where it's very large
                tmp_stderr = open( tmp, 'rb' )
                stderr = ''
                buffsize = 1048576
                try:
                    while True:
                        stderr += tmp_stderr.read( buffsize )
                        if not stderr or len( stderr ) % buffsize != 0:
                            break
                except OverflowError:
                    pass
                tmp_stderr.close()
                #did index succeed?
                if returncode != 0:
                    raise Exception, 'Error creating index file\n' + stderr
                if options.outputdir is None:
                    cmd = cmd % ( opts, "", tmpf1_name, tmpf0bam_name, os.path.abspath(options.output1) )
                else:
                    cmd_list = []
                    for seq in get_bam_seqs(tmpf0bam_name, 0):
                        cmd_list.append( cmd % ( opts, "-r %s" % (seq), tmpf1_name, tmpf0bam_name, os.path.join(os.path.abspath(options.outputdir), os.path.basename(seq)) ) )
            #perform pileup command
            if cmd_list is None:
                returncode, stderr = run_cmd(cmd, tmpDir)
                if returncode != 0:
                    raise Exception, stderr
            else:
                run_cmd_partial = partial(run_cmd, tmpDir=tmpDir)
                cpus = 1
                if options.cpus is not None:
                    cpus = int(options.cpus)
                p = Pool(cpus)
                values = p.map(run_cmd_partial, cmd_list, 1)
                for returncode, stderr in values:
                    if returncode != 0:
                        raise Exception, stderr
        except Exception, e:
            stop_err( 'Error running Samtools pileup tool\n' + str( e ) )
    finally:
        #clean up temp files
        #if os.path.exists( tmpDir ):
        #    shutil.rmtree( tmpDir )
        pass
    # check that there are results in the output file
    if options.output1 is None or os.path.getsize( os.path.abspath(options.output1) ) > 0:
        sys.stdout.write( 'Converted BAM to pileup' )
    else:
        stop_err( 'The output file is empty. Your input file may have had no matches, or there may be an error with your input file or settings.' )

if __name__ == "__main__" : __main__()
