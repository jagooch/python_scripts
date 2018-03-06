#move_asys
import ConfigParser
import argparse
import datetime
import logging
import logging.handlers
import os
import re
import socket
import subprocess
import sys
import time
import traceback
import sendmail

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter( formatter )
ch.setLevel( logging.DEBUG )
logger = logging.getLogger(__name__)
logger.addHandler( ch )
logger.propagate = False
logger.debug( "logging level and format configured ")

version = "3.8"
description = "Uses autosys  commands to monitor the health of database connect, event processor health, and remote agent health."

levels = {"DEBUG": logging.DEBUG,
          "INFO": logging.INFO,
          "WARNING": logging.WARNING,
          "ERROR": logging.ERROR,
          "CRITICAL": logging.CRITICAL
          }

service_names =  {
   'waae_agent-WA_AGENT':'Remote Agent Service',
    'waae_sched':'Scheduler Service',
    'waae_server':'Applicatin Gateway Service',
    'waae_webserver':'Web Services Service'
}


def getServiceName( service_name ):
    logger.debug( "getting service name for %s" % ( service_name)   )
    parts = service_name.split('.')
    parts[0] = service_names[parts[0]]
    hr_service_name = " ".join(parts)
    return hr_service_name



def initCLI():
    parser = argparse.ArgumentParser(description='AutoSys Monitor - checks the health of Autosys components.')
    parser.add_argument('--version', action='version', version='%(prog)s 4.0')
    parser.add_argument('-c', action="store", dest="config_file_path", required=False,
                        help='Path to the configuration file.')
    parser.add_argument('-l', action="store", dest="level", default="INFO", required=False,
                        help="Sets the logging level for the script. Default is INFO")
    parser.add_argument('-d', action="store", dest="autoping_delay", required=False, default=3, type=int,
                        help="Sets the delay between autoping retries.")
    parser.add_argument('-p', action="store", dest="port", required=False, default=25, type=int, help="SMTP Port.")
    parser.add_argument('-s', action="store", dest="server", required=False, help="SMTP mail server.")
    parser.add_argument('-f', action="store", dest="sender", required=False, default="autosys_alert@policy-studies.com",
                        help="Email from address.")
    parser.add_argument('-t', action="store", dest="recipients", required=False, help="Email To address(es).")
    parser.add_argument('-a', action="store", dest="attachment_file_path", required=False, type=list, default=[], help="(Optional) Comma-separated list of file attachment paths.")
    parser.add_argument('-r', action="store", dest="autoping_retries", required=False,help="Retry threshold for autoping.")
    parser.add_argument('-v', action="store_true", dest="verbose", required=False, help="Display verbose test results output.")
    parser.add_argument('--logdir', action="store", dest="log_file_path", required=False,help="Directory path for log files.")
    parser.add_argument('--remote_agent_list', action="store", dest="remote_agent_list_path", required=False,help="Path to remote agent list.")
    return vars(parser.parse_args())


def initLogging(level):
    logger.setLevel(levels[level])
    return


def loadConfig(config_file_path):
    # load global variable values from configuration file
    logger.debug("Loading configuration file %s" % (config_file_path))
    if (os.path.exists(config_file_path) == False):
        raise Exception("Failed to open configuration file %s. Please check path and permissions." % (config_file_path))
    config = ConfigParser.RawConfigParser()
    config.read(config_file_path)
    return dict(config.items('main'))


