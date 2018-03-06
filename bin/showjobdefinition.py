#move_asys
import os
import sys
import logging
import traceback
import subprocess


#@Created By:
#@Created: 20140404
#@Updated:
#@Version 1.0
#@Description: Show Job Definition script
#@ 20140404 1.0 Created script.


def main():
	job_name = os.environ["IXP_USERCOMMAND_JOB_NAME"]
	if not job_name:
		return 2
	else:
		try:
			result = subprocess.call([ "autorep", "-J", job_name, "-q" ])
			if result > 1 :
				print "autorep command failed. EC=%d" % ( result )
				return result
		except Exception, err:
			traceback.print_exc()
			return 2

if __name__=="__main__":
	sys.exit( main() )
