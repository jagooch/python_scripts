#core libraries
import argparse
import logging
import os
import sys
import traceback

import asys
#add-ons
import time
from datetime import datetime

global logger
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#@Author: John Gooch
#@Created: 20120606
#@Updated: 20150212
version = "6.0"
#@Name: John Gooch
#@Description: Detect presence of stable file.
#@6.0 20150212 - add handling of file deletion after detected. updated help output to explain commands.Added -c parameter .
#@5.6 20140606 - Updated reverse logic to use timeout loop instant of being a short circuit setting.
#@5.5 20140606 - Logging and moved common functions into asys module.
#@5.4 20140502 - Logging and moved common functions into asys module.
#@5.2 20140130 Added Cody's reverse file logic code ( -r switch ) .
#@5.1 20140118 Added file permissions checking, fixed file min/max size checks.
#@5.0 20131218 Added support for storing file names longer than 64 characters by allowing the user to supply comma sep list of gv's
#@4.6 20130729 Fixed incorrect timeout formula that made timeout equal to interval.
#@4.5 20130723 Added time string convert to allow user to specify units of time( eg 1s=1 second 1m=1 minute 1h=1 hour 
#@4.4 20130507 Added check for empty (double quoted)  parameters 
#@4.3 Added minumum and maximum file size parameter - this comes into play after the file is determined to be stable
#@    removed useless code that referenced the cancelled conf file feature
#@4.2 20121224 replaced failure return codes with exceptions. 
#@    Moved the global variable deletion into Main and fixed the output of the setGV function
#@4.1 20121121
#@ fixed path manipulation problem that caused script to crash

def initCLI():
	parser = argparse.ArgumentParser(description='File watcher utility')
	parser.add_argument( '--max', action="store",dest="file_max_size", required=False, default=None, help='Maximum file size. Optional. Accepted units are b=bytes k=kilobytes m=megabytes g=gigabytes.' ) 
	parser.add_argument( '--min', action="store",dest="file_min_size", required=False, default=None, help='Minimum file size. Optional. Accepted units are b=bytes k=kilobytes m=megabytes g=gigabytes.' ) 
	parser.add_argument( '-a', action="store",dest="access", required=False, default=None, help="File access check. valid values are 'r' read  'rw' read write" ) 
	parser.add_argument( '-c', action="store",dest="threshold", required=False, type=int, default=3, help='File stability count threshold. Or number of times that file size checks must be the same before file is considered stable.' ) 
	parser.add_argument( '-g', action="store",dest="global_variable", required=False, default=[], help='Comma separated list of global variables for file name storage.One gv is necessary for every 64characters of the file name.' ) 
	parser.add_argument( '-i', action="store", dest="interval", default="10s",required=False, help='File size monitoring interval. Accepted units are s seconds m minutes h hours. eg 1m=1minute')
	parser.add_argument( '-l', action="store",dest="level", default="INFO", help='Sets the logging level for the script. Default is INFO' )
	parser.add_argument( '-m', action="store",dest="mask", required=False, default=".*", help='Pattern to match files to.' )
	parser.add_argument( '-o', action="store",dest="sort_order", default=0, required=False, help='Sort order for files that match pattern. 0 = oldest. 1= newest.' , type=int)
	parser.add_argument( '-r', action="store_true",dest="reverse_condition", required=False, default=False, help='Reverse filewatcher. Fails if there are any files, succeeds if there are none. Optional.Default=False.')
	parser.add_argument( '-s', action="store",dest="src_dir_path", required=False, default=".", help='Path to the directory to watch for files' )
	parser.add_argument( '-t', action="store",dest="timeout", default="1m", required=False, help='Time to wait before giving up and returning exit code 1. Set to 0 to skip file stability check. Time units are s seconds m minutes h hours d days. eg 1m=1 minute' )
	parser.add_argument( '-v', '--version', action='version', version='%(prog)s {version}'.format(version=version) , help='Display script version.')
	args = parser.parse_args()
	items = vars(args)
	for item in items.keys():
		if type(items[item]) is str:	
			if not items[item].strip():
				raise Exception( "Empty parameter %s." % ( item ) )
	return args
	
	
