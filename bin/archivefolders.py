#Template for Python Scripts
import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime

import asys
import deletefile

global logger
logging.basicConfig()
logger = logging.getLogger('archivefolder')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

version="1.0"
#@Author: John Gooch
#@Created: 20140520
#@Updated: 
#@Name: Archive Folder Script 
#@Description: 
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Archive Folder v1.0')
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	parser.add_argument('-j', action="store", dest="json_file_path", required=True, help="Path to json file containing folder archiving configurations.")
	args = parser.parse_args()
	return vars(args)

def initLogging(level):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING, 
		"ERROR":logging.ERROR, 
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level] )
	return
	
def loadFolders( json_file_path ):
	json_file_path = os.path.realpath( json_file_path) 
	if not os.path.exists( json_file_path ):
		raise Exception( "JSON File %s does not exist or is not accessible." )
	json_data = open( json_file_path,'r' ).read().strip('\n')
	return json.loads(json_data)
	# return data
	
	
def archiveFolders( folders ):
	archived_folders = []
	for folder in iter(folders):
		logger.debug( "Processing Folder %s" % ( folder["folder_name"] ) )
		if os.path.exists( folder["folder_path"] ):
			processed_files = archiveFolder( folder )
			logger.info( "Folder %s path %s was successfully processed. %d files." % ( folder["folder_name"], folder["folder_path"], len(processed_files) ) )
			archived_folders.append( [ folder, processed_files ] )
		else:
			logger.error( "Error: Folder %s does not exist or is not accessible. Skipped." % ( folder["folder_path"] ) )
			continue
	return archived_folders
			
def archiveFolder( folder ):
	processed_files = []
	current_time = datetime.now()
	logger.debug( "Folder recursion is %s" % ( folder["folder_recursion"] ) ) 
	files = asys.listFiles(folder["folder_path"], folder["folder_recursion"])
	files = asys.filterFiles(files, folder["file_criteria"])
	file_action = folder["file_action"]
	if "list" in file_action["action"]:
		logger.debug( "File action is \"%s\"." % ( file_action["action"]  )  )
		#processed_files = listFiles()
		template = "{0:20} {1:50} {2:>12} {3:22}"
		logger.info( template.format( "File Name", "File Path", "File Size","File Modified" ) )
		for file in files:
			logger.info( template.format( file["file_name"], file["file_path"], file["file_size"], datetime.fromtimestamp( file["file_mtime"] ).strftime( "%m/%d/%Y %H:%M:%S" ) ) )
			processed_files.append( file )
			return processed_files
	elif "delete" in file_action["action"]:
		logger.debug( "Deleting %d files." % ( len(files) ) )
		processed_files = deletefile.deleteFiles(folder["folder_path"], files)
		return processed_files
	# elif "move" in action:
		# logger.debug( "Moving files %d files from %s to %s." % ( len(archive_files),folder["src_folder_path"], folder["dst_folder_path"] ) )
		# return movefile.moveFiles( folder["src_folder_path"], folder["dst_folder_path"], archive_files, overwrite, timestamp, format, prepend  )
	# elif "archive" in action:
		# return None
	else:
		return processed_files
		
def printReport( archived_folders ):
	for record in archived_folders:
		folder, files = record
		folder_name = folder["folder_name"]
		action = folder["file_action"]
		template = "{0:20} {1:7} {2:25}"
		for file in files:
			print template.format( folder_name, action, file["file_path"] )
		return
		
		
def main():
	mc  = {} #master configuration dictionary that holds all command line and configuration file parameters
	try:
		#update command line arguments into master configuration 
		mc.update( initCLI() )
	except argparse.ArgumentError, err:
		logger.error( "Invalid command line syntax. Reason: %s" % ( str(err) )  )
		traceback.print_exc()
		return 2
	except Exception, err:
		logger.error( "Failed to parse command line arguments. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	#initialize logging
	try:
		initLogging( mc['level'])
	except Exception, err:
		logger.error( "Failed to initialize logging. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
		
	#load folder archive configurations from JSON file
	try:
		archive_folders = loadFolders( mc['json_file_path'] )
	except Exception, err:
		logger.error( "loadFolders Exception. Failed to load folders. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	# for archive_folder in archive_folders:
		# for key,value in archive_folder.iteritems():
			# print "%s=%s\n" % ( key, value )
		# print "\n\n"
		
	#Archive each configured folder based on configuration
	try:
		archived_folders = archiveFolders( archive_folders )
	except Exception, err:
		logger.error( "Archive Folders Exception. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
 		return 2
		
	try:
		printReport( archived_folders )
	except Exception, err:
		logger.error( "Exception: Print Report Exception. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
 		return 2
	
	return 0


if __name__ == "__main__":
	sys.exit(main());

