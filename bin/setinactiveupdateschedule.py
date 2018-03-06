#move_asys
import os
import sys
import logging
import traceback
from subprocess import Popen,PIPE,call
#@Created By: John Gooch
#@Created: 20140404
#@Updated: 20140411
#@Version 1.1
#@Description: Job Change Status and Set Inactive script
#@ 20140411 1.1 Fixed update job function .
#@ 20140404 1.0 Created script.


def main():
	job_name = None
	env = None
	try:
		env = os.environ.copy()
		job_name = env["IXP_USERCOMMAND_JOB_NAME"]
		if not job_name:
			raise Exception( "Processing job %s." % ( job_name )  )
		else:
			print "Processing job %s." % ( job_name )
	except Exception, err:
		traceback.print_exc()
		return 2

	try:
		result = call( "echo update_job: %s | jil" % ( job_name ) , env=env, shell=True )
		print "result=%d" % ( result )
		if result > 0 :
			raise Exception( "job update for job %s failed. EC=%d" % ( job_name, result ) )
		else:
			print "job update succeeded. EC=%d" % ( result )
	except Exception, err:
		traceback.print_exc()
		return 2

	try:
		result = call( "sendevent -E CHANGE_STATUS -s INACTIVE -J %s" % ( job_name ), env=env, shell=True )
		print "result=%d" % ( result )
		if result > 0 :
			raise Exception( "autorep command failed. EC=%d" % ( result ) )
		else:
			print "autorep command succeeded. EC=%d" % ( result )
			result = call( "autorep -J %s" % ( job_name ), env=env, shell=True )
			return 0
	except Exception, err:
		traceback.print_exc()
		return 2

if __name__=="__main__":
	sys.exit( main() )
