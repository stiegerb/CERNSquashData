#! /usr/bin/env python

import sys
import os
import re
import requests
from bs4 import BeautifulSoup

from pprint import pprint

BASEURL = "http://club-squash.web.cern.ch/club-squash/archives/%s.htm"
SEASON = '1605'
# SEASON = '1412-1501'

def get_name(tag):
	text = tag.get_text().strip('\n\r').strip()
	name = re.match(r'^([-\w\s]*?){1,2}\b\s\b([-A-Z]{2,}){1,2}\b(?:\w*)?', text)
	if name:
		return text
	else:
		return None

def get_result(tag):
	res = re.match(r'(\d)-(\d)', tag.get_text().strip()) # '3-1', '2-3', etc.
	if res:
		return tag.get_text().strip()
	elif tag.get_text() in ['', 'n/a', u'\xa0']:
		return ' - '
	return None

def is_player(tag):
	return all([ tag.name == u'td',
		         get_name(tag) ])

def is_result(tag):
	if not tag.name == u'td': return False
	if not get_result(tag): return False
	return True

try:
	result = requests.get(BASEURL % SEASON).text
except:
	with open('site.htm', 'r') as file:
		result = file.read()

soup = BeautifulSoup(result, 'html.parser')

divisions = {} # div rank -> list of player rows
players = {} # player names -> div rank
rank = -1


## First pass: collect all divisions and players in each division
for table in soup.find_all('table'):
	for row in table.find_all('tr'):
		# Check if this starts a new division or not
		div = row.find('td', string=re.compile('Division'))
		if div:
			# Extract the division rank
			rank = int(re.match(r'^Division\s([\d]{1,2})$', div.get_text()).group(1))
			# print 'Found division %d' % rank
			continue # done with this row

		player = row.find(is_player)
		if player:
			# print '  ', get_name(player)
			divisions.setdefault(rank, []).append(row)
			players[get_name(player)] = rank
			continue # done with this row

# Make sure nothing was filled in the -1 rank
assert divisions.get(-1, None) is None

# for player,divrank in players.iteritems():
# 	print '%-30s %d' % (player, divrank)

## Second pass: knowing the number of players in each division, get their results
for divrank, playerrows in divisions.iteritems():
	print '-----------------------'
	print 'Processing division %2d' % divrank
	for row in playerrows:
		player = row.find(is_player)
		if not player:
			print row
			raise RuntimeError("Something went wrong, this is not a player row")

		print '%-30s' % get_name(player),

		results = row.find_all(is_result)[:len(playerrows)]
		for entry in results:
			print get_result(entry),
		print ''






