import os
import sys
import argparse
import os
import glob
import re
import logging
import subprocess
import time
from datetime import datetime 
import traceback

#@Author: John Gooch
#@Created:  20120515
#@Updated:  20130305
#@Version: 1.1
#@Name: Filestatistic Utility 
#@Description: collects and reports request file statistic

def initCLI():
	parser = argparse.ArgumentParser(description='File Statistics utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.1')
	parser.add_argument('-s', action="store", dest="src_file_dir", required=True, help='Path to the source file directory.' )
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None, help='Destination global variable for file stat.')
	parser.add_argument('-d', action="store_true", dest="debug", default=False, required=False, help='Turn on debugging messages')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	parser.add_argument( '-m', action="store", dest="mask", default=".*", required=False, help="Sets the file name matching mask.")
	parser.add_argument( '-o', action="store", dest="order", default="0", required=False, help="Sort order if mask matches more than one file. Default is oldest.")
	parser.add_argument('-t', action="store", dest="stat", required=True, default="SIZE", help='Specifies the file statistic to return. Values are SIZE, MTIME')
	parser.add_argument('-H', action="store_true", dest="human_readable", required=False, default=False, help='Specifies the file statistic to return. Values are SIZE, MTIME')
	
	#stat_group = parser.add_mutually_exclusive_group()
	#stat_group.add_argument('-t', action="store_true", dest="mtime", required=False, default=False, help='Request to get the file modified time.')
	#stat_group.add_argument('-s', action="store_true", dest="size", required=False, default=True, help='Request to get the file size in bytes.')

	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

		
		
def initLogging(args):
	global logger
	logger = logging.getLogger()
	if args.level is False:
		logger.setLevel(logging.WARNING)
	elif ( args.level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( args.level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( args.level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( args.level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( args.level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return 0
			
			
			
	
#retrieves the requested file statistic and returns it as a string value
def getFileStat( src_file_path, stat ):
	value = None
	if ( stat  == "MTIME" ): 
		value = str(os.path.getmtime( src_file_path ) ) 
	elif ( stat == "SIZE" ): 
		value = os.path.getsize( src_file_path ) 
	else:
		logger.error( "File stat %s not recognized." % ( stat )  )
	return value
	
	
#stores statistic in the specified global variable
def setGV(gvar, value ):
	cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd ) 
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		return 1
		
	if returncode != 0:
		logger.error("Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		return 1
	else:
		logger.info("Successfully set global variable  %s = %s" %  ( gvar, value ) )
		return 0

def printFileStat( key , value ):
	print "%s=%s" % ( key, value )
	return 0

def findFile( path, mask,sort_order ):
	logger.debug( "Watching directory %s for file name matching %s" % ( path, mask  ) ) 
	src_dir_path = os.path.realpath(path)
	if os.path.exists( src_dir_path ) == False:
		logger.error( "Cannot access path %s. Please check path and permissions." % ( src_dir_path ) )
		raise SystemExit

	try:
		os.chdir( src_dir_path )
	except Exception, err:
		logger.error( "Failed to change directory to %s. Reason: %s"  % ( src_dir_path, str(err) )  )
		raise
		
	files = glob.glob("*")
	if not files:
		return None
	selected_file = None
	selected_time = None
	src_file_path = None
	for filename in files:
		src_file_path = os.path.join( src_dir_path, filename ) 
		if not os.path.isfile( src_file_path ):
			continue
		elif not re.match( mask, filename, re.I ):
			logger.debug( "File %s name does not match file mask %s" % ( filename, mask ) )
			continue
		else:
			logger.debug( "Processing Filename is %s . File path is %s." % ( filename, os.path.join( src_dir_path, filename) ) )
			mtime = os.path.getmtime( src_file_path )
			mtime_string = datetime.strftime( datetime.fromtimestamp(mtime),"%Y%m%d %H%M%S"  )
			if selected_time == None:
				selected_time = mtime
				selected_file = src_file_path
				logger.debug( "Selected file set to %s . Selected modified time: %s." % ( src_file_path, mtime_string ) )
			#sort oldest modification time first
			elif sort_order == 0: 
				if selected_time >= mtime:
					selected_time = mtime
					selected_file = src_file_path
					logger.debug( "Selected file set to %s . Selected modified time: %s." % (src_file_path, mtime_string ) )
			#sort newest modification time first
			elif sort_order == 1:
				if selected_time <= mtime:
					selected_time = mtime
					selected_file = src_file_path
					logger.debug( "Selected file set to %s . Selected modified time: %s." % ( src_file_path, mtime_string ) )
			else:
				logger.error( "Sort order %d not recognized. Please check syntax." % ( sort_order ) )
	if not selected_file:
		logger.error( "Failed to find a file in directory %s matching file name mask %s" % ( src_dir_path, mask ) )
		return None
	else: 	
		logger.debug( "Found file %s with a modified time of %s" % ( selected_file , mtime_string ) )
		return selected_file
	

def main():
	args = initCLI()
	if ( args is None ):
		print "Exiting..."
		return 1
	if initLogging(args) != 0 :
		print "Failed to initialize logger. "
		return 1


	try:
		src_file_path = findFile( args.src_file_dir, args.mask, args.order )
	except Exception, err:
		logger.error("Failed to find file in %s matching file name pattern %s. Reason: %s" % ( args.src_file_dir, args.mask, str(err) ) )
		traceback.format_exc()
		return 2
		
	if src_file_path == None:
		logger.error( "Could not find file matching %s in folder %s." % ( args.mask, args.src_file_dir ) )
		return 1
	file_stat = None
	
		
		
	file_stat = getFileStat( src_file_path, args.stat )
	if ( file_stat is None):
		logger.error( "Failed to get file stat %s for file %s.\nExiting..." %  ( args.stat,src_file_path   ) )
		return 2
	if args.human_readable:
		if args.stat in "MTIME":
			#file_stat = time.ctime(float(file_stat))
			file_stat = time.strftime('%m/%d/%Y %H:%M:%S',time.localtime(float(file_stat) ) )

		elif args.stat in "SIZE":
			file_stat = file_stat
 	if args.global_variable:	
		if setGV( args.global_variable , file_stat) != 0:
			logger.error( "Failed to store file stat %s for file %s in global variable %s .\nExiting" % ( args.stat,src_file_path , args.global_variable  ) )
			return 2
		else:
			logger.debug( "Global variable %s=%s" % ( args.global_variable, str(file_stat) ) )
	if printFileStat( args.stat, file_stat  ) != 0:
		logger.error( "Failed to print file statistic %s which was equal to %s.\nExiting..." % ( args.stat, str(file_stat)  )  )
		return 2
	return 0;


if __name__ == "__main__":
	sys.exit(main());