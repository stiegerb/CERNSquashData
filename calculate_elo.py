#! /usr/bin/env python
import sys
import json

from operator import itemgetter

from squash_crawl import parse_result

BASEELO = 1000

def expected_score(rating_diff):
	return 1.0 / (1+10**(-1.0*rating_diff/400.))

def calculate_elo(elo1, elo2, result):
	## See here: http://www.eloratings.net/system.html
	score = parse_result(result)
	if not score: return elo1, elo2

	K = 40.0

	# Scale the score to be within 1 (3-0 win) and 0 (0-3 loss)
	score /= 3.0 # now from 1 to -1
	score -= (score-1.0)/2.0
	# Now scores are
	# 3-0 -> 1.0
	# 3-1 -> 0.833
	# 3-2 -> 0.666
	# 2-3 -> 0.333
	# 1-3 -> 0.166
	# 0-3 -> 0.0
	elo1_new = elo1 + K * (score - expected_score(elo1-elo2))
	elo2_new = elo2 + K * ((1.0-score) - expected_score(elo2-elo1))
	return elo1_new, elo2_new

## Read the data
squash_data = None
with open('squash_data.json', 'r') as ifile:
	squash_data = json.load(ifile)

## Set everybody's default elo to the base
for name in squash_data['players'].keys():
	squash_data['players'][name].setdefault('last_elo', BASEELO)

## Sort seasons by date
seasons = [(k, v['year'], v['month']) for k,v in squash_data['seasons'].iteritems()]
seasons.sort(key=itemgetter(1,2))

for season,_,_ in seasons:
	sdata = squash_data['seasons'][season]
	for pname in sdata['players']:
		pdata = squash_data['players'][pname]
		matches = pdata['seasons'][season]['matches']
		for pname2, result in matches.iteritems():
			pdata2 = squash_data['players'][pname2]
			elo1, elo2 = calculate_elo(pdata['last_elo'], pdata2['last_elo'], result)
			pdata['last_elo']  = elo1
			pdata2['last_elo'] = elo2


## Dump to json file
with open('squash_data.json', 'w') as ofile:
	json.dump(squash_data, ofile, indent=2, sort_keys=True)
