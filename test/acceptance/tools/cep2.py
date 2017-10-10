# -*- coding: utf-8 -*-
#
# Copyright 2015 Telefonica Investigación y Desarrollo, S.A.U
#
# This file is part of perseo-fe
#
# perseo-fe is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# perseo-fe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with perseo-fe.
# If not, see http://www.gnu.org/licenses/.
#
# For those usages not covered by the GNU Affero General Public License
# please contact with:
# iot_support at tid.es
#
__author__ = 'Jon Calderín Goñi <jon.caldering@gmail.com>'

import requests
import json
from tools.mongo_utils import Mongo
from iotqautils.iotqaLogger import get_logger
from general_utils import pretty


class Cep(object):
    """
    Class to manage Perseo instance
    """
    def __init__(self,
                 cep_host,
                 cep_port,
                 service,
                 service_path,
                 mongo_host,
                 mongo_port,
                 mongo_db,
                 mongo_orion_db_prefix,
                 mongo_orion_db_collection,
                 cep_core_host,
                 cep_core_port,
                 version_url='/version',
                 notifications_url='/notices',
                 plain_rules_url='/rules',
                 visual_rules_url='/m2m/vrules',
                 core_rules_url='/perseo-core/rules',
                 log_instance=None,
                 log_verbosity='DEBUG'):
        # initialize logger
        if log_instance is not None:
            self.log = log_instance
        else:
            self.log = get_logger('cep', log_verbosity)
        self.cep_url = 'http://{cep_host}:{cep_port}'.format(cep_host=cep_host, cep_port=cep_port)
        self.cep_core_url = 'http://{cep_core_host}:{cep_core_port}'.format(cep_core_host=cep_core_host,
                                                                            cep_core_port=cep_core_port)
        self.service = service
        self.service_path = service_path
        self.mongo = Mongo(mongo_host, mongo_port, mongo_db)
        self.mongo_cep_db = mongo_db
        self.mongo_orion_db = '{mongo_orion_db_prefix}-{service}'.format(mongo_orion_db_prefix=mongo_orion_db_prefix, service=service).lower()
        self.mongo_orion_db_collection = mongo_orion_db_collection
        self.version_url = self.cep_url + version_url
        self.notifications_url = self.cep_url + notifications_url
        self.plain_rules_url = self.cep_url + plain_rules_url
        self.visual_rules_url = self.cep_url + visual_rules_url
        self.core_rule_url = self.cep_core_url + core_rules_url

    def __build_headers(self):
        """
        Build the headers with the service and service path
        :return:
        """
        return {
            'fiware-service': self.service,
            'fiware-servicepath': self.service_path,
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }


    def __request(self, method, url, headers=None, data=None):
        """
        Request method with log
        :param method:
        :param url:
        :param headers:
        :param data:
        :return:
        """
        self.log.debug('****Making a new request++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        parms = {
            'method': method,
            'url': url
        }
        msg_log = ('Sending the request: \n'
                   '\tMethod: {method}\n'
                   '\tUrl: {url}\n'.format(method=method, url=url))
        if headers is not None:
            msg_log += '\tHeaders: {headers}\n'.format(headers=headers)
            parms.update({'headers': headers})
        if data is not None:
            msg_log += '\tPayload: {data}\n'.format(data=data)
            parms.update({'data': data})
        # End request log
        msg_log += '--------------------'
        self.log.debug(msg_log)
        try:
            resp = requests.request(**parms)
            self.log.debug('The response is: \n'
                           '\tCode: {status_code}\n'
                           '\tHeaders: {headers}\n'
                           '\tBody: {body}\n'
                           '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                           ''.format(status_code=resp.status_code, headers=pretty(dict(resp.headers)),
                                     body=pretty(resp.text)))
        except Exception as e:
            self.log.error("Error sending the request:\n{msg_log}, the error is {e}".format(msg_log=msg_log, e=e))
            raise e
        return resp

    def set_service_and_servicepath(self, service, service_path):
        """
        Modify the service and servicepath set in tne __init__
        :param service:
        :param service_path:
        :return:
        """
        self.service = service
        self.service_path = service_path

    def get_service_and_servicepath(self):
        """
        Get the current service and service path
        :return:
        """
        return self.service, self.service_path

    def version(self):
        """
        Get the perseo version
        :return:
        """
        return self.__request('get', self.version_url, headers=self.__build_headers())

    def notify(self, notification):
        """
        Send a CB notification to Perseo
        Take into account there are not check about the notification, but it has to be as CB sents it, and it has to be a python dict, an example is:
        {
          "subscriptionId" : "51c04a21d714fb3b37d7d5a7",
          "originator" : "localhost",
          "contextResponses" : [
            {
              "contextElement" : {
                "attributes" : [
                  {
                    "name" : "temperature",
                    "type" : "float",
                    "value" : "26.5"
                  }
                ],
                "type" : "Room",
                "isPattern" : "false",
                "id" : "Room1"
              },
              "statusCode" : {
                "code" : "200",
                "reasonPhrase" : "OK"
              }
            }
          ]
        }
        :param notification:
        :return:
        """
        return self.__request('post', self.notifications_url, headers=self.__build_headers(), data=json.dumps(notification))

    # Plain Rules

    def create_plain_rule(self, plain_rule_dict):
        """
        Create a plain rule given the payload to create it
        :param plain_rule_dict:
        :return:
        """
        return self.__request('post', self.plain_rules_url, headers=self.__build_headers(),
                              data=json.dumps(plain_rule_dict))

    def list_plain_rules(self):
        """
        List all plain rules stored in CEP front end (perseo-fe)
        :return:
        """
        return self.__request('get', self.plain_rules_url, headers=self.__build_headers())

    def get_plain_rule(self, id):
        """
        Get a specific plain rule given its id
        :param id:
        :return:
        """
        url = self.plain_rules_url + '/{id}'.format(id=id)
        return self.__request('get', url, headers=self.__build_headers())

    def delete_plain_rule(self, id):
        """
        Delete a specific plain rule given its id
        :param id:
        :return:
        """
        url = self.plain_rules_url + '/{id}'.format(id=id)
        return self.__request('delete', url, headers=self.__build_headers())

    # Visual rules

    def create_visual_rule(self, visual_rule):
        """
        Create a new visual rule in cep
        :param visual_rule:
        :return:
        """
        return self.__request('post', self.visual_rules_url, headers=self.__build_headers(),
                              data=json.dumps(visual_rule))

    def list_visual_rules(self):
        """
        List all visual rules existant in cep
        :return:
        """
        return self.__request('get', self.visual_rules_url, headers=self.__build_headers())

    def get_visual_rule(self, id):
        """
        Get a specific visual rule from cep given its id
        :param id:
        :return:
        """
        url = self.visual_rules_url + '/{id}'.format(id=id)
        return self.__request('get', url, headers=self.__build_headers())

    def delete_visual_rule(self, id):
        """
        Delete a specific visual rule from cep given its id
        :param id:
        :return:
        """
        url = self.visual_rules_url + '/{id}'.format(id=id)
        return self.__request('delete', url, headers=self.__build_headers())

    def update_visual_rule(self, id, visual_rule):
        """
        Update the visual rule. The really thing is, the cep delete the visual rule with the id given and create a new one
        :param id:
        :param visual_rule:
        :return:
        """
        url = self.visual_rules_url + '/{id}'.format(id=id)
        return self.__request('put', url, headers=self.__build_headers(), data=json.dumps(visual_rule))

    # Mongo

    def __connect_mongo_rules(self):
        """
        Connect to mongo and choice the rules collection
        :return:
        """
        self.mongo.connect()
        self.mongo.choice_database(self.mongo_cep_db)
        self.mongo.choice_collection('rules')

    def __turn_from_mongo_to_python(self, result):
        """
        Get the mongo result and turn it into a python list
        :param result:
        :return:
        """
        list_results = []
        for row in result:
            list_results.append(row)
        return list_results

    def get_rule_from_mongo(self, name):
        """
        Get a specific rule from mongo given its name
        :param name:
        :return:
        """
        self.__connect_mongo_rules()
        result = self.__turn_from_mongo_to_python(self.mongo.find_data({'name': name}))
        self.mongo.disconnect()
        return result

    def list_rules_from_mongo(self):
        """
        List all rules in mongo
        :return:
        """
        self.__connect_mongo_rules()
        result = self.__turn_from_mongo_to_python(self.mongo.find_data({}))
        self.mongo.disconnect()
        return result

    def delete_rule_in_mongo(self, name):
        """
        Delete a rule in mongo given its name
        :param name:
        :return: True if it is deleted or if it doesnt exist, else, return a False
        """
        self.__connect_mongo_rules()
        rule = self.get_rule_from_mongo(name)
        if len(rule) > 1:
            self.mongo.disconnect()
            raise ValueError('There is more than one rule in the database with the name "{name}". '
                             'The result for the query is {result}'.format(name=name, result=rule))
        elif len(rule) == 0:
            print 'There is no rule to delete'
            self.mongo.disconnect()
            return True
        else:
            self.mongo.remove({'_id': rule[0]['_id']})
            self.mongo.disconnect()
            return True

    def create_rule_in_mongo(self, rule):
        """
        Create a new rule in mongo. The rule is not checked, any payload can be sent
        :param rule:
        :return:
        """
        self.__connect_mongo_rules()
        self.mongo.insert_data(rule)
        self.mongo.disconnect()
        return True

    def create_entity_orion_mongo(self, entity_structure):
        """
        Create an entity like CB. The structure is not checked. The databased is changed to use the one CB would use
        :param entity_structure:
        :return:
        """
        self.log.debug('Creating in db {mongo_orion_db} in the collection {mongo_orion_db_collection} the structure: {entity_structure}'.format(mongo_orion_db=self.mongo_orion_db, mongo_orion_db_collection=self.mongo_orion_db_collection, entity_structure=entity_structure))
        self.mongo.connect()
        self.mongo.choice_database(self.mongo_orion_db)
        self.mongo.choice_collection(self.mongo_orion_db_collection)
        self.mongo.insert_data(entity_structure)
        self.mongo.disconnect()

    def reset_db(self):
        """
        Reset all DBs used in tests
        :return:
        """
        self.mongo.connect()
        self.mongo.choice_database(self.mongo_cep_db)
        self.mongo.choice_collection('rules')
        self.mongo.remove_collection()
        self.mongo.choice_collection('executions')
        self.mongo.remove_collection()
        self.mongo.choice_database(self.mongo_orion_db)
        self.mongo.drop_database()
        self.mongo.disconnect()


    # Perseo-core

    def create_perseo_core_rule(self, rule):
        """
        Create a perseo core rules
        :param rule:
        :return:
        """
        return self.__request('post', self.core_rule_url, self.__build_headers(), json.dumps(rule))

    def list_perseo_core_rules(self):
        """
        List all rules in the perseo-core
        :return:
        """
        return self.__request('get', self.core_rule_url, self.__build_headers())

    def get_perseo_core_rule(self, name):
        """
        Get a perseo rule given its name
        :param name:
        :return:
        """
        url = self.core_rule_url + '/{name}'.format(name=name)
        return self.__request('get', url, headers=self.__build_headers())

    def update_perseo_core_rule(self, rules_set):
        """
        Update a perseo core rule
        :param rules_set:
        :return:
        """
        return self.__request('put', self.core_rule_url, self.__build_headers(), json.dumps(rules_set))

    def delete_perseo_core_rule(self, name):
        """
        Delete a perseo core rule
        :param name:
        :return:
        """
        url = self.core_rule_url + '/{name}'.format(name=name)
        return self.__request('delete', url, headers=self.__build_headers())

    def util_delete_all_core_rules(self):
        """
        Delete all rules in core getting all and deleting each
        :return:
        """
        for rule in self.list_perseo_core_rules().json():
            resp = self.delete_perseo_core_rule(rule['name'])
            if resp.status_code == 200:
                continue
            else:
                raise StandardError(
                    'There was a problem removing the rule "{name}", the response from perseo-core is "{response}"'.format(
                        name=rule['name'], response=resp.text))
        return True
