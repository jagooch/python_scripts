import argparse
import gzip
import logging
import os
import sys
import traceback
from zipfile import ZipFile

import asys

global logger
logging.basicConfig()
logger = logging.getLogger('fts_capturefile')
logger.setLevel(logging.ERROR)

#@Version: 2.0
version = "2.0"
#@Author: John Gooch
#@Created: 20121106
#@Updated: 20140616
#@Name: Unzip Utility
#@Description: Unzips files to current or specified folder
#@ Tasks


def initCLI():
	parser = argparse.ArgumentParser(description='Unzip Utility.')
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
	parser.add_argument('-s', action="store", dest="src_dir_path", required=True, help="Path to the folder containing files to unzip.")
	parser.add_argument('-d', action="store", dest="dst_dir_path", required=False, default=".", help="Path to destination folder for unzipped files. Default is current folder.")
	parser.add_argument('-m', action="store", dest="mask", required=False, default=".*\.zip", help="File name pattern for target zip files.")
	parser.add_argument('-o', action="store_true", dest="overwrite", required=False, default=False, help="Overwrite existing files. Default is false.")
	parser.add_argument('--list', action="store_true", dest="list", required=False, default=False,help="Flag to view contents of zip file. Does not unzip any files.")
	parser.add_argument('-e', action="store_true", dest="error", required=False, default=False,help="Flag to throw error if operation does nothing.")
	parser.add_argument('-t', action="store", dest="type", required=False, default="zip",help="Type of compression. Default is zip. Values can be zip or gzip")
	parser.add_argument('--delete-original', action="store_true", dest="delete_original", required=False, default=False,help="Delete original file after successfully unzipping it.")

	"""
	-l  list files (short format)

	  -o  overwrite files WITHOUT prompting
	  -x  exclude files that follow (in xlist)
	"""
	args = parser.parse_args()
	return vars(args)


#initialize the logger object
def initLogging( level ):
	if "DEBUG" in level:
		logger.setLevel( logging.DEBUG )
	elif "INFO" in level:
		logger.setLevel( logging.INFO )
	elif "WARNING" in level:
		logger.setLevel( logging.WARNING )
	elif "ERROR" in level:
		logger.setLevel( logging.ERROR )
	elif "CRITICAL" in level:
		logger.setLevel( logging.CRITICAL )
	else:
		logger.setLevel( logging.ERROR )
	return

#prints the contents of the zip file to stdout
def printContents( zip_file_path ):
	#validate the source zip file
	zf = ZipFile( zip_file_path, 'r' )
	#unzip the contents of the file
	print "\"%s\" contents:" % ( zip_file_path )
	zf.printdir()
	return 0


#lists files in folder matching source file name and tries to unzip all of them.
def gunzip( src_file_path, dst_dir_path ):
	logger.debug( "unzip: unzipping %s to %s" % ( src_file_path, dst_dir_path ) )
	src_dir_path = os.path.dirname( src_file_path )
	src_dir_path = os.path.realpath( src_dir_path )
	src_file_name = os.path.basename( src_file_path )
	dst_dir_path = os.path.realpath( dst_dir_path )
	dst_file_name =  os.path.splitext( src_file_name )[0]
	dst_file_path = os.path.join( dst_dir_path, dst_file_name )
	#validate the source zip file
	zf = gzip.open( src_file_path, 'r' )
	#unzip the contents of the file
	with open( dst_file_path, 'w' ) as of:
		while True:
			buffer = zf.read(16384)
			if not len(buffer):
				break
			else:
				of.write(buffer)
	logger.debug( "Successfully uncompressed %s to %s" % ( src_file_path, dst_dir_path ) )
	return


