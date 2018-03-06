import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
#@Author: John Gooch
#@Created: 20120508
#@Updated:
#@Version:
#@Name:



def printHelp():
	print "Syntax zipfile.py -z <path to zip file> -s <path/to/source/files>  -m<file name mask of target files> "
	return 0;

	
def initCLI():
	parser = argparse.ArgumentParser(description='File Zip utility')
	parser.add_argument('-z', action="store", dest="zip_file_path", required=True, help='Path to the zip file including the desited file name.' )
	parser.add_argument('-s', action="store", dest="source_file_path", required=True, help='path to the files to include in the zip file.,')
	parser.add_argument('-m', action="store", dest="source_file_mask", required=True, help='File name mask for files to include in the zip file.')
	parser.add_argument('-b', action="store_true", dest="debug", default=False, help='Turn on debugging messages')
	parser.add_argument('-r', action="store_true", dest="remove", default=False, help='Remove files after adding them to zip.')

	parser.add_argument('-f', action="store_true", dest="flat", default=False, help='Flatten the filesystem, so do not store the path in the filename. Turn on debugging messages')

	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

def listFiles(conf):
	print "Source file path %s " % ( conf.source_file_path )
	targetFiles = []

	if ( os.path.exists( conf.source_file_path ) == False ):
		print "Source file path %s does not exist. Please check path and permissions." % ( conf.source_file_path  )
		return None
	#change to the source file dir
	#os.chdir(conf.source_file_path )
	#get list of files that match the path
	files = os.listdir(conf.source_file_path ) 
	print "files contains %s" % ( files )
	for file in files:
		filename = os.path.basename(file)
		if ( re.search( conf.source_file_mask , filename) ):
			print "filename %s matches file mask %s" % ( filename, conf.source_file_mask )
			targetFiles.append(  os.path.join( conf.source_file_path, file  ) )		
			print "Added %s to file list." % ( os.path.join( conf.source_file_path, file  ) )
	
	if ( targetFiles == None ):
		print "No files found."
	elif ( len(targetFiles) == 0 ):
		targetFiles = None
	else:
		print "%d file found matching %s in directory %s." % ( len(targetFiles), conf.source_file_mask, conf.source_file_path )

	return targetFiles
	

def zipFiles(conf, fileList):
	zip_file_dir = os.path.dirname( conf.zip_file_path )
	if ( os.path.exists( zip_file_dir ) == False ):
		print "Cannot access the zip file destination directory at %s. Please check the path and permissions." % ( zip_file_dir )
		return 1;
	
	print "Creating zip file %s" % ( conf.zip_file_path )
	zf = zipfile.ZipFile( conf.zip_file_path, 'w' )
	try:
		for file in fileList:
			print "Adding file %s to zip file %s" % ( file , conf.zip_file_path   )
			if ( conf.flat == True):
				filename = os.path.basename(file)
				zf.write(file, filename )
				print "Added file %s to zip file %s" % ( filename , conf.zip_file_path   )
				if ( conf.remove == True ):
					os.remove(file)
			else:
				zf.write(file )				
				print "Added file %s to zip file %s" % ( file , conf.zip_file_path   )
				if ( conf.remove == True ):
					os.remove(file)
	except Exception, error:
		print "Failed to write file %s to zip file %s" % ( file , conf.zip_file_path   )
		return 1
	finally:
		print "Closing zip file %s" % ( conf.zip_file_path ) 
		zf.close()
	return 0
	
def main():
	params = initCLI()
	if ( params is None ):
		print "Exiting..."
		return 1
	#get the list of files to zip
	files = listFiles(params)
	if ( files == None ):
		print "Exiting..."
		return 1	
	#zip the files
	if ( zipFiles(params,  files) != 0 ):
		print "Exiting..."
		return 1
	print "Successfully created zip file %s. Done.\n" % ( params.zip_file_path ) 
	return 0;


if __name__ == "__main__":
	sys.exit(main());