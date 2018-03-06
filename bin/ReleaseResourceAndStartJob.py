import os
import sys
import logging
import traceback
from subprocess import Popen,PIPE, call
#@Created By: John Gooch
#@Created: 20141104
#@Updated: 
#@Version 1.1
#@Description: Job Release Resouce and Start Job script
#@ 20141104 1.0 Created script.


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
		cmd = [ 'sendevent','-E', 'RELEASE_RESOURCE', '-J', '%s' % ( job_name ) ]
		print "Executing command %s" % ( " ".join( cmd ) )	
		p = Popen( cmd, shell=False, stdout=PIPE, stderr=PIPE )
		stdout, stderr = p.communicate()
		returncode = p.returncode
		if not returncode == 0:
			raise Exception( "Unable to release resource for job %s. EC=%d. Reason: %s %s" % ( job_name, returncode, stdout, stderr ) )
		else:
			print "job update succeeded. EC=%d" % ( returncode ) 
	except Exception, err:
		traceback.print_exc()
		return 2

	try:
		cmd = [ 'sendevent','-E', 'STARTJOB', '-J', '%s' % ( job_name ) ]
		p = Popen( cmd, shell=False,stdout=PIPE, stderr=PIPE )
		stdout, stderr = p.communicate()
		returncode = p.returncode
		if not returncode == 0:
			raise Exception( "Failed to start job %s. EC=%d. Reason: %s %s" % ( job_name, returncode, stdout, stderr ) )
		else:
			print "Job %s started. EC=%d" % ( job_name, returncode ) 
	except Exception, err:
		traceback.print_exc()
		return 2
			
if __name__=="__main__":
	sys.exit( main() )

