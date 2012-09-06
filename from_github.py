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

# A script to export Github issues into the portable bug interchange format.
#
# Usage: from_github.py repoURL    - export all issues for repository
#        from_github.py issueURL   - export particular issue
#        from_github.py commentURL - export particular issue comment

import httplib
import urllib
import json
import sys
import pprint

def github_get(url):
	conn = httplib.HTTPSConnection('api.github.com')
	conn.request('GET', url)
	response = conn.getresponse()

	result = json.loads(response.read())
	conn.close()

	return result

def get_comments(issue_url):
	args = issue_url.split('/')
	user = args[3]
	repo = args[4]
	issue = args[6]

	url = '/repos/%s/%s/issues/%s/comments' % (user, repo, issue)

	result = github_get(url)

	comments = {}

	for comment in result:
		commentid = comment['url']

		comments[commentid] = {}
		comments[commentid]['name'] = comment['user']['login']
		comments[commentid]['created_at'] = comment['created_at']
		comments[commentid]['in-reply-to'] = 'issue' # Github doesn't support threaded comments
		comments[commentid]['comment'] = comment['body']

	return comments

def export_comment(comment_url):
	pass

# Returns a tuple of (key, object)
def format_issue(bug, repository_url):
	repo = repository_url.split('/')[4]

	bugid = bug['html_url']
	export = {}

	export['metadata'] = {}
	export['metadata']['title'] = bug['title']
	export['metadata']['created_at'] = bug['created_at']
	export['metadata']['metadata_modified_at'] = bug['updated_at']
	export['metadata']['project_name'] = repo
	export['metadata']['project_id'] = repository_url
	export['metadata']['status'] = bug['state']
	export['metadata']['severity'] = ''
	export['metadata']['component'] = ''
	export['metadata']['reporter'] = bug['user']['login']
	export['metadata']['seen_in'] = ''

	if bug['assignee'] == None:
		export['metadata']['owner'] = 'Unassigned'
	else:
		export['metadata']['owner'] = bug['assignee']['login']

	export['metadata']['description'] = bug['body']

	comments = get_comments(bugid)

	for comment in comments.keys():
		export[comment] = comments[comment]
	
	return (bugid, export)

def export_issue(issue_url):
	args = issue_url.split('/')
	user = args[3]
	repo = args[4]
	issue = args[6]

	url = '/repos/%s/%s/issues/%s' % (user, repo, issue)

	result = github_get(url)

	bug = format_issue(result, issue_url)

	export = {bug[0] : bug[1]}
	print json.dumps(export, sort_keys=True, indent=4)

def export_repository(repository_url):
	args = repository_url.split('/')
	user = args[3]
	repo = args[4]

	url = '/repos/%s/%s/issues' % (user, repo)

	result = github_get(url)

	export = {'format' : 'http://travisbrown.ca/projects/bug_interchange.txt'}
	for bug in result:
		formatted = format_issue(bug, repository_url)

		export[formatted[0]] = formatted[1]

	print json.dumps(export, sort_keys=True, indent=4)

if __name__ == '__main__':
	if len(sys.argv) == 1:
		print 'Usage: from_github.py repoURL    - export all issues for repository'
		print '       from_github.py issueURL   - export particular issue'
		print '       from_github.py commentURL - export particular issue comment'
		sys.exit(1)

	if 'issuecomment' in sys.argv[1]:
		export_comment(sys.argv[1])
	elif 'issues' in sys.argv[1]:
		export_issue(sys.argv[1])
	else:
		export_repository(sys.argv[1])
