#!/usr/bin/env python
#module which defines "low" level methods for accessing CGHub WSI, both internal and external interfaces

import os
import shutil
import sys
import urllib2
import urllib
import re
import lxml.etree as xparser
import time
from functools import wraps
import pprint

UUID_FORMAT='([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})'
#CGHUB_ANALYSIS_ATTR_URL='https://cghub.ucsc.edu/cghub/metadata/analysisAttributes'
#CGHUB_ANALYSIS_OBJECT_URL='https://cghub.ucsc.edu/cghub/metadata/analysisObject'
#CGHUB_ANALYSIS_ATTR_URL='https://stage.cghub.ucsc.edu/cghub/metadata/analysisFull'
CGHUB_ANALYSIS_ATTR_URL='https://cghub.ucsc.edu/cghub/metadata/analysisFull'
CGHUB_ANALYSIS_OBJECT_URL='https://cghub.ucsc.edu/cghub/metadata/analysisDetail'
CGHUB_ROOT_TAGS=['ANALYSIS','RUN','EXPERIMENT']


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

@retry(urllib2.URLError, tries=100, delay=2, backoff=2)
def open_url(url):
	return urllib2.urlopen(url)

#same above w/o retry
def open_url_noretry(url):
	return urllib2.urlopen(url)
	
#this is a generic low level urllib caller that can be used for the following internal WSI update actions:
#update
#update_state
#update_sample
#redact_sample
#unredact_sample
def update_metadata(id_name,id_value,action,admin_key_file,wsi_url,additional_data,commit):
	try:
		f=open(admin_key_file,"r")
		admin_key=f.read()
		f.close()
	except IOError as err:
		sys.stderr.write("exception reading admin key file: %s" % err)
		sys.exit(-1)
	
	post_sequence={'action':action,'token':admin_key,id_name:id_value}
	for data in additional_data:
		fields=data.split("=")
		#if the reason has "="s in it we need to rejoin
		post_sequence[fields[0]]="=".join(fields[1:])
	
	request=urllib2.Request(url=wsi_url,data=urllib.urlencode(post_sequence))
	sys.stderr.write("request object fields: %s \n" % "\t".join(map(lambda x: "=".join([x[0],x[1]]), post_sequence.iteritems())))
	resp=None
	if commit:
		sys.stderr.write("committing\n")
		resp=open_url_noretry(request)
	return resp


def token_management(action,admin_key_file,wsi_url,targettoken,commit):
	try:
		f=open(admin_key_file,"r")
		admin_key=f.read()
		f.close()
	except IOError as err:
		sys.stderr.write("exception reading admin key file: %s" % err)
		sys.exit(-1)
	
	post_sequence={'action':action,'token':admin_key}
	if targettoken:
		post_sequence['targettoken']=targettoken
	get_sequence="&".join(map(lambda x: "=".join([x[0],x[1]]),post_sequence.iteritems()))
	
	#request=urllib2.Request(url=wsi_url,data=urllib.urlencode(post_sequence))
	request="%s?%s" % (wsi_url,get_sequence)
	#sys.stderr.write("request object fields: %s \n" % "\t".join(map(lambda x: "=".join([x[0],x[1]]), post_sequence.iteritems())))
	sys.stderr.write("request string: %s\n" % request)
	resp=None
	if commit:
		sys.stderr.write("committing\n")
		resp=open_url_noretry(request)
	return resp


def read_response(resp):
	lines=[]
	for line in resp:
		line=line.rstrip()
		lines.append(line)
	return lines	

def retrieve_analysis_attributes_for_uuid(uuid):
	#check for the 8-4-4-4-12 alphanumeric format of the uuid
	if re.compile(UUID_FORMAT,re.IGNORECASE).search(uuid) == None:
		return "CGHWSI_ERROR: bad uuid"
	readurl="%s?analysis_id=%s" % (CGHUB_ANALYSIS_ATTR_URL,uuid)
	data = open_url(readurl)
	data=data.read()
	return data	


def split_analysis_attributes(xml,uuid):
	if 'CGHWSI_ERROR' in xml:
		return xml
	if not os.path.exists( uuid ):
		os.mkdir("./%s" % uuid)
	root=xparser.fromstring(xml)
	for tag in CGHUB_ROOT_TAGS:
		fout=open("./%s/%s.xml" % (uuid,tag.lower()),"w")
		fout.write('<?xml version="1.0" encoding="UTF-8"?>\n')
		ctree=root.find("./Result/%s_xml/%s_SET" % (tag.lower(),tag))
		if ctree == None:
			return "CGHWSI_ERROR: missing %s" % tag
		newtree=xparser.ElementTree(ctree)
		newtree.write(fout)
	
def retrieve_analysis_uuids_by_state(state):
	readurl="%s?state=%s" % (CGHUB_ANALYSIS_OBJECT_URL,state)
	data=urllib2.urlopen(readurl)
	#data=data.read()
	uuids=[]
	p=re.compile(UUID_FORMAT,re.IGNORECASE)
	for line in data:
		line.rstrip()
		if '<analysis_id>' in line:
			m=p.search(line)
			if m != None:
				uuids.append(m.group(1))
	return uuids

def test():
	sys.stdout.write("test mode, duh\n")
	shutil.rmtree("./9c0210d1-f5df-46dc-ab59-b0993469a355",True)
	data=retrieve_analysis_attributes_for_uuid('9c0210d1-f5df-46dc-ab59-b0993469a355')
	error=split_analysis_attributes(data,'9c0210d1-f5df-46dc-ab59-b0993469a355')
	if error != None:
		sys.stderr.write(error+"\n");

def main():
	test()


if __name__ == '__main__':
	main()
