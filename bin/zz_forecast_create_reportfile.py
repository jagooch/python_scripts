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
from xlwt import Workbook,Font,Pattern,XFStyle,easyxf
from datetime import date, timedelta

#@Version: 1.0
#@Author: John Gooch
#@Created:  20130409
#@Updated:
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='script v1.0')
	parser.add_argument('-U', action="store", dest="db_user", required=True, help="Database username.")
	parser.add_argument('-P', action="store", dest="db_pwd",  required=True, help="Database password.")
	parser.add_argument('-D', action="store", dest="db_alias", required=True, help="Ddatabase alias.")
	parser.add_argument('-d', action="store", dest="dst_dir_path", default=".", required=False, help="Path to output Excel file")
	parser.add_argument('-f', action="store", dest="dst_file_name", required=False, help="Name of output Excel file")
	parser.add_argument('-o', action="store", dest="start_date", required=False, default=1, help="Date range for report.")
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

	#Queries the table and returns the sorted recordset
def collectReportData( db_alias,db_user, db_pwd ):
	curs = None
	conn = None
	recordset = None
	query = """ select
TO_CHAR ( SYSDATE, 'fmMM/DD') as DAY,
job_name,
case when instr(job.description, 'UC=') = '0' then ' ' else substr(job.description,instr(job.description,'UC=')+3, instr(job.description,';')-4) end as UC,
start_times,
start_mins,
case when job_status_codes.status = 'SUCCESS' THEN ' ' ELSE job_status_codes.status END AS STATUS
from
autosys.job join autosys.job_status on job.joid = job_status.joid
join  autosys.job_status_codes on job_status.status = job_status_codes.status_code
where
((days_of_week like ('%'||substr(to_char(sysdate,'dy'),1,2)||'%') or days_of_week like 'all')
and ((start_times > '08:00' and start_times < '24:00'))
and job_name not like 'zz%'
or job_name in (select job_name from autosys.job, autosys.calendar where job.run_calendar = calendar.name and substr(calendar.day,1,9) = substr(sysdate,1,9)  and job.start_times > '08:00' and job.start_times < '24:00')
) AND not exists (select job.job_name from autosys.job, autosys.calendar where job.exclude_calendar = calendar.name and substr(calendar.day,1,9) = substr(sysdate,1,9) and job.start_times > '08:00' and start_times < '24:00')
union
select
TO_CHAR ( SYSDATE+1, 'fmMM/DD') as DAY,
job_name,
case when instr(job.description, 'UC=') = '0' then ' ' else substr(job.description,instr(job.description,'UC=')+3, instr(job.description,';')-4) end as UC,
start_times,
start_mins,
case when job_status_codes.status = 'SUCCESS' THEN ' ' ELSE job_status_codes.status END AS STATUS
from
autosys.job join autosys.job_status on job.joid = job_status.joid
join  autosys.job_status_codes on job_status.status = job_status_codes.status_code
where
((days_of_week like ('%'||substr(to_char(sysdate+1,'dy'),1,2)||'%') or days_of_week like 'all')
and ((start_times > '00:00' and start_times <= '08:00'))
and job_name not like 'zz%'
or job_name in (select job_name from autosys.job, autosys.calendar where job.run_calendar = calendar.name and substr(calendar.day,1,9) = substr(sysdate+1,1,9)  and job.start_times > '00:00' and job.start_times <= '08:00')
) AND not exists (select job.job_name from autosys.job, autosys.calendar where job.exclude_calendar = calendar.name and substr(calendar.day,1,9) = substr(sysdate,1,9) and job.start_times > '00:00' and start_times <= '08:00')
union

select
'Both' AS DAY,
job_name,
case when instr(job.description, 'UC=') = '0' then ' ' else substr(job.description,instr(job.description,'UC=')+3, instr(job.description,';')-4) end as UC,
start_times,
start_mins,
case when job_status_codes.status = 'SUCCESS' THEN ' ' ELSE job_status_codes.status END AS STATUS
from
autosys.job join autosys.job_status on job.joid = job_status.joid
join  autosys.job_status_codes on job_status.status = job_status_codes.status_code
where
((days_of_week like ('%'||substr(to_char(sysdate+1,'dy'),1,2)||'%') or days_of_week like 'all')
and start_mins is not null)
and job_name not like 'zz%'
AND not exists (select job.job_name from autosys.job, autosys.calendar where job.exclude_calendar = calendar.name and substr(calendar.day,1,9) = substr(sysdate,1,9) and job.start_times > '00:00' and start_times < '24:00')
order by DAY ASC, START_TIMES ASC"""

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
		logger.error("Failed to retreive DB cursor. Reason: %s"  % (  str(err) ) )
		raise

	try:
		logger.debug("Querying table.")
		curs.execute(query)
		row_count = curs.rowcount
		logger.info( "%d rows affected by query." % ( row_count ) )
		recordset = curs.fetchall()
		record_count = len(recordset)
		logger.info( "%d records retrieved from table." % ( record_count ) )
	except Exception, err:
		logger.error( "Failed to retrieve records from table. Reason: %s" % ( str(err) ) )
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
	return recordset


def getDefaultFileName( start_date):
	report_date_text = start_date
	report_file_name = "Operations_Forecast_%s.xls" % ( report_date_text )
	return report_file_name

