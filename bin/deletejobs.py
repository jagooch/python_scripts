import os
import sys
import argparse
import ConfigParser
import re
import logging
import asys
import traceback

#special case modules
import glob
import time
import string
import subprocess
import datetime

#@Version: 1.1
#@Author: John Gooch
#@Created: 20130830 
#@Updated: 20140210 - John Gooch
#@Name: Delete Jobs Script 
#@Description: Deletes Autosys jobs.
#@ Tasks
#20140210 1.2 Fixed cutoff job name issue by adding the -w switch to autorep


def initCLI():
	parser = argparse.ArgumentParser(description='Python Script Template v1.0')
	parser.add_argument('-j', action="store", dest="jobname", required=True, help="Job/Box name to delete.")
	parser.add_argument('-i', action="store_true", dest="iterate", required=False, default=False,help="Enable iterative job deletion.")
	parser.add_argument('-e', action="store_true", dest="error", required=False, default=False,help="Error if no jobs are deleted.")
	parser.add_argument('-a', action="store", dest="archive_dir_path", required=False, default=None,help="Path to store archive files of deleted jobs.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return args

	
def initLogging(args):
	global logger
	logger = logging.getLogger()
	if not args.level:
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
	return logger

def getJobs( jobname, iterate ):
	jobs = []
	cmd = None
	if iterate:
		cmd = ["autorep", "-J", jobname, "-w" ]
		logger.debug( "Iterate enabled. cmd = %s" % ( " ".join( cmd ) ) )
	else:
		cmd = ["autorep", "-J", jobname, "-l", "0", "-w" ]
		logger.debug( "Iterate disabled. cmd = %s" % ( " ".join( cmd ) ) )
	stdout = subprocess.check_output( cmd )
	lines = ( stdout.split( '\n' ) )[3:]
	for line in lines:
		#line = line.strip()
		logger.debug( "Processing line %s" % ( line ) )
		jobname = line.strip().split(' ',2)[0]
		if not jobname:
			logger.debug( "Name %s is not a valid jobname." % ( jobname ) )
			continue
		logger.debug( "Found job %s." % ( jobname ) )
		jobs.append( jobname )
		logger.debug( "added job name %s." % ( jobname ))
	if not len(jobs):
		return None
		#raise Exception( "No jobs found." )
	else:
		logger.debug( "%d jobs found." % ( len(jobs) ) )
		return jobs
	
def deleteJobs( jobs ):
	delete_count = 0
	logger.debug( "Deleting %d jobs." % ( len(jobs ) ))
	for job in jobs:
		logger.debug( "Deleting job %s." % ( job ) )
		deletejob( job )
		logger.info( "Deleted job %s." % ( job ) )
		delete_count += 1
	logger.info( "%d jobs successfully deleted." % ( delete_count ) )
	return 0

def archiveJob( jobname, archive_dir_path ):
	archive_dir_path = os.path.realpath( archive_dir_path )
	timestamp = datetime.datetime.now().strftime( "%Y%m%d%H%M%S%f" )
	archive_file_name = "deletejobs_archive_%s.jil" % ( timestamp )
	archive_file_path = os.path.join( archive_dir_path, archive_file_name )
	if not os.path.exists( archive_dir_path ):
		raise Exception( "Archive directory %s is not accessible or does not exist. Check path and try again." % ( archive_dir_path) )
	elif not os.path.isdir( archive_dir_path ):
		raise Exception( "Archive directory %s is not a directory. Check path and try again." % ( archive_dir_path) )
	else:
		cmd = "autorep -j %s -q > %s" % ( jobname, archive_file_path)
		logger.debug( "Archiving job cmd = %s " %  ( cmd ) )
		output = subprocess.call( cmd, shell=True ) 
		logger.debug( output )
		logger.debug( "%s successfully archived" % ( jobname ) ) 
		return archive_file_path

	
def deletejob( jobname ):
	cmd = "echo delete_job: %s | jil"  % ( jobname ) 
	logger.debug( "Delete job cmd = %s " %  (  cmd ) )
	output = subprocess.call( cmd, shell=True ) 
	logger.debug ( output )
	#logger.info( "%s successfully deleted" % ( jobname ) ) 
	return 0

def main():
	global logger
	global conf
	global args
	joblist = None
	
	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
		
	#create a list of jobs to delete
	try:
		jobs = getJobs( args.jobname, args.iterate )
	except Exception, err:
		logger.error("Failed to retrieve list of jobs. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	if not jobs:
		if args.error:
			return 1
		else:
			return 0

	if args.archive_dir_path:
		try:
			archive_file_path = archiveJob( args.jobname, args.archive_dir_path )
			logger.info( "Archived job %s to %s" % ( args.jobname, archive_file_path ) ) 
		except Exception, err:
			print "Failed to archive jobs. Reason: %s" % ( str(err) ) 
			traceback.print_exc()
			return 2
			
			
	try:
		deleteJobs( jobs )
	except Exception, err:
		print "Failed to delete jobs. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	return 0


if __name__ == "__main__":
	sys.exit(main());





