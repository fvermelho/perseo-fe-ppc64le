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


class Mock(object):

    def __init__(self, host, http_port):
        """
        Set the host and the port where the mock is started
        :param host:
        :param http_port:
        :return:
        """
        base_url = 'http://{host}:{http_port}'.format(host=host, http_port=http_port)
        self.mail_url = '{base_url}/get/email'.format(base_url=base_url)
        self.sms_url = '{base_url}/get/sms'.format(base_url=base_url)
        self.update_url = '{base_url}/get/update'.format(base_url=base_url)
        self.post_url = '{base_url}/get/post'.format(base_url=base_url)
        self.mail_counter_url = '{base_url}/counter/email'.format(base_url=base_url)
        self.sms_counter_url = '{base_url}/counter/sms'.format(base_url=base_url)
        self.update_counter_url = '{base_url}/counter/update'.format(base_url=base_url)
        self.post_counter_url = '{base_url}/counter/post'.format(base_url=base_url)
        self.reset_mails_url = '{base_url}/reset/email'.format(base_url=base_url)
        self.reset_sms_url = '{base_url}/reset/sms'.format(base_url=base_url)
        self.reset_update_url = '{base_url}/reset/update'.format(base_url=base_url)
        self.reset_post_url = '{base_url}/reset/post'.format(base_url=base_url)

    def get_mails(self):
        """
        Get all the mails sent from the mock
        :return:
        """
        return requests.request('get', self.mail_url)

    def get_sms(self):
        """
        Get all smss sent from the mock
        :return:
        """
        return requests.request('get', self.sms_url)

    def get_update(self):
        """
        Get all updates sent from the mock
        :return:
        """
        return requests.request('get', self.update_url)

    def get_post(self):
        """
        Get all posts sent from the mock
        :return:
        """
        return requests.request('get', self.post_url)
    
    def get_counter_mails(self):
        """
        Get the counter of the mails from the mock
        :return:
        """
        return requests.request('get', self.mail_counter_url)
    
    def get_counter_post(self):
        """
        Get the counter of the posts from the mock
        :return:
        """
        return requests.request('get', self.post_counter_url)
    
    def get_counter_update(self):
        """
        Get the counter of the updates from the mock
        :return:
        """
        return requests.request('get', self.update_counter_url)
    
    def get_counter_sms(self):
        """
        Get the counter of the sms from the mock
        :return:
        """
        return requests.request('get', self.sms_counter_url)
    
    def reset_mails(self):
        """
        Reset the mails and the counter mails in the emock
        :return:
        """
        return requests.request('put', self.reset_mails_url)
    
    def reset_post(self):
        """
        Reset the posts and the counter posts in the mock
        :return:
        """
        return requests.request('put', self.reset_post_url)
    
    def reset_update(self):
        """
        Reset the updates and the counter updates in the mock
        :return:
        """
        return requests.request('put', self.reset_update_url)
    
    def reset_sms(self):
        """
        Reste the smss and the counter smss in the mock
        :return:
        """
        return requests.request('put', self.reset_sms_url)