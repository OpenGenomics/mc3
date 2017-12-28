#!/usr/bin/env python

from optparse import OptionParser  
import gzip, yaml, re, sys, os, shutil, subprocess

# based on vcfToMageTab.py

def get_read_fileHandler(aFilename):
    '''
    ' Open aFilename for reading and return
    ' the file handler.  The file can be
    ' gzipped or not.
    '''
    if aFilename.endswith('.gz'):
        return gzip.open(aFilename,'rb')
    else:
        return open(aFilename,'r')


def get_write_fileHandler(aFilename):
    '''
    ' Open aFilename for writing and return
    ' the file handler.  The file can be
    ' gzipped or not.
    '''
    if aFilename.endswith('.gz'):
        return gzip.open(aFilename,'wb')
    else:
        return open(aFilename,'w')

class idfParams(object):
    """Parse input yaml file to IDF parameter object"""
    def __init__(self, inputYaml):
        with open(inputYaml) as handle:
            self.params = yaml.load(handle.read())
        handle.close()

        # do we have all inputs?
        expected = ['expDesign', 'expDesignOntology', 'expDesignFactorName', 'expDesignFactorType', 'investigationTitle',
          'personLastName', 'personFirstName', 'personMidInitial', 'personEmail', 'personAddress', 
          'personAffiliation', 'personRole', 'pubMedId', 'pubAuthors', 'pubTitle', 'pubStatus', 
          'expDescription', 'protocolNames', 'protocolTypes', 'protocolDescriptions', 
          'protocolOntologies', 'protocolParameters', 'ontologyName', 'ontologyFile', 
          'ontologyVersion']
        found = set(self.params.keys())
        if set(expected).difference(found):
            for mis in set(expected).difference(found):
                sys.stderr.write("ERROR, missing %s in yaml inputs\n" % mis)
            sys.exit(1)

        if set(found).difference(expected):
            for toomuch in set(found).difference(expected):
                sys.stderr.write("WARNING, %s in yaml inputs does not match to an input variable, ignoring...\n" % toomuch)
        self.name = os.path.basename(inputYaml)[:-4]	# remove yml extension

def sanity_check(idfObjects):
    if len(idfObjects) < 1:
        print >>sys.stderr, "ERROR, no yaml format input files found in yamlDir, exiting..."
        sys.exit(1)
    names = set()
    for obj in idfObjects:
        if obj.params["protocolNames"] in names:
            print >>sys.stderr, "ERROR: duplicate name %s in yaml input, please correct" % obj.params["protocolNames"]
            sys.exit(1)
        names.add(obj.params["protocolNames"])

def getProtocolRef(idfObjects, softwareName):
    """Returns protocol reference and center ID for use in SDRF"""
    for obj in idfObjects:
        if obj.name == softwareName:
            return obj.params["protocolNames"], obj.params["protocolNames"].split(":")[0]
    return False

def getGenome(line):
            if ("GRCh37-lite" in line):
                genome = "GRCh37-lite"
            elif ("GRCh37" in line):
                genome = "GRCh37"
            elif ("Homo_sapiens_assembly19" in line):
                genome = "hg19"
            elif ("hg19" in line):
                genome = "hg19"
            elif ("hg18" in line):
                genome = "hg18"
            elif ("NCBI36" in line):
                genome = "36.1"
            elif ("NCBI37" in line):
                genome = "37"
            else:
                genome = None
            return genome

class SDRF(object):
    def __init__(self, fromSample):
        if fromSample:
            self.sampleSDRF(fromSample)
        else:
            self.uuid = "Extract Name"
    	    self.barcode = "Comment [TCGA Barcode]"
            self.isTumor = "Comment [is tumor]"
            self.material = "Material Type"
    	    self.annot = "Annotation REF"
    	    self.genome = "Comment [TCGA Genome Reference]"
            self.protocol1 = "Protocol REF"
            self.vendor =  "Parameter Value [Vendor]"
            self.catalogName = "Parameter Value [Catalog Name]"
            self.catalogNr = "Parameter Value [Catalog Number]"
            self.protocol2 = "Protocol REF"
            self.bamfile = "Comment [Derived Data File REF]"
            self.cghubId = "Comment [TCGA CGHub ID]"
            self.include1 = "Comment [TCGA Include for Analysis]"
            self.protocol3 = "Protocol REF"
            self.vcf = "Derived Data File"
            self.tcgaSpec = "Comment [TCGA Spec Version]"
            self.include2 =  "Comment [TCGA Include for Analysis]"
            self.datatype = "Comment [TCGA Data Type]"
            self.dataLevel = "Comment [TCGA Data Level]"
            self.archive = "Comment [TCGA Archive Name]"

