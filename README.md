#     	mc3
# 
		The TCGA PanCancer Atlas MC3 set is a re-calling of uniform files to remove batch effects and
		enable pancancer analysis.

			Citation: "Scalable Open Science Approach for Mutation Calling of Tumor Exomes Using Multiple
			Genomic Pipelines". Ellrott K, Bailey MH, Saksena G, Covington KR, Kandoth C, Stewart C, Hess
			J, Ma S, Chiotti KE, McLellan M, Sofia HJ, Hutter C, Getz G, Wheeler D, Ding	L; MC3 Working
			Group; Cancer Genome Atlas Research Network. Cell Syst. 2018 Mar 28;6(3):271-281.e7. doi:
			10.1016/j.cels.2018.03.002. PubMed PMID: 29596782.
			(http://www.cell.com/cell-systems/fulltext/S2405-4712(18)30096-6)

###############################################################
	A START-UP GUIDE TO PREPARE FOR USE OF THE MC3 PIPELINE:
###############################################################

###############################################################

	IMPORTANT NOTE: Access to GDC Data Portal controlled-access data is required to obtain many of the
	reference and other input files. Use the "Instructions for Data Download" section toward the bottom of
	the page located at https://gdc.cancer.gov/about-data/publications/mc3-2017. Access to Synapse project
	syn3241088 is also required to obtain the remainder of the required files.
	
	Installation of 'docker' and 'cwltool' is required to run this pipeline.
	
	The following text provides detailed instructions on proper placement of the pipeline files utilized
	in the Ellrott, et al. publication. Customization of the pipeline through substitution of any files
	is possible, given the new files are in the same format as the files being replaced.

###############################################################

		1) Create the MC3 pipeline directory tree using the following command (the name of the primary directory
		is not important, so feel free to replace 'my_mc3' with another name):

				`mkdir my_mc3 my_mc3/ref my_mc3/ref/markfiles my_mc3/ref/markfiles/mark_samples \
				 my_mc3/ref/markfiles/mark_variants my_mc3/ref/oxog_filter`

		2) From within the primary directory ('my_mc3' in this case), clone the OpenGenomics/mc3 pipeline from GitHub: 
		
				`git clone https://github.com/OpenGenomics/mc3.git`

		3) From https://www.synapse.org/#!Synapse:syn3241088/files/, download the following files and place them in
		the 'ref' subdirectory:
			1000G_phase1.indels.hg19.sites.vcf
			b37_cosmic_v54_120711.vcf
			dbsnp_132_b37.leftAligned.vcf.gz
			centromere_hg19.bed
			gaf_20111020+broad_wex_1.1_hg19.bed
			Homo_sapiens_assembly19.fasta.gz
			Mills_and_1000G_gold_standard.indels.hg19.sites.vcf

			4) Navigate into the 'ref' directory and generate the appropriate index, dictionary, and decompressed
			files as detailed below. You may produce the necessary files from the command line if you have samtools, 
			picard, gzip, igvtools, and tabix installed; otherwise use the appropriate CWL tool available in the
			'utils' directory of the MC3 pipeline (i.e., ./my_mc3/mc3/utils/). In general, the steps to process each
			file are to:
			
				a) Make a copy of the template file corresponding to the desired CWL tool. This step ensures the original file 
				remains intact while the copy is edited.

						`cp <tool>.template <tool>.json`

				b) Using a text editor such as 'vim' or 'emac', edit the new JSON file following the directions provided within 
				the document.

				c) Run the CWL tool.
						`cwltool <tool>.cwl <tool>.json`

			5) Process the 'ref' files using the appropriate cwltool following Steps 4a, 4b, and 4c:
				
				a) Use </path/to>/utils/idx.cwl and </path/to>/utils/idx.json with '1000G_phase1.indels.hg19.sites.vcf' and 
				'Mills_and_1000G_gold_standard.indels.hg19.sites.vcf' to generate:
							1000G_phase1.indels.hg19.sites.vcf.idx
							Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.idx

					 	- `cp idx.template idx.json`
					 	-  Edit idx.json by replacing '</full/file/path' with the path to the 1000G_phase1.indels.hg19.sites.vcf
					 	- `cwltool idx.cwl idx.json`
					 	-  Repeat last three steps using Mills_and_1000G_gold_standard.indels.hg19.sites.vcf


						Example of completed JSON:
					_________________________________________________________________________________________
					|		{									|	
					|		    "to_index": {							|
					|		        "class" : "File",						|
					|		        "path" : "/my/path/to/1000G_phase1.indels.hg19.sites.vcf"	|
					|		    }									|
					|		}									|
					|_______________________________________________________________________________________|
				

				b) Use </path/to>/utils/gzip.cwl and </path/to>/utils/gzip.template to decompress
				'Homo_sapiens_assembly19.fasta.gz', 'dbsnp_132_b37.leftAligned.vcf.gz' and 'b37_cosmic_v54_120711.vcf.gz'
				in similar fashion as Step 5a to generate: 

							Homo_sapiens_assembly19.fasta 
							dbsnp_132_b37.leftAligned.vcf
							b37_cosmic_v54_120711.vcf

				c) Use </path/to>/utils/fai.cwl and </path/to>/utils/fai.template with 'Homo_sapiens_assembly19.fasta', 
				to generate: 

							Homo_sapiens_assembly19.fasta.fai

				d) Use </path/to>/utils/dict.cwl and </path/to>/utils/dict.template with 'Homo_sapiens_assembly19.fasta', 
				to generate: 

							Homo_sapiens_assembly19.fasta.dict
							
				e)  Use </path/to>/utils/bgzip.cwl and </path/to>/utils/bgzip.template with 'Homo_sapiens_assembly19.fasta', 																																					
				'Homo_sapiens_assembly19.fasta.dict','dbsnp_132_b37.leftAligned.vcf', and 'b37_cosmic_v54_120711.vcf' to 
				generate the following BGZIP'd files required by samtools and tabix:

							Homo_sapiens_assembly19.fasta.gz (This will replace the original downloaded version of the file)
							Homo_sapiens_assembly19.fasta.dict.gz
							dbsnp_132_b37.leftAligned.vcf.gz
							b37_cosmic_v54_120711.vcf.gz

				f) Use </path/to>/utils/tabix.cwl and </path/to>/utils/tabix.template with 'b37_cosmic_v54_120711.vcf.gz' and
				'dbsnp_132_b37.leftAligned.vcf.gz' to generate:

							dbsnp_132_b37.leftAligned.vcf.gz.tbi
							b37_cosmic_v54_120711.vcf.gz.tbi

				g) Use </path/to>/utils/gzi.cwl and </path/to>/utils/gzi.template with 'Homo_sapiens_assembly19.fasta.gz', to 
				generate: 

							Homo_sapiens_assembly19.fasta.gz.gzi
							Homo_sapiens_assembly19.fasta.gz.fai


		6) From the 'ref' directory, retrieve the 'vep_supporting_files.tar.gz' tarball from the GDC Data Portal:

					- `wget https://api.gdc.cancer.gov/data/008517e9-0853-4e1e-aaf6-66a50bb8cf61`
					- `tar xzf 008517e9-0853-4e1e-aaf6-66a50bb8cf61`
					- `rm 008517e9-0853-4e1e-aaf6-66a50bb8cf61`

		Following the `tar` decompression step, a 'home' directory will appear. Move down this directory tree until you get to 
		the 'vep' directory, then move 'vep' up into the 'ref' directory:

					- `mv ./vep/ </path/to>/ref/` 

		Navigate back to 'ref' and delete the new 'home' directory:

					- `rm -rf ./home/`
		
		7) Download the files detailed in the 'manifest' file located in the 'mc3' directory created in Step 2. To complete this step, 
		you must have the following items in place:
		
			a) The 'gdc-client' data transfer tool installed on your system. See https://gdc.cancer.gov/about-data/publications/mc3-2017 for
			links to download and for installation instructions.

			b) A GDC allocated token allowing for download of protected data with 'gdc-client'. Retrieve this by logging into the GDC Data
			Portal at https://portal.gdc.cancer.gov/, click on your user name in the upper right corner of the screen, and then click 'Download
			Token' from the dropdown box.

		Use the following commands to download the files to 'ref':
		
					- `gdc-client download -t </path/to/gdc_token> -m </path/to>/mc3/manifest`
					- `mv *gz ../mv */*txt */*bed */*gz */*tar */*tion .`
				
		At this point, you may delete the newly downloaded directories, if you would like.

		8) From 'ref', populate the 'markfiles' subdirectories with some of the files downloaded in Step 7:
		
					- `gunzip pancan.merged.v0.2* strandBias.filter_v2.txt.gz`
					- `mv contestkeys.txt mark_bitgt.txt mark_nonexonic.txt pancan.merged.v0.2.exac_pon_tagged.txt \
					pancan.merged.v0.2.pfiltered.broad_pon_tagged_v2.txt pcadontusekeys.txt strandBias.filter_v2.txt \
					./markfiles/mark_samples`
					- `mv ndp.mark.txt nonpreferredpair_maf_keys.txt oxog.annotation wga_maf_keys.txt ./markfiles/mark_variants`
					- `mv ref_data_for_oxog_all_permissions.tar.gz ref_data_for_oxog.tar ./oxog_filter`

		9) Use </path/to>/utils/idx.cwl and </path/to>/utils/idx.json with 'gencode.v19.basic.exome.bed to generate:
		
						gencode.v19.basic.exome.bed.idx
			
		10) At this point, all files required to run the pipeline should be in place. Review 'mc3_refdocs_tree.txt' located in the 'mc3'
		directory (i.e., ./my_mc3/mc3/refdocs_tree.txt) confirm proper file placement.

		11) Refer to './my_mc3/mc3/tutorial.txt' for instructions on execution of the pipeline.
