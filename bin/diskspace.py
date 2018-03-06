import os
import sys
import ConfigParser
import argparse
import re
import logging
import glob
import traceback
import collections
import subprocess


#@Version: 1.1 
#@Author: John Gooch
#@Created: 20130205
#@Updated: 20130206
#@Name: Disk Space Properties Script 
#@Description: Report the specified disk space property and places value into a global variable(optional)
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Disk Space properties v1.0')
	parser.add_argument('-v', action="store", dest="volume", required=True, help="Volume name/path to analyze.")
	parser.add_argument('-t', action="store", dest="type", required=True, help="Type of property to report. AVAIL, USED, TOTAL, ALL.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None, help="Global variable to store statistic in.")
	parser.add_argument('-u', action="store", dest="units", required=False, default=None, help="Units of measure for outut. k=kB, m=MB, g=GB,t=TB.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO. DEBUG,INFO,and ERROR are valid.")
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

def setGV(gvar, value ):
	cmd = None
	if value:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	else:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=DELETE" % ( gvar )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd ) 
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		raise
	else:
		if returncode != 0:
			raise Exception( "Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		else:
			if value:
				logger.debug("Successfully set global variable  %s = %s" %  ( gvar, value ) )
			else:
				logger.debug("Successfully DELETED global variable %s." %  ( gvar ) )
			return 0
	
	
def diskspace( volume ):
	_ntuple_diskusage = collections.namedtuple('usage', 'total used free')
	if hasattr(os, 'statvfs'):  # POSIX
		def disk_usage(path):
			st = os.statvfs(path)
			free = st.f_bavail * st.f_frsize
			total = st.f_blocks * st.f_frsize
			used = (st.f_blocks - st.f_bfree) * st.f_frsize
			return _ntuple_diskusage(total, used, free)

	elif os.name == 'nt':       # Windows
		import ctypes
		import sys

		def disk_usage(path):
			_, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), \
							   ctypes.c_ulonglong()
			if sys.version_info >= (3,) or isinstance(path, unicode):
				fun = ctypes.windll.kernel32.GetDiskFreeSpaceExW
			else:
				fun = ctypes.windll.kernel32.GetDiskFreeSpaceExA
			ret = fun(path, ctypes.byref(_), ctypes.byref(total), ctypes.byref(free))
			if ret == 0:
				raise ctypes.WinError()
			used = total.value - free.value
			return _ntuple_diskusage(total.value, used, free.value)
	else:
		raise NotImplementedError("platform not supported")	
	return disk_usage(volume)


def humanized_bytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024*123)
    '123.0 kB'
    >>> humanize_bytes(1024*12342)
    '12.1 MB'
    >>> humanize_bytes(1024*12342,2)
    '12.05 MB'
    >>> humanize_bytes(1024*1234,2)
    '1.21 MB'
    >>> humanize_bytes(1024*1234*1111,2)
    '1.31 GB'
    >>> humanize_bytes(1024*1234*1111,1)
    '1.3 GB'
    """
    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'kB'),
        (1, 'bytes')
    )
    if bytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)

def format_bytes( bytes, units ):
	if not units:
		logger.debug( "Bytes = %d" % ( bytes) )
		return bytes
	elif units in "k":
		logger.debug( "Bytes = %d, kilobytes = %d" % ( int(bytes), bytes / ( 1024**1 ) ) )
		return int(bytes/1024**1 )
	elif units in "m":
		logger.debug( "Bytes = %d, megaytes = %d" % ( int(bytes), bytes / ( 1024**2 ) ) )
		return int( bytes / 1024**2 )
	elif units in "g":
		logger.debug( "Bytes = %d, gigabytes = %d" % ( int(bytes), bytes / ( 1024**3 ) ) )
		return int( bytes / ( 1024**3 ) )
	elif units in "t":
		logger.debug( "Bytes = %d, terabytes = %d" % ( int(bytes), bytes / ( 1024**4 ) ) )
		return int( bytes /(1024**4 ) )
	else:
		raise Exception( "Invalid Unit %s specified. Check input." % ( units ) )
	
	
def main():
	global logger
	global conf
	global args
	global stats
	global stat
	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2

	try:
		stats = diskspace( args.volume )
	except Exception, err:
		print "Failed to collect disk statistics from %s. Reason: %s" % ( args.volume , str(err) ) 
		traceback.format_exc()
		return 2
	( total_bytes, used_bytes, avail_bytes ) = stats
	#total.value, used, free.value
	if args.type in "AVAIL":
		stat = avail_bytes
		logger.info("AVAIL=%s"  % ( humanized_bytes(avail_bytes) ) )
		#print "AVAIL=%s"  % ( humanized_bytes(avail_bytes) )
	elif args.type in "USED":
		stat = used_bytes
		logger.info("USED=%s"  % ( humanized_bytes(used_bytes) ) )
		#print "USED=%s"  % ( humanized_bytes(used_bytes) )
	elif args.type in "TOTAL":
		stat = total_bytes
		logger.info("TOTAL=%s"  % ( humanized_bytes(total_bytes) ) )
		#print "TOTAL=%s"  % ( humanized_bytes(total_bytes) )
	elif args.type in "ALL":
		logger.error( "Stat type %s not implemented." % ( args.type) )
		return 2
	else:
		logger.error( "Stat type %s not recognized." % ( args.type) ) 
		return 2
		
	if args.global_variable:
		formatted_stat = format_bytes( stat, args.units )
		try:
			setGV( args.global_variable, formatted_stat )
			logger.debug( "Global variable %s set to %s . Units = %s" % (  args.global_variable, formatted_stat, args.units   ))
		except Exception, err:
			logger.error("Failed to set global variable %s = %d . Reason: %s" % ( args.global_variable, stat, str(err) ) )
			traceback.format_exc()
			return 2
	return 0


if __name__ == "__main__":
	sys.exit(main());





