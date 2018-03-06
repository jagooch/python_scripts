#move_asys
import os
import sys
import argparse
import ConfigParser
import re
import logging

#special case modules
import glob
import cx_Oracle
import time
import string
import traceback
import urllib
#@Version: 1.0
#@Author: John Gooch
#@Created: 20130411
#@Updated:
#@Name: viewWorkbook
#@Description: Returns the URL of the workbook of the submitted job
#@ Tasks

global logger
logger = logging.getLogger('usercmd_RunBook')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)


def initCLI():
	parser = argparse.ArgumentParser(description='DC 834 Create CSV script v1.0')
	parser.add_argument('-u', action="store", dest="db_user", required=True, help="Database username.")
	parser.add_argument('-p', action="store", dest="db_pwd", required=True, help="Database password.")
	parser.add_argument('-d', action="store", dest="db_sid", required=True,help="Database service id(sid).")
	parser.add_argument('-l', action="store", dest="level", required=False, default="ERROR",help="Debug level. Default is ERROR")
	return vars(parser.parse_args())


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
		logger.debug("Running query %s" % query )
		curs.execute(query)
		row_count = curs.rowcount
		logger.info( "%d rows affected by query." % ( row_count ) )
		recordset = curs.fetchall()
		record_count = len(recordset)
		logger.info( "%d records retrieved." % ( record_count ) )
		if not record_count:
			return None
	except Exception, err:
		logger.error( "Failed to retrieve records. Reason: %s" % ( str(err) ) )
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
	# global logger
	# global conf
	# global args
	# global url
	# global ixp_home
	# global db_user
	# global db_pwd
	# global db_alias
	# global recordset
	# db_user = None"autosys"
	# db_pwd = "autosys"
	# db_alias = "asysdb_p1"
	recordset = None
	mc = {}


	try:
		mc.update( initCLI() )
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		initLogging(mc["level"])
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	mc["job_name"] = os.environ['IXP_USERCOMMAND_JOB_NAME']
	if not mc["job_name"]:
		print "ERROR: JOB NAME not supplied."
		return 2

	try:
		mc["url"] = getURL( mc["db_sid"], mc["db_user"], mc["db_pwd"], mc["job_name"] )
		if not mc["url"]:
			print "No workbook found for job %s. Contact the iXp administrator to have it added." % ( mc["job_name"] )
			return 2
		else:
			print mc["url"]
	except Exception, err:
		print "Failed to retrieve the job runbook url. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2
	return 0


if __name__ == "__main__":
	sys.exit(main());