##SAMPLE=<ID=PRIMARY,Description="Primary Tumor",SampleUUID=f23b3d0d-26a5-4adf-8aec-4994d094465b,SampleTCGABarcode=TCGA-W5-AA33-01A-11D-A417-09,AnalysisUUID=cd5d8895-6b13-450f-993b-bff9943dc0d9,File="9a6ebf433eb4bcb93be593f74ffa1d3b.bam",Platform="Illumina",Source="dbGAP",Accession="dbGaP",softwareName=<varscan>,softwareVer=<2.4.0>,softwareParam=<"min-coverage=8,min-coverage-normal=8,min-coverage-tumor=6,min-var-freq=0.1,min-freq-for-hom=0.75,normal-purity=1.0,tumor-purity=1.0,p-value=0.99,somatic-p-value=0.05">>
    def sampleSDRF(self, line):
        sampleLine = line[len("##SAMPLE=<"):len(line)-1]	# remove outer <>
        params = dict(item.split("=",1) for item in sampleLine.split(","))
        # remove the quotes
        for key in params:
            if (params[key].startswith("\"")):
                value = params[key]
                params[key] = value[1:(len(value)-1)]
        self.uuid = params['SampleUUID']
        self.barcode = params['SampleTCGABarcode']
        self.isTumor = None
        if params['ID'] == 'NORMAL':
            self.isTumor = 'no'
        elif (params['ID'] == 'PRIMARY') or (params['ID'] == 'TUMOR'):
            self.isTumor = 'yes'
        self.material = 'DNA'		# NOTE: hardcoded, must parse from header when adding RNA data
	self.annot = '->'
	self.genome = None	# TBD
        self.protocol1 = '->'
        self.vendor = '->'
        self.catalogName = '->'
        self.catalogNr = '->'
        self.protocol2 = '->'
        self.bamfile = params['File']	
        self.cghubId = params['Source']	# dbGaP
        self.include1 = "yes"
        self.protocol3 = None	# TBD, this is the protocol as listed in the IDF
        self.vcf = None		# TBD
        self.tcgaSpec = None	# TBD
        self.include2 =  "yes"
        self.datatype = "Mutations"
        self.dataLevel = "Level 2"
        self.archive = None	# TBD
        self.software = params['softwareName']	# does not go in SDRF, will need this later
        self.individual = ('-').join(params['SampleTCGABarcode'].split('-')[0:3])

    def addVcfInfo(self, genome, tcgaSpec, archive):
        self.genome = genome
        self.tcgaSpec = tcgaSpec
        self.archive = archive

    def addExternal(self, protocolRef, vcf):
        self.vcf = vcf
        self.protocol3 = protocolRef

    def doPrint(self):
        printList = [self.uuid, self.barcode, self.isTumor, self.material, self.annot, 
            self.genome, self.protocol1, self.vendor, self.catalogName, self.catalogNr, 
            self.protocol2, self.bamfile, self.cghubId, self.include1, self.protocol3, 
            self.vcf, self.tcgaSpec, self.include2, self.datatype, self.dataLevel, 
            self.archive]
        if None in printList:
            print >>sys.stderr, "SDRF output contains illegal None value:\n", printList
            sys.exit(1)
        return "\t".join(printList)