def initLogging( level ):
	if level is False:
		logger.setLevel(logging.WARNING)
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
	return
	
def getElapsedTime( start_time ):
	return ( datetime.now() - start_time ).total_seconds()
		
def monitorFile( src_dir_path, mask, interval, timeout, sort_order, file_min_size, file_max_size, global_variable, access, reverse_condition,file_stability_threshold ):
	src_file_path = None
	src_dir_path = os.path.realpath(src_dir_path)
	start_time = datetime.now()
	#ensure the values are in a safe range.
	if interval < 3:
		interval = 3
	if file_stability_threshold < 0:
		file_stability_threshold = 0
	if file_min_size < 0:
		file_min_size = 0
	if timeout < 0:
		timeout = 0
	
	#check access and existence of the source folder
	if os.path.exists(src_dir_path) == False:
		raise Exception( "Cannot access path %s. Please check path and permissions. " % ( src_dir_path ) )
	elif os.path.isdir(src_dir_path) == False:
		raise Exception( logger.error( "Path %s is not a directory. Please check path. " % ( src_dir_path ) ) )

	#check for the existence of a file matching name criteria
	logger.debug( "Starting MonitorFile at %s. Watching directory %s for a file %s with timeout %d and interval %d" % ( start_time.strftime('%Y/%m/%d %H:%M:%S'), src_dir_path, mask, timeout, interval ) )
	src_file_path = None
	file_stability_count = 0
	#file_stability_threshold = 3
	last_file_size = file_size = 0
	#File check criteria. The ok means based on what the command indicated is important the file properties are 'ok' 
	file_exists_ok = False
	file_readable = False
	file_writable = False
	file_executable = False
	file_stability_ok = False 
	file_min_size_ok = False
	file_max_size_ok = False
	file_read_ok = False
	file_write_ok = False
	file_execute_ok = False
	previous_src_file_path = None


	#File criteria checks
	while True:

		#update the source file path 
		#check if path was set from previous run and still valid
		if src_file_path and os.access( src_file_path, os.F_OK ):
			file_exists_ok = True
		#get new source file path and reset statisics
		else:
			file_stability_count = 0
			last_file_size = file_size = 0
			src_file_path = asys.findFile(src_dir_path, mask, sort_order)
			if src_file_path:
				file_exists_ok = os.access( src_file_path, os.F_OK )
			else:
				file_exists_ok = False
				
		#File stats collection block
		if file_exists_ok:
			logger.debug( "File %s exists. File_Ok: %s .Checking file stats."  % ( src_file_path, file_exists_ok ) ) 
			try:
				#get file size
				file_size = os.path.getsize( src_file_path )
				#get file permissions/access
				file_readable = os.access( src_file_path, os.R_OK )   
				file_writable = os.access( src_file_path, os.W_OK )
				file_executable = os.access( src_file_path, os.X_OK )
			except:
				file_exists_ok = False
				file_stability_count = 0
				pass

				
		#Decision Block
		if file_exists_ok:
			#File stability check
			if timeout == 0:
				file_stability_ok = True
			elif file_size == last_file_size:
				file_stability_count +=1
				if file_stability_count >= file_stability_threshold:
					file_stability_ok = True
				else:
					file_stability_ok = False
			else:
				last_file_size = file_size
				file_stability_count = 0
				
			#File minimum size check
			if file_min_size == -1:
				logger.debug( "File min size value %d disables min size checking." % ( file_min_size ) )
				file_min_size_ok = True
			elif file_size >= file_min_size:
				logger.debug( "File size %d is >= file min size %d" % ( file_size, file_min_size ) )
				file_min_size_ok = True
			else:
				logger.debug( "File size %d is > file min size value %d." % ( file_size, file_min_size ) )
				file_min_size_ok = False
				
			#File maximum size check
			if file_max_size == -1:
				logger.debug( "File max size value %d disables max size checking." % ( file_max_size ) )
				file_max_size_ok = True
			elif file_size <= file_max_size:
				logger.debug( "File size %d is <= file max size %d" % ( file_size, file_max_size ) )
				file_max_size_ok = True
			else:
				logger.debug( "File size %d is greater than max size value %d." % ( file_size, file_max_size ) )
				file_max_size_ok = False

			#File read access check
			if access:
				if 'r' in access:
					#check the file readability setting
					file_read_ok = file_readable
				else:
					#true if readability check not requested 
					file_read_ok = True
			else:
				#true if access parameter not given
				file_read_ok = True
					
			#file write access check:
			if access:
				if 'w' in access:
					#check file writability 
					file_write_ok = file_writable
				else:
					#true if write check not requested
					file_write_ok = True
			else:
				file_write_ok = True
			
		logger.info( "File Exists:%s| File Stable:%s| Min Size:%s| Max Size:%s| Readable:%s| Writeable:%s" % ( file_exists_ok,file_stability_ok, file_min_size_ok, file_max_size_ok, file_read_ok, file_write_ok ) ) 
		logger.debug("FilePath: %s. Interval: %d. Count: %d. Threshold: %d. last_file_size: %d| Reverse Condition: %s " % ( src_dir_path,interval,file_stability_count,file_stability_threshold,last_file_size, reverse_condition ))
				
		#if looking for the lack of existence of the file
		if reverse_condition: 
			if not file_exists_ok:
				logger.info( "File matching %s not found and reverse condition enabled. Returning exit code 0." % ( mask ) ) 
				return 0
		#if the file meets the specificied criteria
		elif file_stability_ok and file_min_size_ok and file_max_size_ok and file_read_ok and file_write_ok and file_exists_ok:
			logger.info( "File %s with file size: %d |Passed checks." % ( src_file_path, last_file_size ) ) 
			#set the global variable if requested 
			if ( global_variable ):
				asys.setGV(global_variable, os.path.basename(src_file_path))
			else:
				logger.info( "Global variable option not selected. Not setting global variable." )
			return 0

		if getElapsedTime(start_time ) > timeout:
			logger.info( "Timeout was exceeded before file meeting criteria was found. Returning Exit Code 1." ) 
			return 1
		#exit conditions not met, sleep and repeat loop
		logger.info("Sleeping for %d seconds" % ( interval ) )
		time.sleep(interval)

	
