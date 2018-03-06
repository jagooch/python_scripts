#Template for Python Scripts
import argparse
import logging
import os
import re
import sys
import time
import traceback

import sendmail

global logger
logging.basicConfig()
logger = logging.getLogger('textfile_monitor')
logger.setLevel(logging.ERROR)

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20150924
#@Updated: 20150929
#@Name: Text file Monitor
#@Description: Monitors text file for specific text and notifies recipients. 
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Text File monitor v1.0')
	parser.add_argument('-s', action="store", dest="src_file_path", required=True,help="Full path to text file, including text file name.")
	parser.add_argument('-r', action="store", dest="recipients", required=True,help="Comma separated list of email recipients.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	parser.add_argument('-p', action="store", dest="pattern", required=True,help="Text to monitor for.")	
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

def getmtime( file_path ):
	return os.stat( file_path )[8]


def getLineCount( file_path ):
	#get the line count
	with open( file_path, 'r' ) as f:
		linecount = sum( 1 for _ in f ) 
		f.close()
	return linecount

def main():
	src_file_path = None
	last_mtime = None
	last_linecount = None
	#set file path
	#pattern = re.compile( 'ORA-06512', re.I )
	pattern = None
	mc  = {} #master configuration dictionary that holds all command line and configuration file parameters
	try:
		#append command line arguments to master configuration 
		mc.update( initCLI() )
	except argparse.ArgumentError, err:
		logger.error( "Invalid command line syntax. Reason: %s" % ( str(err) )  )
		traceback.print_exc()
		return 2
	except Exception, err:
		logger.error( "Failed to parse command line arguments. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	
	try:
		initLogging( mc['level'])
	except Exception, err:
		logger.error( "Failed to initialize logging. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	#get the modified time
	try:
		last_mtime = os.stat( mc['src_file_path'] )[8] 
	except Exception, err:
		logger.error( "Failed to get file modified time. Reason: %s." % ( str(err) ) )  
		traceback.print_exc()
		return 2

	#get the linecount 
	try:
		last_linecount = current_linecount = getLineCount(mc['src_file_path'] )
	except Exception, err:
		logger.error( "Failed to get file modified time. Reason: %s." % ( str(err) ) )  
		traceback.print_exc()
		return 2
	
	#compile the search pattern
	pattern = re.compile( mc['pattern'], re.I )
	
	try:
		#file monitoring loop
		while True:
			#wait for the file to change
			while getmtime( mc['src_file_path'] ) == last_mtime:
				logger.info( "File mtime unchanged. Sleeping..." ) 
				time.sleep( 3 )
			logger.debug( "File mtime has changed." )
			last_mtime = getmtime( mc['src_file_path'] )
			with open( mc['src_file_path'] ) as file:
				lines = file.readlines()
				current_linecount = getLineCount( mc['src_file_path'] )
				logger.debug( "last_linecount: %d current_linecount: %d" % ( last_linecount,current_linecount) )
				if last_linecount < current_linecount:
					newlines  = lines[last_linecount:]
					last_linecount = current_linecount
					for line in newlines:
						if pattern.search( line ):
							print "Line contains oracle error. Line = %s"  % ( line ) 
							#sendmail.sendMail( smtp_server, smtp_user,smtp_pwd,sender, subject, nts, cc, body, files, encoding,replyto=None):
							sendmail.sendMail('smtpext.maxcorp.maximus', None, None, 'autosys_alert@maximus.com', 'FAILURE - ASYS - ORACLE Error Detected.', mc['recipients'], None, 'Oracle error detected in event_demon.PRD file. Send logs to CA.', [], 'text')
							return 0	
						else:
							logger.debug( "line does not contain error message. Line = %s" % ( line ) )
					#check lines for watched text
	except Exception, err:
		logger.error( "Failed to monitor file %s. Reason: %s." % ( mc['src_file_path'], str(err) ) ) 
		traceback.print_exc()
		return 2
	return	
if __name__ == "__main__":
	sys.exit(main())

	
	
	
	