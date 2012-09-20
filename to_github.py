#!/usr/bin/env python2.7
# 
# Copyright (C) 2012  Travis Brown (travisb@travisbrown.ca)
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# A script to import bug-interchange bugs into the Github issue tracker
#
# Usage: to_github.py projectURL bug_file 
#                  - import all bugs in bug_file into the project at projectURL

import httplib
import urllib
import json
import sys
import pprint
import fileinput
import base64
import os.path
import readline

CONFIG_FILENAME = 'to_github.map'

def github_post(url, content, extra_headers = {}):
	conn = httplib.HTTPSConnection('api.github.com')
	conn.request('POST', url, content, extra_headers)
	response = conn.getresponse()

	pprint.pprint(response.getheaders())
	result = json.loads(response.read())
	conn.close()

	return result

# Prompt the user to authenticate so we can get an OAuth2 token and perform all
# the operations asked of us without bothering the user. This only needs to be
# done once.
def authenticate():
	username = raw_input('Username: ')
	password = raw_input('Password: ')

	encoded = base64.b64encode('%s:%s' % (username, password))
	auth_header = {'Authorization' : 'Basic %s' % encoded}

	auth_args = {
			'note'     : 'bug-interchange github importer',
			'note_url' : 'https://github.com/travisb-ca/bug_interchange',
			'scopes'   : ['repo'],
		}

	result = github_post('/authorizations', json.dumps(auth_args), auth_header)

	print result

	if 'token' not in result.keys():
		print 'Failed to authenticate'
		return None

	return result['token']

def save_config(config):
	config_file = open(CONFIG_FILENAME, 'w')

	config_file.write('%s\n' % config['token'])
	for key in config:
		if key == 'token':
			continue

		config_file.write('%s %s\n' % (key, config[key]))
	config_file.close()

# Load the configuration and datafile.
#
# This is a dictionary. The value of the 'token' key is the OAuth token needed
# to access Github. Every other key-value is a mapping from a github URL to an
# issue or comment original ID.
def load_config():
	if not os.path.exists(CONFIG_FILENAME):
		config = {}

		config['token'] = authenticate()
		if config['token'] != None:
			save_config(config)
	else:
		config = None

		for line in fileinput.input(CONFIG_FILENAME):
			if config == None:
				config = {}
				config['token'] = line
			else:
				github, original = line.split(' ', 1)
				config[github] = original

	return config

print load_config()
