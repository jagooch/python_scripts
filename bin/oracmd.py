import ConfigParser
import argparse
import logging
import os
import sys
import traceback

import cx_Oracle

import asys

global logger
logging.basicConfig()
logger = logging.getLogger('Oracle CMD SQL Statement Utility')
logger.setLevel(logging.ERROR)


# @Version: 1.0
# @Author: John Gooch
# @Created: 20130401
# @Updated: 20151015
# @Name: Oracle Command line utility
# @Description: Connects to Oracle database and executes sql statements

# @tasks
# needs auth file load functions

def initCLI():
    parser = argparse.ArgumentParser(description='Queries the Oracle DB, outputs to global variabl, screen, and file.')
    parser.add_argument('-a', action="store", dest="auth_file_path", required=False, default=None,
                        help="Path to the authentication credentials file.")
    parser.add_argument('-q', action="store", dest="sql", required=False, default=None,
                        help="SQL to execute upon connection. This overrides the conf file contents.")
    parser.add_argument('-f', action="store", dest="sql_file_path", required=False, default=None,
                        help="SQL to execute upon connection. This overrides the conf file contents.")
    parser.add_argument('-d', action="store", dest="db_alias", required=True, help="Database alias.")
    parser.add_argument('-u', action="store", dest="db_user", required=False, help="Database user.")
    parser.add_argument('-p', action="store", dest="db_pwd", required=False, help="Database password.")
    parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None,
                        help="Global variable to store scalar results.")
    parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",
                        help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
    parser.add_argument('-o', action="store", dest="output_file_path", required=False, help="Database password.")
    args = parser.parse_args()
    return vars(args)


def initLogging(level):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    logger.setLevel(levels[level])
    return


# connect to database with supplied db alias and credentials
def connect(db_alias, db_user, db_pwd):
    logger.debug("Connecting to database alias %s as %s." % (db_alias, db_user))
    conn = cx_Oracle.connect("%s/%s@%s" % (db_user, db_pwd, db_alias))
    logger.debug("Successfully connected to database.")
    return conn


# Execute a query statement that returns a resultset
def execQuery(conn, sql, output_file_path=None, global_variable=None):
    logger.debug("Starting execQuery Query=%s output_file_path=%s" % (sql, output_file_path))
    rows = None
    curs = None
    outfile = None
    fields = None
    logger.debug("Connection to database successful.")
    curs = conn.cursor()
    logger.debug("Executing query %s" % (sql))
    curs.execute(sql)
    logger.debug("Fetching results of query.")
    rows = curs.fetchall()
    row_count = curs.rowcount
    if global_variable:
       if row_count > 0:
            asys.setGV(global_variable, rows[0][0])
       else:
            asys.setGV(global_variable, "NULL")
    logger.debug("%d rows fetched." % (len(rows)))
    if row_count == 0:
        logger.info("No matching records found.")
    else:
        field_names = []
        count = 0
        logger.debug("Collecting field names.")
        logger.debug("%d field names are in each record." % (len(curs.description)))
        for record in curs.description:
            logger.debug("Field name to add is %s.unt is %d" % (record[0], count))
            field_names.insert(count, record[0])
            logger.debug("Added Field named: %s to list" % (field_names[count]))
            count += 1
        fields = ','.join(field_names)
    curs.close()
    # print output to screen
    if row_count > 0:
        print "%s\n" % (fields)
        for row in rows:
            record = ','.join(map(str, row))
            print record
        if output_file_path:
            output_file = open(output_file_path, 'w')
            output_file.write("%s\n" % (fields))
            for row in rows:
                record = ','.join(map(str, row))
                output_file.write("%s\n" % (record))
            output_file.close()
    return 0


# Disconnect from the database.
def disconnect(conn):
    logger.debug("Disconnecting from database.")
    conn.close()
    logger.debug("Disconnected from database.")


def loadAuth(auth_file_path):
    if os.path.exists(auth_file_path) == False:
        logger.error(
            "Cannot access the authentication file %s. Please check the path and permissions." % (auth_file_path))
        raise Exception(
            "Cannot access the authentication file %s. Please check the path and permissions." % (auth_file_path))
    elif not os.path.isfile(auth_file_path):
        raise Exception(
            "Authentication file %s is not a valid file. Please check the path and permissions." % (auth_file_path))
    else:
        auth = ConfigParser.RawConfigParser()
        auth.read(auth_file_path)
        db_user = auth.get('main', 'db_user')
        db_pwd = auth.get('main', 'db_pwd')
        #return ( db_user, db_pwd)
        return dict( db_user = db_user , db_pwd = db_pwd )


def readSQLFile(sql_file_path):
    sql_file_path = os.path.realpath(sql_file_path)
    if not os.path.exists(sql_file_path):
        raise Exception("Cannot access sql file at %s." % (sql_file_path))
    elif not os.path.isfile(sql_file_path):
        raise Exception("Cannot access sql file at %s." % (sql_file_path))
    else:
        with open(sql_file_path, 'r') as f:
            sql = f.read()
        return sql


def main():
    mc = {}  # master config dictionary
    db_user = None
    db_pwd = None
    db_alias = None
    conn = None
    #parse the command line
    try:
        mc.update(initCLI())
    except Exception, err:
        traceback.print_exc()
        return 2
    #set the logging level
    try:
        initLogging(mc['level'])
    except Exception, err:
        print traceback.format_exc()
        return 2

    #load credentials from auth file if supplied
    if mc["auth_file_path"]:
        try:
            #(args.db_user, args.db_pwd) = loadAuth(args.auth_file_path)
            mc.update( loadAuth(mc["auth_file_path"]))
            logger.debug("Auth file %s loaded" % ( mc["auth_file_path"]) )
        except Exception, err:
            traceback.print_exc()
            return 2

    #load sql statement if sql file path was supplied
    if mc["sql_file_path"]:
        try:
            mc["sql"] = readSQLFile( mc["sql_file_path"])
        except Exception, err:
            logger.error("Exception encountered while reading %s sql file. Reason: %s" % (mc["sql_file_path"], str(err)))
            traceback.print_exc()
            return 2

    # remove semicolon from SQL because cx_Oracle does not recognize them as terminators
    mc["sql"] = mc["sql"].strip()
    if mc["sql"].endswith(';'):
        mc["sql"] = mc["sql"][:-1]
    # connect to the database with supplied credentials
    try:
        conn = connect( mc["db_alias"], mc["db_user"], mc["db_pwd"])
        if not conn:
            raise Exception("Failed to connect to database alias %s as %s"( mc["db_alias"], mc["db_user"]) )
        else:
            logger.debug("Connection object is %s" % (conn))
    except Exception, err:
        logger.error("Exception connecting to database. Reason: %s" % (str(err)))
        traceback.print_exc()
        return 2

    logger.debug("Executing sql statement %s." % ( mc["sql"]))
    try:
        execQuery(conn, mc["sql"], mc["output_file_path"], mc["global_variable"])
    except Exception, err:
        print traceback.format_exc()
        return 2

    # disconnect from the database
    try:
        disconnect(conn)
    except Exception, err:
        logger.error("Exception disconnecting from the database. Reason: %s." % (str(err)))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main());
