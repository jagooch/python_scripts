#core modules
import argparse
import logging
import os
import sys
import traceback

import asys

global logger
logger = logging.getLogger('deletefile')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#script specific modules.

#@Author: John Gooch
#@Created: 20120824
#@Updated: 20130907
version = "2.2"
#@Name: Delete File Script
#@Description: Deletes file(s) from specified folder with specified file name pattern. 
#@1.2 20130507 - Replaced error return codes with exceptions, 
#@2.0 20130711 - Added the -T switch to specify the delete mode ( eg NEWEST, OLDEST, ALL ). updated findFiles and move files functions
#@2.1 20130907 - Fixed handling of "no files found" event. refactored code to put setgvar and reporting at top level. findFiles should be moved in asys module.
#@2.2 20140502 - Logging and moved common functions into asys module.

def initCLI():
	parser = argparse.ArgumentParser(description='Delete File Utility')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s {version}'.format( version=version ) )
	parser.add_argument('-s', action="store", dest="src_dir_path", required=True, help='Path of the files to be deleted.')
	parser.add_argument('-m', action="store", dest="src_file_mask", required=True, help='File name mask for files to be deleted. Case-insensitive')
	parser.add_argument('-g', action="store", dest="global_variable", default=False, required=False, help="Global variable name to store number of files copied." )
	parser.add_argument('-T', action="store", dest="type", required=False, default="ALL", help='Specifies processing mode for files. Default is ALL. Other options are OLDEST(single), NEWEST(single)')
	parser.add_argument('-n', action="store_true", dest="negative_logic", required=False, default=False, help='Match on file names that do not match the file name mask.')
	parser.add_argument('-e', action="store_true", dest="error", default=False, help='Flag to throw an error if no files are deleted.')
	parser.add_argument( '-l', action="store", dest="level", required=False, default="INFO",help="Sets the logging level for the script. Default is INFO" )
	try:
		args = parser.parse_args()
		items = vars(args)
		for item in items.keys():
			if type(items[item]) is str:	
				if not items[item].strip():
					raise Exception( "Empty parameter %s." % ( item ) )
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		raise

def initLogging( level ):
	if level is None:
		raise Exception( "level not initialized.") 
	elif ( level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	else:
		raise Exception( "Invalid logging level %s specified." % ( level ) ) 
	return
		
#deletes files in src path folder that are in the files arrays		
def deleteFiles( src_path, files, error, global_variable ):
	deleted_files = []
	#get the absolute path to the file. This handles . and .. relative file path components
	src_path = os.path.realpath( src_path )
	if not os.path.exists(src_path):
		logger.error( "Source path is %s not accessible. Check path and permissions." % ( src_path ) )
		raise Exception( "Source path is %s not accessible. Check path and permissions." % ( src_path ) )
	logger.debug( "Source path %s exists and is accessible. Listing files." % ( src_path ) ) 
	logger.debug( "Found %d files in folder %s " % ( len(files), src_path ) )  
	for file_name in files:
		src_file_path = os.path.join(  src_path, file_name )
		if os.path.isfile(src_file_path) == False:
			logger.debug( "%s is not a regular file. Skipping." % ( src_file_path ) )
			continue
		else:
			try:
				logger.info("Deleting file %s." % ( src_file_path ) )
				os.remove(  src_file_path ) 
				logger.info("Successfully deleted file %s." % ( src_file_path ) )
				deleted_files.append( src_file_path )
			except Exception, err:
				logger.error( "Failed to delete file %s. Reason: %s" % ( src_file_path, err ) )
				raise Exception( "Failed to delete file %s. Reason: %s" % ( src_file_path, err ) ) 
	return deleted_files

		
def main():
	global logger
	global args 
	files = None
	deleted_files = None
	#parse the command line parameters
	try:
		args = initCLI()
	except Exception, err:
		print "Exception encountered while parsing command line arguments. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		initLogging(args.level)
	except Exception, err:
		print "Exception encountered while initializing the logging facility. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2
		
	try:
		if args.type in "ALL":
			files = asys.findFiles(args.src_dir_path, args.src_file_mask, -1, args.negative_logic)
		elif args.type in "OLDEST":
			files = asys.findFiles(args.src_dir_path, args.src_file_mask, 0, args.negative_logic)
		elif args.type in "NEWEST":
			files = asys.findFiles(args.src_dir_path, args.src_file_mask, 1, args.negative_logic)
		else:
			logger.error( "Exception. Operation type %s not recognized." % ( args.type ) )
			raise Exception( "Exception. Operation type %s not recognized." % ( args.type ) )
	except Exception, err:
		logger.error( "Exception finding files in %s. Reason: %s." % ( args.src_dir_path, str(err) ) )
		traceback.print_exc()
		return 2

	if files is None:
		logger.error( "Exception: Null file object returned. Code error." )
		return 2
	elif len(files) == 0:
		if args.error:
			logger.error( "Error: No files found in %s that matched the supplied criteria." % ( os.path.realpath( args.src_dir_path ) ) )
			return 1
		else:
			logger.debug( "%d files found matching the search criteria." ) 
			
	try:
		logger.debug( "Calling deleteFiles to delete files from folder %s with file name matching %s."  % ( args.src_dir_path, args.src_file_mask ) )
		deleted_files = deleteFiles( args.src_dir_path, files, args.error, args.global_variable)
	except Exception, err:
		logger.error( "Exception encountered while deleting files. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	try:
		if deleted_files is None:
			raise Exception( "Exception. Null deleted_file object returned. Fix code. " ) 
	except Exception, err:
		traceback.print_exc()
		return 2

	if args.global_variable:
		asys.setGV(args.global_variable, len(deleted_files))
		logger.info( "Global variable %s set to %d." % ( args.global_variable, len(deleted_files) ) )
		
	if len(deleted_files) == 0 and args.error:
		logger.error( "Error: No files were deleted from \"%s\"." % ( os.path.realpath( args.src_dir_path ) ) )
		return 1
	else:
		for file in deleted_files:
			logger.info( "%s was successfully deleted."  % ( file ) )
		logger.info( "%d files were deleted from \"%s\"." % ( len(deleted_files), os.path.realpath( args.src_dir_path ) ) )
		return 0
		
if __name__ == "__main__":
	sys.exit(main());