#! /usr/bin/env python
import sys
import json

name = sys.argv[1]

squash_data = None
with open('squash_data.json', 'r') as ifile:
	squash_data = json.load(ifile)

player_data = squash_data['players'].get(name)
if not player_data:
	print 'Player %s not found' % name
	sys.exit(-1)

print '{name:<30} -- Total games: {tot} ({wins} wins, {rate:.2%} percentage)'.format(
				 name=name,
	             tot=player_data['n_total_matches'],
	             wins=player_data['n_total_wins'],
	             rate=float(player_data['n_total_wins'])/player_data['n_total_matches'])

## Dump to json file
oname = 'player_data_%s.json' % name.replace(' ', '').lower()
with open(oname, 'w') as ofile:
	json.dump(player_data, ofile, indent=2, sort_keys=True)


## Print all the matches
all_matches = []
for season,seas_data in player_data['seasons'].iteritems():
	for opp,res in seas_data['matches'].iteritems():
		all_matches.append((season,opp,res))

print len(all_matches)
for seas,opp,res in all_matches:
	print '%-12s: %-30s: %s' % (seas, opp, res)