def main():
	global args
	global file_min_size
	global file_max_size
	file_min_size = None
	file_max_size = None
	interval_seconds = 0
	timeout_seconds = 0
	
	try:
		args = initCLI()
	except Exception, err:
		print "Error parsing command line arguments. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2
		
	try:
		initLogging(args.level)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2


	#convert the min and max threshold values from text to long integers ( if supplied )
	if args.file_min_size:
		try:
			file_min_size = asys.getBytes(args.file_min_size)
		except Exception, err:
			logger.error("Invalid minimum threshold format - %s. Check parameter. Reason: %s" % ( args.file_min_size, str(err)  ) )  
			traceback.print_exc()
			return 2
	else:
		file_min_size = -1

	if args.file_max_size:
		try:
			file_max_size = asys.getBytes(args.file_max_size)
		except Exception, err:
			logger.error("Invalid maximum threshold format - %s. Check parameter. Reason %s" % ( args.file_max_size, str(err)  ) )  
			traceback.print_exc()
			return 2
	else:
		file_max_size = -1
	
	try:
		interval = asys.getSeconds(args.interval)
	except Exception, err:
		logger.error( "Exception getting Interval Seconds. Reason: %s" % ( str(err) ))
		traceback.print_exc()
		return 2

	try:
		timeout = asys.getSeconds(args.timeout)
	except Exception, err:
		logger.error( "Exception getting Timeout Seconds. Reason: %s" % ( str(err) ))
		traceback.print_exc()
		return 2
		
	try:
		return monitorFile( args.src_dir_path, args.mask, interval, timeout, args.sort_order, file_min_size, file_max_size, args.global_variable,args.access, args.reverse_condition,args.threshold  )
	except Exception, err:
		logger.error( "Failed monitor for file presence. Reason: %s" % ( str(err) ) )  
		traceback.print_exc(file=sys.stdout)
		return 2
		

if __name__ == "__main__":
	sys.exit(main())