def sdrfFromVcf(vcfFile, archive):
    """Create SDRF objects from VCF input"""

    sdrfList = []
    tcgaSpecVersion = None
    genome = None
    
    # open the file
    # we need to get (at least) two output samples from the VCF header: normal and primary tumor
    vcfFileHandler = get_read_fileHandler(vcfFile)
    for line in vcfFileHandler:
        # strip the carriage return and newline characters
        line = line.rstrip("\r\n")

        # if it is an empty line, then just continue
        if (line.isspace()):
            continue;
        # we need to extract the tcga spec that was used
        elif (line.startswith("##tcgaversion")):
            ##tcgaversion=1.0

            (key, value) = line.split("=")
            tcgaSpecVersion = value
        # we need to extract info from the reference tag in the header
        elif (line.startswith("##reference")):
            genome = getGenome(line)

        # Create one SDRF object for every SAMPLE found in the header
        elif (line.startswith("##SAMPLE")):
            mySDRF = SDRF(line)	# create SDRF object
            mySDRF.addVcfInfo(genome, tcgaSpecVersion, archive)
            sdrfList.append(mySDRF)

        elif (line.startswith("INFO") or line.startswith("FORMAT")):
            break
    
    vcfFileHandler.close()
    return sdrfList


def get_manifest(md5Dir):
    """create MANIFEST.txt file with md5sum on files in input dir. Could also use module hash.md5sum but that has issues with larger files"""
    manifest = open(os.path.join(md5Dir, 'MANIFEST.txt'),'w')

    onlyfiles = [ f for f in os.listdir(md5Dir) if os.path.isfile(os.path.join(md5Dir,f)) ]
    for file in onlyfiles:
        if file != 'MANIFEST.txt':
            md5sum = subprocess.check_output(['md5sum', os.path.join(md5Dir, file)])
            manifest.write("%s  %s\n" % (md5sum.split(' ')[0], file))  # only use filename, not path
    manifest.close()
    return True

def make_archive(inputDir):
    """Create tar.gz file from inputDir and md5sum on that tar file"""
    # FIXME: The md5sum adds the inputDir name to the output. This does not seem to affect validation, but
    # might still be illegal
    tarfile = '.'.join([inputDir, 'tar.gz'])
    # This will die on the command line when it fails. That's a good thing - it will alert the user.
    subprocess.check_call(['tar', '-zcvf', tarfile, inputDir])
    # create md5sum of archive
    md5File = open(tarfile + '.md5', 'w')
    subprocess.check_call(['md5sum', tarfile], stdout = md5File)
    md5File.close()
    return True


def noneClean(v):
    if v is None:
        return ""
    return v

def oneIDF(idfObjectList, param):
    """Return output based on first input yaml parameter objects"""
    outString = "\t" +  str(noneClean(idfObjectList[0].params[param]))
    return outString

def concatIDF(idfObjectList, param):
    """Create tab separated strings from input yaml parameter objects"""
    outString = ""
    for obj in idfObjectList:
        outString += "\t" + str(noneClean(obj.params[param]))
    return outString