# checks individual Autosys services which should be running on the local system
def chk_services(hostname, str_services ):
    subject = None
    body = None
    service_down = []
    # list of services to check -
    services = sorted( str_services.split(','))
    cmd = "/opt/CA/SharedComponents/bin/ustat"
    for service in services:
        logger.debug( "Test: Is %s service running." % ( getServiceName(service) ) )
        p = subprocess.Popen([ cmd, service ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()
        if p.returncode != 0:
            service_down.append( service_down)
            logger.debug( "Result: %s service is not running on %s." % ( getServiceName(service), hostname  ) )

            body = xstr(body) + "Service: %s is not running on %s.\n" % (  getServiceName(service), hostname  )
        else:
            logger.debug( "Result: %s service is running on %s." % ( getServiceName(service), hostname ) )

    if body:
        body += "Open https://tech.sp.maxcorp.maximus/teams/itautomation/Shared%20Documents/Workbooks/ASYS_APPLICATION_WORKBOOK.docx?Web=1 using Internet Explorer for troubleshooting and recovery instructions.\n"
        subject = "FAILURE - ASYS - [%s] %d Core Services Down on %s." % (hostname, len( service_down ), hostname)
        return ( subject, body )
    else:
        return None

#checks the event servers health - exit code is the sum of es's that are up. eg 1 server = ec 1, 2 servers = 2
def chk_auto_up(healthy_exit_code, hostname):
    logger.debug( "Checking database status"  )
    p = subprocess.Popen(["/opt/CA/WorkloadAutomationAE/autosys/bin/chk_auto_up", "-r1"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    exit_code = p.poll()
    if exit_code == healthy_exit_code:
        logger.info( "Autosys Database up. Primary EP up. Shadow EP up. Scheduler service is up. Exit Code: %d. Desired Exit Code: %d" % ( exit_code, healthy_exit_code))
        return 0
    else:
        subject = "FAILURE - AUTOSYS - [%s] Event Servers Down at %s" % ( hostname,  (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M") )
        body = "chk_auto_up detected that %d event servers out of %d are not responding. Please investigate." %  (  ( exit_code - healthy_exit_code ),healthy_exit_code )
        body = xstr(body) + "Open https://tech.sp.maxcorp.maximus/teams/itautomation/Shared%20Documents/Workbooks/ASYS_APPLICATION_WORKBOOK.docx?Web=1 using Internet Explorer for troubleshooting and recovery instructions.\n"
        return ( subject, body)


# load agent list and settings from the remote agent list file
def loadAgents(remote_agent_list_path, agent_retries):
    agents = []
    # str_remote_agent_errors = ""
    fail_count = 0
    if os.path.exists(remote_agent_list_path) == False:
        raise Exception(
            "Cannot access the Remote Agent Ping list at %s. Check the config file, permissions, and the file path." % (
                remote_agent_list_path))

    # file = open( remote_agent_list_path , "r")
    lines = [line.strip() for line in open(remote_agent_list_path, 'r')]

    for line in lines:
        if line.startswith("#"):
            continue
        elif not line:
            continue
        else:
            # Create empty agent dictionary object
            logger.debug("Processing agent line %s." % (line))
            agent = {}
            fields = line.split(",")
            field_count = len(fields)
            if field_count != 3:
                raise Exception("Remote Agent list format error. The offending line is %s" % (line))
            else:
                agent = {}
                agent['agent_name'] = fields[0]
                agent['agent_enabled'] = fields[1]
                if fields[2]:
                    agent['agent_retries'] = int(fields[2])
                else:
                    agent['agent_retries'] = agent_retries

                agent['basic'] = "SKIPPED"
                agent['basic_latency'] = 0
                agent['database'] = "SKIPPED"
                agent['database_latency'] = 0
                agent['autoping_basic_retries'] = 0
                agent['autoping_database_retries'] = 0

                if agent['agent_enabled'] != "enabled":
                    logger.info("Monitoring is not enabled for Remote Agent %s. Skipping..." % (agent['agent_name']))
                    continue
                else:
                    agents.append(agent)
                    logger.debug("Agent %s added to agents list. Enabled value is: %s. Retry threshold is %d." % (
                        agent['agent_name'], agent['agent_enabled'], agent['agent_retries']))
    return agents


# Iterate through agent list and run autoping on each one
def autoping_agents(agents, autoping_delay, hostname):
    agents_failed = []
    # run autoping test against the agents list
    for agent in agents:
        logger.debug("Service testing agent %s" % (agent['agent_name']))
        attempts = 0
        latency_time = None  # time it takes to execute a command , given in seconds
        passed = False
        # perform basic connectivity test
        while True:
            start_time = datetime.datetime.now()
            p = subprocess.Popen(["/opt/CA/WorkloadAutomationAE/autosys/bin/autoping", "-m", agent['agent_name']],
                                 stdout=subprocess.PIPE)
            out, err = p.communicate()
            stop_time = datetime.datetime.now()
            latency_time = stop_time - start_time
            # print "Start time %s \nStop Time %s \nLatency Time: %s\n" %  ( start_time, stop_time, latency_time   )
            exit_code = p.poll()
            if exit_code != 0:
                logger.debug("Failed attempt %d. Sleeping %d seconds. %d attempts left" % (
                    (attempts + 1), autoping_delay, (agent['agent_retries'] - attempts)))
                if attempts == agent['agent_retries']:
                    break
                else:
                    agent['autoping_basic_retries'] += 1
                    attempts += 1
                    time.sleep(autoping_delay)
            else:
                passed = True
                break

        # set the agent's latency value
        agent['basic_latency'] = ((latency_time.seconds * 1000) + (latency_time.microseconds / 1000))

        if passed == True:
            agent['basic'] = "PASSED"
            logger.debug("Agent %s - Service Test: Status[%s] Latency[%0.2f]ms Retries[%d]." % (
                agent['agent_name'], agent['basic'], agent['basic_latency'], agent['autoping_basic_retries']))
        else:
            # log agent failure and continue on to next agent
            agent['basic'] = "FAILED"
            agents_failed.append(agent)
            continue

        # perform database test
        attempts = 0
        passed = False
        latency_time = None
        while True:
            start_time = datetime.datetime.now()
            p = subprocess.Popen(["/opt/CA/WorkloadAutomationAE/autosys/bin/autoping", "-m", agent['agent_name'], "-S"],stdout=subprocess.PIPE)
            out, err = p.communicate()
            stop_time = datetime.datetime.now()
            latency_time = stop_time - start_time
            # print "Start time %s \nStop Time %s \nLatency Time: %s\n" %  ( start_time, stop_time, latency_time   )
            exit_code = p.poll()
            if exit_code != 0:
                time.sleep(autoping_delay)
                attempts += 1
                if attempts == agent['agent_retries']:
                    break
                else:
                    agent['autoping_database_retries'] += 1
            else:
                passed = True
                break

        # set the agent's latency value
        agent['database_latency'] = (latency_time.seconds + latency_time.microseconds / 1000000)

        # update agents db test status
        if passed == True:
            agent['database'] = "PASSED"
            logger.debug("Agent %s - DB Test: Status[%s] Latency[%0.2f]s Retries[%d]." % ( agent['agent_name'], agent['database'], agent['database_latency'], agent['autoping_database_retries']))
        else:
            agent['database'] = "FAILED"
            agents_failed.append(agent)
            logger.debug("Agent %s - DB Test: Status[%s] Latency[%0.2f]s Retries[%d]." % ( agent['agent_name'], agent['database'], agent['database_latency'], agent['autoping_database_retries']))
            continue

    if len(agents_failed):
        body = ""
        for agent in agents_failed:
            body = body + "Agent %s - Service Test: Status[%s]  Latency[%0.2f]ms Retries[%d]  AppGW Test: Status[%s] Latency[%0.2f]s Retries[%d].\n" % ( agent['agent_name'], agent['basic'], agent['basic_latency'], agent['autoping_basic_retries'],  agent['database'], agent['database_latency'], agent['autoping_database_retries'])
            logger.error("FAILURE - AUTOSYS - Autoping Failure at %s - %d Agents Failed.[%s]" % ((datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), len(agents_failed), hostname))
        for line in body.split('\n'):
            logger.error("%s" % (line))
        subject = "FAILURE - AUTOSYS - Autoping Failure at %s - %d Agents Failed.[%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), len(agents_failed), hostname)
        body = body + "Open https://tech.sp.maxcorp.maximus/teams/itautomation/Shared%20Documents/Workbooks/ASYS_APPLICATION_WORKBOOK.docx?Web=1 using Internet Explorer for troubleshooint and recovery instructions.\n"
        return (subject, body)
    else:
        logger.info("All Remote Agents passed the Autoping test.")
        return None


def shell_source(script):
    """Sometime you want to emulate the action of "source" in bash,
    settings some environment variables. Here is a way to do it."""
    logger.debug(" Sourcing environment %s"  % ( script  ) )
    pipe = subprocess.Popen("source %s; env" % script, stdout=subprocess.PIPE, shell=True)
    output = pipe.communicate()[0]
    env = dict((line.split("=", 1) for line in output.splitlines()))
    os.environ.update(env)


def initLogFile(log_file_path):
    # this is a one-off, but if the config file specifies a log file path, then add and use it.
    log_file_dirname = os.path.dirname(log_file_path)
    if not os.path.exists(log_file_dirname):
        raise Exception("Cannot access logging directory %s.  Please check path and permissions." % (log_file_dirname))
    else:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh = logging.handlers.TimedRotatingFileHandler(log_file_path, when='D', interval=1, backupCount=3, encoding=None, delay=False, utc=False)
        fh.setFormatter(formatter)
        logger.addHandler(fh)


# prints comprehensive results of Autoping tests
def autopingReport(agents):
    logger.info("Start Autoping Report")
    for agent in agents:
        logger.info(
            "Agent %s - Service Test: Status[%s]  Latency[%0.2f]ms Retries[%d]  AppGW Test: Status[%s] Latency[%0.2f]s Retries[%d]." % ( agent['agent_name'], agent['basic'], agent['basic_latency'], agent['autoping_basic_retries'], agent['database'], agent['database_latency'], agent['autoping_database_retries']))
    logger.info("End Autoping Report")
    return 0

#converts none string to empty string
def xstr(s):
    return '' if s is None else str(s)

def main():
    config = None  # hold configuration items from config file
    args = None  # holds parsed command line arguments
    # config_file_path = None #this is checked earlier than the other globals, before loadConfig(path)
    agents = None  # empty agent dictionary array
    agents_failed = None  # array of agents that failed the autoping test
    mc = {}  # master configuration dictionary
    # assign default values , these are overridden by configuration file values
    mc['healthy_exit_code'] = 132
    mc['hostname'] = socket.gethostname()  # local hostname
    mc['admin_recipients'] = 'johnagooch@maximus.com'
    mc['agent_retries'] = 3
    mc['suppress_primary_alert'] = 0
    mc['suppress_shadow_alert'] = 0
    mc['instance'] = os.environ['AUTOSERV']

    # parse the command line arguments and place them into the args variable
    try:
        mc.update(initCLI())
    except Exception, e:
        logger.error("Failed to parse command line arguments. Reason: %s" % (str(e)))
        traceback.print_exc()
        return 2

    # Initialize global logger object that generates application log file
    try:
        initLogging(mc['level'])
    except Exception, e:
        logger.error("Failed to initialize logging. Reason:%s" % (str(e)))
        traceback.print_exc()
        return 2

    # initialize mc values from conf object
    try:
        if mc['config_file_path']:
            logger.debug("Loading configuration from config file %s." % (mc['config_file_path']))
            mc.update(loadConfig(mc['config_file_path']))
            if 'attachment_file_path' in mc:
                logger.debug("Attachement file path is %s before split." % (mc['attachment_file_path']))
                if len( mc['attachment_file_path'] ):
                    mc['attachment_file_path'] = mc['attachment_file_path'].split(',')
                else:
                    mc['attachment_file_path'] = []
                logger.debug("Attachement file path is %s after split." % (mc['attachment_file_path']))
        else:
            logger.debug("No configuration file path given. mc.config_file_path is %s. Skipping loadConfig()." % (
                mc['config_file_path']))
            mc['attachment_file_path'] = []
    except Exception, e:
        logger.error("Failed to load configuration. Reason: %s" % (str(e)))
        traceback.print_exc()
        return 2

    try:
        logger.debug("Sourcing autosys profile.")
        shell_source("/opt/CA/WorkloadAutomationAE/autouser.%s/autosys.bash.%s" % ( mc['instance'], mc['hostname'].lower() ))
        logger.debug("Autosys profile successfully sourced.")
    except Exception, e:
        logger.error("Failed to initialize environment. Reason:%s" % (str(e)))
        traceback.print_exc()
        return 2

    try:
        if mc['log_file_path']:
            logger.debug("Adding log file in %s folder for logging purposes." % (mc['log_file_path']))
            initLogFile(mc['log_file_path'])
            logger.debug("Successfully added log file in %s folder for logging purposes." % (mc['log_file_path']))
        else:
            logger.info("No log file specified. Skipping initLogFile().")
    except Exception, e:
        logger.error("Failed to initialize log file %s. Reason: %s" % (mc['log_file_path'], str(e)))
        traceback.print_exc()
        # sendMail( mc['smtp_server'], mc['sender'], mc['admin_recipients'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname'] ),  "%s" % ( str(e) ),None )
        sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'],
                          "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % (
                              (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']),
                          mc['admin_recipients'],
                          None, "%s" % (str(e)), [], "plain", None)
        return 2

    # load the list and settings for remote agents to be tested
    try:
        agents = loadAgents(mc['remote_agent_list_path'], mc['agent_retries'])
    except Exception, e:
        logger.error("Failed to complete loadAgents. Reason: %s" % (str(e)))
        traceback.print_exc()
        # sendMail( mc['smtp_server'], mc['sender'], mc['admin_recipients'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname'] ),  "%s" % ( str(e) ),None )
        sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'],
                          "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % (
                              (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']),
                          mc['admin_recipients'],
                          None, "Failed to complete loadAgents. Reason: %s" % (str(e)), [], "plain", None)
        return 2

    # run the main program
    logger.info("Starting Autosys Monitor on host %s" % (mc['hostname']))

    # check the waae services which are the schedule, remote agent, and application server services.
    try:
        logger.info("Checking Autosys services using ustat command.")
        response = chk_services(mc["hostname"], mc['services'])
        if response:
            (subject, body) = response
            logger.debug(
                "server:%s user:%s pwd:%s sender:% subject:%s recips:%s cc:%s body:%s attachments:%s encoding:%s replyto:%s" % (
                    mc['smtp_server'], None, None, mc['sender'], subject, mc['recipients'], None, body,
                    mc['attachment_file_path'], "plain", None))
            logger.debug( "using sendmail command %s "  % ( [ mc['smtp_server'], None, None, mc['sender'], subject, mc['recipients'], None, body, mc['attachment_file_path'], "plain", None ]) )
            #sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], subject, mc['recipients'], None, body, [], "plain")
            sendmail.sendMail( mc['smtp_server'], None, None, mc['sender'], subject,mc['recipients'], None, body,mc['attachment_file_path'], 'text')
            return 1
        else:
            logger.info("Autosys service check completed. All services are running.")
    except Exception, e:
        logger.error("Failed to check services. Reason: %s" % (str(e)))
        traceback.print_exc()
        sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']), mc['admin_recipients'],None, "Failed to check services. Reason: %s" % (str(e)), [], "plain")
        return 2

    # check the Autosys database, primary event process, and shadow event processor status
    try:
        logger.info("Running chk_auto_up command.")
        response = chk_auto_up(int(mc['healthy_exit_code']),  mc['hostname'])
        logger.info("chk_auto_up command completed.")
        if response:
            (subject, body) = response
            # sendMail( mc['smtp_server'], mc['sender'], mc['recipients'], subject, body, mc['attachment_file_path'] )
            sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], subject, mc['recipients'], None, body, mc['attachment_file_path'], "plain")
            return 1
    except Exception, e:
        logger.error("Failed to run chk_auto_up. Reason: %s" % (str(e)))
        traceback.print_exc()
        # sendMail( mc['smtp_server'], mc['sender'], mc['admin_recipients'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname'] ),  "%s" % ( str(e) ),None )
        sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']), mc['admin_recipients'],  None, "Failed to run chk_auto_up. Reason: %s" % (str(e)), [], "plain")
        return 2

    try:
        logger.info("Performing Remote Agent autoping test.")
        response = autoping_agents(agents, mc['autoping_delay'], mc['hostname'])
        if response:
            (subject, body) = response
            # sendMail( mc['smtp_server'], mc['sender'], mc['recipients'], subject, body, mc['attachment_file_path'] )
            #sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']), mc['admin_recipients'],  None, "Failed to run chk_auto_up. Reason: %s" % (str(e)), [], "plain")
            sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], subject, mc['recipients'], None, body, [], "plain" )
            return 1
        logger.info("Remote Agent autoping test completed.")
    except Exception, e:
        logger.error("Failed to complete the autoping test. Reason: %s" % (str(e)))
        traceback.print_exc()
        # sendMail( mc['smtp_server'], mc['sender'], mc['admin_recipients'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname'] ),  "%s" % ( str(e) ),None )
        sendmail.sendMail(mc['smtp_server'], None, None, mc['sender'], "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % ( (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']),mc['admin_recipients'],None, "Failed to complete the autoping test. Reason: %s" % (str(e)), [], "plain")
        return 2
    #
    # try:
    #     if mc['verbose'] == True:
    #         autopingReport(agents)
    # except Exception, e:
    #     logger.error("Failed to complete autopingReport. Reason: %s" % (str(e)))
    #     traceback.print_exc()
    #     sendMail(mc['smtp_server'], mc['sender'], mc['admin_recipients'],
    #              "FAILURE - AUTOSYS - Autosys Monitor Script on %s. [%s]" % (
    #                  (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M"), mc['hostname']), "%s" % (str(e)), None)
    #     return 2
    logger.info("Ending Autosys Monitor Run\n\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
