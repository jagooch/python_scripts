import argparse
import datetime
import logging
import os
import sys
import traceback
import zipfile

import asys

global logger
logging.basicConfig()
logger = logging.getLogger('zip')
logger.setLevel(logging.INFO)

version = "2.2"
#@Version: 2.2 
#@Author: John Gooch
#@Created: 20121106
#@Updated: 20140711
#@Name: Zip Utility
#@Description: Zips files in specified folder or subfolders.
#@ Tasks
#Version 2.2 20140925 
#Added timestamping of zip file
#fixed file enumeration method, added --archive switch, updated logging. 
#Version 2.1 20140711 
#fixed file enumeration method, added --archive switch, updated logging. 
#Version 2.0 20130207
#Completed core unzip functionality 
#Version 1.0 20130117
#Completed core zip functionality 


def initCLI():
	parser = argparse.ArgumentParser(description='Zip Utility.')
	parser.add_argument('-s', action="store", dest="src_dir_path", required=False, default=".", help="Path to parent directory of files.")
	parser.add_argument('-f', action="store", dest="zip_file_path", required=True, help="Path to zip file to create." )  
	parser.add_argument( '-i', '--imask', action="store", dest="include", required=False, default=".*", help="Include file mask. Applies to all levels.")
	parser.add_argument( '-x', '--xmask', action="store", dest="exclude", required=False, default="a^", help="Exclude file mask. Applies to all levels.")
	parser.add_argument('--archive', action="store_true", dest="archive", required=False, default=False,help="Archive flag causes files to be deleted after being added to the zip file.")
	parser.add_argument('-e', action="store_true", dest="error", required=False, default=False, help="Fail if no files are processed.")
	parser.add_argument('-t', action="store_true", dest="timestamp", required=False, default=False, help="Add timestamp to zip file name.")
	parser.add_argument('-r', action="store_true", dest="recursive", required=False, default=False, help="Path to zip file to create." )  
	parser.add_argument('-p', action="store", dest="password", required=False, default=False, help="Set password on zip file." )  
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")

	arcname = parser.add_mutually_exclusive_group()
	arcname.add_argument('--flat', action="store_true", dest="flat", required=False, default=False, help="Store file with name only." )  
	arcname.add_argument('--relative', action="store_true", dest="relative", required=False, default=False, help="Store file with relative path.")
	arcname.add_argument('--full', action="store_true", dest="full", required=False, default=False, help="Store file with absolute path.")

	actions = parser.add_mutually_exclusive_group(required=True)
	actions.add_argument('-c', action="store_true", dest="create", required=False, default=False, help="Create archive.")
	actions.add_argument('-a', action="store_true", dest="add", required=False, default=False, help="Add files to archive.")
	actions.add_argument('-u', action="store_true", dest="update", required=False, default=False, help="Update files in archive.")
	args = parser.parse_args()
	return vars(args)
	
def initLogging( level ):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING,
		"ERROR":logging.ERROR ,
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level.upper()] )
	return

def createZipFile ( file_entries, zip_file_path ):
	compression = None
	zipped_files = []
	logger.debug( "zip file path is %s" % ( zip_file_path ) )
	try:
		compression = zipfile.ZIP_DEFLATED
	except:
		compression = zipfile.ZIP_STORED
		pass

	zf = zipfile.ZipFile( zip_file_path, mode='w', compression=compression  )
	for file_entry in file_entries:
		logger.debug( "Adding %s to %s." % ( file_entry["path"], zip_file_path  ) )
		zf.write( file_entry["path"], file_entry["arcname"] ) #write the file path to zip file
		zipped_files.append( file_entry ) 
	zf.close()
	logger.info( "Closed zip file %s" % ( zip_file_path ) )
	return zipped_files

def deleteFiles( files ):
	deleted_files = []
	for file in files:
		logger.debug( "Deleting %s." % ( file["path"] ) ) 
		os.remove( file["path"] )
		logger.info( "%s deleted." % ( file["path"] ) ) 
		deleted_files.append( file["path"] )
	return deleted_files
	
def main():
	mc = {}
	files = []
	processed_files = []
	try:
		mc.update( initCLI() )
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

	try:
		initLogging( mc["level"])
	except Exception, err:
		print "Exception while initializing logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

	#normalize zip file path
	mc["zip_file_path"] = os.path.realpath( mc["zip_file_path"] )
	mc['src_dir_path'] =  os.path.realpath( mc['src_dir_path'] )
	logger.debug( " Real src dir path is %s " % ( mc['src_dir_path'] ) )
	
	#collect file names
	try:
		files.extend(asys.findFiles2(mc['src_dir_path'], mc['include'], mc['exclude'], mc["recursive"]))
		logger.debug( "%d files found to archive." % ( len( files ) ) )
	except Exception, err:
		logger.error( "Exception finding files in %s. Reason: %s" % ( mc['src_dir_path'], str(err) ) )
		traceback.print_exc()
		return 2

	#create archive names
	file_entries = []
	for file in files:
		entry = None
		if mc["flat"]:
			entry = { "path":file, "arcname": os.path.basename(file) }
		elif mc["relative"]:
			parent_dir = os.path.dirname(file)
			start_dir = os.path.dirname( mc['src_dir_path'] )
			relative_path = os.path.relpath( parent_dir, start_dir )
			logger.debug( "Relative path for start %s and parent %s is %s" % ( start_dir, parent_dir, relative_path )  )
			relative_file_path =  os.path.join(  relative_path , os.path.basename(file) )
			logger.debug( "relative file path is '%s'" % ( relative_file_path ) )
			entry = { "path":file, "arcname": relative_file_path  }
		elif mc["full"]:
			entry = { "path":file, "arcname":file }
		else:
			raise Exception( "ArcnameException: File arcname not specified." )
		logger.debug( "%s,%s added to file entry list." % ( entry["path"], entry["arcname"] ) )
		file_entries.append( entry )
	#perform request action using selected files
	#create new zip file
	if mc["create"]:
		zip_file_path = None
		if mc["timestamp"]:
			zip_file_name = os.path.basename( mc["zip_file_path"] )
			zip_dir_path = os.path.dirname( mc["zip_file_path"] )
			timestring = datetime.datetime.strftime( datetime.datetime.now(), '%Y%m%d_%H%M%S' )
			( root , ext )  = os.path.splitext(zip_file_name)
			zip_file_name = "%s_%s%s" % ( root, timestring, ext ) 
			zip_file_path = os.path.join( zip_dir_path, zip_file_name ) 
			logger.debug( "zip file path timestamped to %s" % ( zip_file_path ) )
		else:
			logger.debug( "Timestamp is %s. zip file will not be timestamped." % ( mc["timestamp"] ) )

		try:
			zipped_files = createZipFile( file_entries, zip_file_path )
			logger.info( "%d files added to archive file %s" % ( len( zipped_files), zip_file_path ) )
			if mc["archive"]:
				deleted_files = deleteFiles( zipped_files )
		except Exception, err:
			logger.error( "Exception while creating zip file. Reason: %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	else:
		logger.error( "Either Create or Add actions must be specified. Please check parameters(-h) and try again." )
		return 2

	return 0


if __name__ == "__main__":
	sys.exit(main());