def createIDFfile(idfFilename, sdrfFilename, idfObjects):
    """Create IDF format output. This looks very similar to the expected yaml config input, but contains the sdrf filename and a title"""
    idfFileHandler = get_write_fileHandler(idfFilename)

    # output the experimental design lines
    idfFileHandler.write("".join(["Investigation Title", oneIDF(idfObjects, "investigationTitle")]) + "\n")
    idfFileHandler.write("".join(["Experimental Design", oneIDF(idfObjects, "expDesign")]) + "\n")
    idfFileHandler.write("".join(["Experimental Design Term Source REF", oneIDF(idfObjects, "expDesignOntology")]) + "\n")
    idfFileHandler.write("".join(["Experimental Factor Name", oneIDF(idfObjects, "expDesignFactorName")]) + "\n")
    idfFileHandler.write("".join(["Experimental Factor Type", oneIDF(idfObjects, "expDesignFactorType")]) + "\n")
    idfFileHandler.write("\n")

    # output the person lines
    idfFileHandler.write("".join(["Person Last Name", concatIDF(idfObjects, "personLastName")]) + "\n")
    idfFileHandler.write("".join(["Person First Name", concatIDF(idfObjects, "personFirstName")]) + "\n")
    idfFileHandler.write("".join(["Person Mid Initials", concatIDF(idfObjects, "personMidInitial")]) + "\n")
    idfFileHandler.write("".join(["Person Email", concatIDF(idfObjects, "personEmail")]) + "\n")
    idfFileHandler.write("".join(["Person Address", concatIDF(idfObjects, "personAddress")]) + "\n")
    idfFileHandler.write("".join(["Person Affiliation", concatIDF(idfObjects, "personAffiliation")]) + "\n")
    idfFileHandler.write("".join(["Person Roles", concatIDF(idfObjects, "personRole")]) + "\n")
    idfFileHandler.write("\n")

    # output the publication lines
    idfFileHandler.write("".join(["PubMed ID", concatIDF(idfObjects, "pubMedId")]) + "\n")
    idfFileHandler.write("".join(["Publication Author List", concatIDF(idfObjects, "pubAuthors")]) + "\n")
    idfFileHandler.write("".join(["Publication Title", concatIDF(idfObjects, "pubTitle")]) + "\n")
    idfFileHandler.write("".join(["Publication Status", concatIDF(idfObjects, "pubStatus")]) + "\n")
    idfFileHandler.write("".join(["Experiment Description", concatIDF(idfObjects, "expDescription")]) + "\n")
    idfFileHandler.write("\n")

    # output the protocol lines
    idfFileHandler.write("".join(["Protocol Name", concatIDF(idfObjects, "protocolNames")]) + "\n")
    idfFileHandler.write("".join(["Protocol Type", concatIDF(idfObjects, "protocolTypes")]) + "\n")
    idfFileHandler.write("".join(["Protocol Description", concatIDF(idfObjects, "protocolDescriptions")]) + "\n")
    idfFileHandler.write("".join(["Protocol Term Source REF", concatIDF(idfObjects, "protocolOntologies")]) + "\n")
    idfFileHandler.write("".join(["Protocol Parameters", concatIDF(idfObjects, "protocolParameters")]) + "\n")
    idfFileHandler.write("\n")

    # output the sdrf line
    sdrfBasename = os.path.basename(sdrfFilename)
    idfFileHandler.write("\t".join(["SDRF Files", sdrfBasename]) + "\n")
    idfFileHandler.write("\n")

    # output the ontology lines (get field from one input only)
    idfFileHandler.write("".join(["Term Source Name", oneIDF(idfObjects, "ontologyName")]) + "\n")
    idfFileHandler.write("".join(["Term Source File", oneIDF(idfObjects, "ontologyFile")]) + "\n")
    idfFileHandler.write("".join(["Term Source Version", oneIDF(idfObjects, "ontologyVersion")]) + "\n")

    # close the file
    idfFileHandler.close()

def createSDRFfile(sdrfFile, sdrfObjects):
    """Create SDRF format output file from input list of SDRF objects"""

    sdrfFileHandler = get_write_fileHandler(sdrfFile)
    for sdrf in sdrfObjects:
        sdrfFileHandler.write(sdrf.doPrint() + "\n")
    sdrfFileHandler.close()


def createDir(mydir):
    if os.path.exists(mydir):
        print >>sys.stderr, "WARNING, overwriting", mydir
        shutil.rmtree(mydir)
    os.makedirs(mydir)


