#! /usr/bin/env python

import sys
import os
import re
import requests
from bs4 import BeautifulSoup

from pprint import pprint

BASEURL = "http://club-squash.web.cern.ch/club-squash/archives/%s.htm"
try:
	SEASON = sys.argv[1]
except IndexError:
	SEASON = '1605'

EMPTYRESULT = ' - '

def get_name(tag):
	text = tag.get_text().strip().lower()
	text = text.replace('\n','')
	text = text.replace('\r','')
	text = text.replace('  ',' ')
	text = re.sub(r'(\s?-?\s?\(?(1st|2nd|3rd|[1-9]{1}th) to finish\)?)', '', text)
	return text

def get_result(tag):
	res = re.match(r'(\d)-(\d)', tag.get_text().strip()) # '3-1', '2-3', etc.
	if res:
		return tag.get_text().strip()
	else:
		return EMPTYRESULT

## Load page
url = BASEURL % SEASON
page_request = requests.get(url)
if not page_request.ok:
	url = url+'l' # some end in .htm, some in .html
	page_request = requests.get(url)
	if not page_request.ok:
		print "Something wrong with url:",
		print page_request.url
		print page_request.status_code, page_request.reason
		sys.exit()

## Parse html
soup = BeautifulSoup(page_request.text, 'html.parser')

players   = {} # div rank -> list of player names
results   = {} # player name -> list of results
division_size = -1

## First pass: collect all divisions and players in each division
for table in soup.find_all('table'):
	rows_iter = iter(table.find_all('tr'))
	for row in rows_iter:
		# Check if this starts a new division or not
		div = row.find('td', string=re.compile('Division'))
		# FIXME This is not going to work if the cell doesn't read 'Division ..'
		if div:
			# Extract the division rank
			rank = int(re.match(r'^Division\s([\d]{1,2})$', div.get_text()).group(1))

			# Extract the division size (once)
			if division_size < 0:
				res_cols = row.find_all('td', string=re.compile(r'\b[A-G]{1}\b'))
				division_size = len(res_cols)

			# Store the next N rows as player rows
			prows = [next(rows_iter) for _ in range(division_size)]

			# Player entry is always the second one in the row
			players[rank] = [get_name(r.find_all('td')[1]) for r in prows]

			# Go through the rows and extract the match results
			for name,prow in zip(players[rank], prows):
				# Results start in 3rd position and we know how many to expect
				match_results = prow.find_all('td')[2:division_size+2]
				for entry in match_results:
					results.setdefault(name, []).append(get_result(entry))

			# ####### DEBUG
			# break

print 'Found %d divisions of size %d' % (len(players), division_size)

# Make sure nothing was filled in the -1 rank
assert players.get(-1, None) is None
# Make sure we found a division size
assert division_size > 0
# Make sure all divisions are the same size
assert all([len(p) == division_size for p in players.values()])

# for player,divrank in players.iteritems():
# 	print '%-30s %d' % (player, divrank)

## Second pass: knowing the number of players in each division, get their results
for divrank, player_names in players.iteritems():
	print '-----------------------'
	print 'Processing division %2d' % divrank

	matches = [] # (name1, name2, result)
	for name in player_names:
		for n, result in enumerate(results[name]):
			if result == EMPTYRESULT: continue
			print '%-30s vs %30s : %s' % (name, player_names[n], result)


# 		# player = row.find(is_player)
# 		# if not player:
# 		# 	# Empty player row?
# 		# 	player_name = '-'
# 		# 	# print row
# 		# 	# raise RuntimeError("Something went wrong, this is not a player row")
# 		# else:
# 		# 	player_name = get_name(player)

# 		# print '%-30s' % player_name,

# 		# results = row.find_all(is_result)[:len(playerrows)]
# 		# for entry in results:
# 		# 	print get_result(entry),
# 		# print ''