#lists files in folder matching source file name and tries to unzip all of them.
def unzip( src_file_path, dst_dir_path ):
	logger.debug( "unzip: unzipping %s to %s" % ( src_file_path, dst_dir_path ) )
	src_dir_path = os.path.dirname( src_file_path )
	src_dir_path = os.path.realpath( src_dir_path )
	src_file_name = os.path.basename( src_file_path )

	dst_dir_path = os.path.realpath( dst_dir_path )
	dst_file_name =  os.path.splitext( src_file_name )[0]
	dst_file_path = os.path.join( dst_dir_path, dst_file_name )
	zf = ZipFile( src_file_path, 'r' )
	#validate the source zip file
	badfile = zf.testzip()
	if badfile:
		raise Exception( "BadFileException: File %s failed CRC check." % ( badfile ) )
	else:
		#unzip the contents of the file
		zf.extractall( dst_dir_path )
		logger.debug( "Successfully uncompressed %s to %s" % ( src_file_path, dst_dir_path ) )
	return

def listZipFiles( src_path, file_mask ):
	zipfiles = getZipFileList( src_path, file_mask )
	if ( not zipfiles ) and throw_error:
		logger.error( "No files in folder %s match the file name mask %s" % (src_path, file_mask ) )
		return 1
	else:
		logger.debug( "%d files in folder %s match the file name mask %s" % ( len(zipfiles), src_path, file_mask ) )

	for zipfile in zipfiles:
		try:
			printContents( zipfile )
		except Exception, err:
			logger.error( "Failed to list contents of zip file %s . Reason: %s" % ( zipfile, str(err) ) )
			return 1
	return 0

def main():
	mc = {}
	zip_files = []
	processed_files = []
	deleted_files = []
	try:
		mc.update( initCLI() )
	except Exception, err:
		logger.error( "Exception parsing command line. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	try:
		initLogging( mc['level'])
	except Exception, err:
		logger.error( "Exception initializing logging. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	#normalize paths
	mc['src_dir_path'] =  os.path.realpath(mc['src_dir_path'])
	mc['dst_dir_path'] =  os.path.realpath(mc['dst_dir_path'])

#findFiles( src_dir_path, mask, mode=-1,negativelogic=False ):
	try:
		zip_files = asys.findFiles(mc['src_dir_path'], mc['mask'], -1)
		logger.debug( "%d zip files discovered." % ( len( zip_files) ) )
	except Exception, err:
		logger.error( "Exception listing zip files in %s named like %s. Reason: %s" % ( mc['src_dir_path'], mc['mask'],str(err) ) )
		traceback.print_exc()
		return 2

	if mc['list']:
		for zip_file in zip_files:
			zip_file_path = os.path.join( src_dir_path, zip_file )
			listZipFile( zip_file_path )
			processed_files.append( zip_file_path )
	else:
		#unzip the files the match the file name mask in the source path
		try:
			for zip_file in zip_files:
				logger.info( "Unzipping %s into %s." % ( zip_file, mc['dst_dir_path'] ) )
				zip_file_path = os.path.join( mc['src_dir_path'], zip_file )
				if mc['type'].lower() == "zip":
					unzip( zip_file_path, mc['dst_dir_path'] )
				elif mc["type"].lower() == "gzip":
					gunzip( zip_file_path, mc['dst_dir_path'] )
				else:
					raise Exception( "UnknownFileTypeException: Unknown file type for %s." % ( zip_file_path ) )
				processed_files.append( zip_file )
				logger.info( "%s successfully unzipped into %s." % ( zip_file, mc['dst_dir_path'] ) )
				if mc["delete_original"]:
					logger.info( "delete_original is enabled. Deleting original file %s." % ( zip_file ) )
					os.remove( zip_file )
					logger.info( "Original file %s successfully deleted." % ( zip_file ) )
					deleted_files.append( zip_file )
		except Exception, err:
			logger.error( "Exception unzipping files in %s. Reason: %s" % ( mc["src_dir_path"],str(err) ) )
			traceback.print_exc()
			return 2
		logger.info( "%d files unzipped." % ( len( processed_files) ) )
		logger.info( "%d original files deleted." % ( len( deleted_files) ) )
	if mc['error'] and len(processed_files) == 0:
		return 1
	else:
		return 0


if __name__ == "__main__":
	sys.exit(main())