def main():

    # create the usage statement
    usage = """usage: python %prog <vcf dir> <idf.yaml dir> disease

From an input dir with (subdirs with) VCF files, a dir with .yml format IDF input and a disease code (e.g. BRCA), 
create TCGA formatted Level_2 data and mage-tab archives in a directory named <disease>.

NOTE: The correct IDF protocol for each input VCF is based on its name. This program expects inputs to be named
pindel.vcf, varscan.snp.vcf, etc. It may be better to parse this info from the VCF header.

"""
    cmdLineParser = OptionParser(usage=usage)
    if len(sys.argv) != 4:
        cmdLineParser.print_help()
        sys.exit(1)

    # get the required parameters
    (cmdLineOptions, cmdLineArgs) = cmdLineParser.parse_args()
    inputDir = str(cmdLineArgs[0])
    yamlDir = str(cmdLineArgs[1])
    outDir = str(cmdLineArgs[2])

    # parse the yaml format idf configs
    idfObjects = []
    for item in os.listdir(yamlDir):
        if item.endswith('yml'):
            idfObjects.append(idfParams(os.path.join(yamlDir, item)))
    sanity_check(idfObjects)
    
    #scan input directory for different disease
    # get patient directories in input dir. 
    # FIXME: This assumes all patients have the same (input) disease!
    pdirs = [ os.path.join(inputDir, d) for d in os.listdir(inputDir) if os.path.isdir(os.path.join(inputDir,d)) ]
    for patient in pdirs:
        for vcfFile in os.listdir(patient):
            if vcfFile.endswith('vcf'):
                print vcfFile


    return
    # create output names
    # the outputdirs are of the format <domain>_<disease study>.Multicenter_mutation_calling_MC3.<archive type>.<serial index>.<revision>.<series>
    serial_index = "1"
    revision = "0"
    series = "0"
    version = (".").join([serial_index, revision, series])
    outBase = 'ucsc.edu_' + disease + '.Multicenter_mutation_calling_MC3'
    outMageTab = (".").join([outBase, "mage-tab", version]) 
    outData = (".").join([outBase, "Level_2", version]) 
    idfFilename = outBase + '.idf.txt'
    sdrfFilename = outBase + '.sdrf.txt'

    # overwrite output directories if need be
    createDir(archiveDir)
    mageTabDir = os.path.join(archiveDir, outMageTab)
    createDir(mageTabDir)
    dataDir = os.path.join(archiveDir, outData)
    createDir(dataDir)

    # create the output IDF file
    createIDFfile(os.path.join(mageTabDir, idfFilename), sdrfFilename, idfObjects)

    # parse and copy VCF files while creating SDRF output
    sdrfOutput = []
    # header
    header = SDRF(fromSample=False)
    sdrfOutput.append(header)

    # get patient directories in input dir. 
    # FIXME: This assumes all patients have the same (input) disease!
    pdirs = [ os.path.join(inputDir, d) for d in os.listdir(inputDir) if os.path.isdir(os.path.join(inputDir,d)) ]
    for patient in pdirs:
        for vcfFile in os.listdir(patient):
            if vcfFile.endswith('vcf'):
                sdrfObjectList = sdrfFromVcf(os.path.join(patient, vcfFile), outData)
                if len(sdrfObjectList) == 0:
                    raise Exception("No SDRF Objects in %s" % os.path.join(patient, vcfFile))
                

    	        # copy and rename with center name and patient barcode
                # Note that there are two varscan outputs that have to be kept separate but point to the same IDF entry
                idfName = vcfFile.split(".")[0]	# radia, pindel...
    
                # get the protocol reference and center ID from the idf object
                protocolRef, centerId = getProtocolRef(idfObjects, idfName)
                # then use the center ID to create the output filename
                rename = ('.').join([vcfFile[:-4], centerId, sdrfObjectList[0].individual, 'vcf'])
                shutil.copyfile(os.path.join(patient, vcfFile), os.path.join(dataDir, rename))
    
                # insert protocol REF vcf filename into the SDRF objects
                for obj in sdrfObjectList:
                    obj.addExternal(protocolRef, rename)
    
                # finally, add completed objects to output
                sdrfOutput.extend(sdrfObjectList)

    createSDRFfile(os.path.join(mageTabDir, sdrfFilename), sdrfOutput)


    #FIXME: Must add DESCRIPTION.txt to mageTabDir. This is a free form text that describes the experiments

    # Create MANIFEST files in both input directories
    get_manifest(mageTabDir)
    get_manifest(dataDir)

    # Make archives

    make_archive(mageTabDir)
    make_archive(dataDir)

    # FIXME: for submission the untarred mageTabDir and dataDir should be removed. However, for running the TCGA
    # client side validator it's easier to keep them around

main()
sys.exit(0)
