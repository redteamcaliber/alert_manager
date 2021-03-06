import logging
import os
import sys
import json
import shutil
import cherrypy
import re
import time
import datetime
import urllib

#from splunk import AuthorizationFailed as AuthorizationFailed
import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
import splunk.bundle as bundle
import splunk.entity as entity
from splunk.appserver.mrsparkle.lib import jsonresponse
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
import splunk.clilib.bundle_paths as bundle_paths
from splunk.util import normalizeBoolean as normBool
from splunk.appserver.mrsparkle.lib.decorators import expose_page
from splunk.appserver.mrsparkle.lib.routes import route
import splunk.rest as rest

dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)    

from AlertManagerUsers import *

#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')    


def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.alert_manager.controllers.Helpers')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'alert_manager_helpers_controller.log']), maxBytes=25000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger(logging.DEBUG)

from splunk.models.base import SplunkAppObjModel
from splunk.models.field import BoolField, Field



class Helpers(controllers.BaseController):

    @expose_page(must_login=True, methods=['GET']) 
    def get_users(self, **kwargs):
        logger.info("Get users")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        users = AlertManagerUsers(sessionKey=sessionKey)
        user_list = users.getUserList()

        logger.debug("user_list: %s " % json.dumps(user_list))

        return json.dumps(user_list)
   
    @expose_page(must_login=True, methods=['GET']) 
    def get_indexes(self, **kwargs):
        logger.info("Get indexes")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        
        uri = '/services/admin/indexes?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        #logger.debug("response: %s" % serverContent)
        entries = json.loads(serverContent)
        
        index_list = []
        if len(entries['entry']) > 0:
            for entry in entries['entry']:
                index_list.append(entry['name'])
        

        return json.dumps(index_list)

    @expose_page(must_login=True, methods=['GET']) 
    def get_email_templates(self, **kwargs):
        logger.info("Get templates")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?q=&output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("response: %s" % serverContent)
        entries = json.loads(serverContent)
        
        template_list = [ "notify_user" ]
        if len(entries) > 0:
            for entry in entries:
                template_list.append(entry['email_template_name'])
        

        return json.dumps(template_list)

    @expose_page(must_login=True, methods=['GET']) 
    def get_email_template_files(self, **kwargs):
        logger.info("Get templates files")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        file_list = []

        file_default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
        if os.path.exists(file_default_dir):
            for f in os.listdir(file_default_dir):
                if re.match(r'.*\.html', f):
                    if f not in file_list:
                        file_list.append(f)

        file_local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")
        if os.path.exists(file_local_dir):
            for f in os.listdir(file_local_dir):
                if re.match(r'.*\.html', f):
                    if f not in file_list:
                        file_list.append(f)

        return json.dumps(file_list)        


    @expose_page(must_login=True, methods=['GET']) 
    def get_savedsearch_description(self, savedsearch, app, **kwargs):
        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        uri = '/servicesNS/nobody/%s/admin/savedsearch/%s?output_mode=json' % (app, savedsearch)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')

        savedSearchContent = json.loads(serverContent)

        if savedSearchContent["entry"][0]["content"]["description"]:
            return savedSearchContent["entry"][0]["content"]["description"]
        else:
            return ""
