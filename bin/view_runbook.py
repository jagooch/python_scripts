#move_asys
import os
import sys
import argparse
import ConfigParser
import re
import logging

global logger
logger = logging.getLogger('view_runbook')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)


#special case modules
import glob
import cx_Oracle
import time
import string
import traceback
import urllib

#@Version: 1.1
#@Author: John Gooch
#@Created: 20130411
#@Updated: 20140411
#@Name: viewWorkbook
#@Description: Returns the URL of the workbook of the submitted job
#@ Tasks
#@ 20130411 1.0 Converted script from perl to python
#@ 20140411 1.1 Updated to run crossplatform

def initCLI():
	parser = argparse.ArgumentParser(description='DC 834 Create CSV script v1.0')
	parser.add_argument('-l', action="store", dest="level", required=False, default="ERROR",help="Debug level. Default is ERROR")
	args = parser.parse_args()
	return args


def initLogging(logger, level):
	if not level:
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


def getURL( db_alias, db_user, db_pwd, job_name ):
	curs = None
	conn = None
	recordset = None
	query = """
				select
					url
				from
					aedbadmin.runbooks
				where
					job_name = '%s'
	""" % ( job_name )

	try:
		conn_string = "%s/%s@%s" % ( db_user, db_pwd, db_alias)
		conn = cx_Oracle.connect( "%s/%s@%s" % ( db_user, db_pwd, db_alias) )
		logger.info("Connection to database %s as %s user was successful." % ( db_alias, db_user  ) )
	except Exception, err:
		logger.error("Connection to database %s as %s user failed. Reason: %s" % ( db_alias, db_user, str(err)  ) )
		raise

	try:
		curs = conn.cursor()
		logger.info("Got cursor for database." )
	except Exception, err:
		logger.error("Failed to retrieve DB cursor. Reason: %s"  % (  str(err) ) )
		raise

	try:
		logger.debug("Querying ga_job_runs table.")
		curs.execute(query)
		row_count = curs.rowcount
		logger.info( "%d rows affected by query." % ( row_count ) )
		recordset = curs.fetchall()
		record_count = len(recordset)
		logger.info( "%d records retrieved from ga_job_runs table." % ( record_count ) )
		if not record_count:
			return None
	except Exception, err:
		logger.error( "Failed to retrieve records from ga_job_runs table. Reason: %s" % ( str(err) ) )
		raise

	try:
		curs.close()
		logger.info("Cursor closed." )
	except Exception, err:
		logger.error("Failed to close cursor. Reason: %s" % ( str(err) ) )
		raise
	try:
		conn.close()
		logger.info("DB connection closed." )
	except Exception, err:
		logger.error("Failed to close db connection. Reason: %s" % ( str(err) ) )
		raise
	return recordset[0][0]



	return url


def main():
	env = None
	args = None
	db_user = "autosys_db_ro"
	db_pwd = "autoro2014"
	db_alias = "prdora02"
	recordset = None
	url = None
	job_name = None

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
		initLogging(logger,args.level)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		env = os.environ.copy()
		job_name = env['IXP_USERCOMMAND_JOB_NAME']
		if not job_name:
			raise( "ERROR: JOB NAME not supplied." )
	except Exception, err:
		traceback.print_exc()
		return 2

	try:
		url = getURL( db_alias, db_user, db_pwd, job_name )
		if not url:
			print "No workbook found for job %s. Contact the iXp administrator to have it added." % ( job_name )
			return 2
		else:
			#print urllib.unquote( r )
			print url
	except Exception, err:
		print "Failed to retrieve the job runbook url. Reason: %s" % ( str(err) )
		traceback.format_exc()
		return 2


	return 0


if __name__ == "__main__":
	sys.exit(main());