def createSpreadsheet( recordset, dst_dir_path, dst_file_name ):
	dst_dir_path = os.path.realpath( dst_dir_path )
	logger.debug( "opening new workbook at %s" % ( os.path.join( dst_dir_path, dst_file_name  ) ) )
	if not os.path.exists( dst_dir_path ):
		logger.error( "Destination path %s does not exist. Error: %s" % ( dst_dir_path ) )
		raise Exception("Destination path %s does not exist." % ( dst_dir_path ) )
	# Start some Excel magic
	wb = Workbook()
	ws0 = wb.add_sheet('Forecast')
	ws0.set_panes_frozen(True)
	ws0.set_horz_split_pos(1)
	logger.debug( "Workbook created with name 'Forecast'" )

	#0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = Yellow, 6 = Magenta, 7 = Cyan, 16 = Maroon, 17 = Dark Green, 18 = Dark Blue, 19 = Dark Yellow , almost brown), 20 = Dark Magenta, 21 = Teal, 22 = Light Gray, 23 = Dark Gray
	#Create the default font
	defaultFont = Font()
	defaultFont.name = 'Arial'
	defaultFont.bold = False
	defaultFont.size = 10

	#create the default Pattern
	defaultPattern  = Pattern()

	#create the default style
	defaultStyle = XFStyle()
	defaultStyle.font = defaultFont

	#Create the failure font
	failureFont = Font()
	failureFont.name = 'Arial'
	failureFont.bold = True
	failureFont.size = 10
	failureFont.colour = 'red'

	#create the failure Pattern
	failurePattern = Pattern()
	failurePattern.pattern = Pattern.SOLID_PATTERN
	failurePattern.pattern_fore_colour = 2

	#Create the failure style
	#failureStyle = XFStyle()
	#easyxf( 'font: colour red, bold True, size 10, name Arial;')
	#failureStyle.font = failureFont
	#failureStyle.pattern = failurePattern
	failureStyle = easyxf('font: bold 1, name Arial , height 200, color red;')


	#create the failure Pattern
	runningPattern = Pattern()
	runningPattern.pattern = Pattern.SOLID_PATTERN
	runningPattern.pattern_fore_colour = 3

	#Create a running style
	runningStyle = XFStyle()
	runningStyle.font = defaultFont
	runningStyle.pattern = runningPattern

	# Grey background for the header row
	headerPattern = Pattern()
	headerPattern.pattern = Pattern.SOLID_PATTERN
	headerPattern.pattern_fore_colour = 22

	# Bold Fonts for the header row
	headerFont = Font()
	headerFont.name = 'Arial'
	headerFont.bold = True
	headerFont.size = 10

	# style and write field labels
	headerStyle = XFStyle()
	headerStyle.font = headerFont
	headerStyle.pattern = headerPattern

	logger.debug( "Writing data to worksheet." )

	row_number=1
	col_width_dict = dict()
	for i in range(8):
		col_width_dict[i] = 0
	for record in recordset:

		currentStyle = defaultStyle
		# if str(record[4]).upper() == "FAILURE":
			# logger.debug( "Status %s is in FAILURE" % ( str(record[5] ) ) )
			# currentStyle = failureStyle
		# elif str(record[4] ).upper() == "RUNNING":
			# logger.debug( "Status %s is in RUNNING" % ( str(record[5] ) ) )
			# currentStyle = runningStyle

		column = 0
		for field in record: #i.e. for each field in the record
			logger.debug( "Writing data field %s to worksheet" % ( str(field) ) )
			if field:
				ws0.write(row_number,column,str(field), currentStyle)  #write excel cell from the cursor at row 1
			else:
				ws0.write(row_number,column,"", currentStyle)  #write excel cell from the cursor at row 1
			if len(str(field)) > col_width_dict[column]:
				#only redefine the column width if we need it to be bigger
				col_width_dict[column] = len(str(field))
			ws0.col(column).width = len(str(field))*256
			ws0.col(column).width = col_width_dict[column]*256
			column = column +1  #increment the column to get the next field
		row_number += 1

	logger.debug( "Writing header row to worksheet." )
	ws0.write(0,0,'DAY',headerStyle)
	ws0.col(0).width = 10*256
	ws0.write(0,1,'JOB NAME',headerStyle)
	ws0.write(0,2,'UC',headerStyle)
	ws0.col(2).width = 17*256
	ws0.write(0,3,'START TIME',headerStyle)
	ws0.write(0,4,'PERIODICALLY',headerStyle)
	ws0.col(4).width = 16*256
	ws0.write(0,5,'STATUS',headerStyle)
	ws0.col(5).width = 11*256
	logger.debug( "Writing excel file %s" % (os.path.join( dst_dir_path, dst_file_name )) )
	wb.save( os.path.join( dst_dir_path, dst_file_name ))
	return 0


def main():
	global logger
	global conf
	global args
	global recordset
	global report_file_name

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

	try:
		recordset = collectReportData( args.db_alias, args.db_user, args.db_pwd )
	except Exception,err:
		logger.error( "Failed to collect report data from table. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	if not args.dst_file_name:
		try:
			report_file_name = getDefaultFileName( args.start_date )
		except Exception, err:
			logger.error( "Failed to create default report name. Reason: %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	else:
		report_file_name = args.dst_file_name

	try:
		createSpreadsheet( recordset, args.dst_dir_path, report_file_name )
		logger.info( "Successfully created Excel spreadsheet %s." % ( report_file_name ) )
	except Exception,err:
		logger.error( "Failed to write the Excel spreadsheet %s. Reason: %s" % ( args.dst_dir_path,str(err) ) )
		traceback.print_exc()
		return 2

	return 0

if __name__ == "__main__":
	sys.exit(main());
