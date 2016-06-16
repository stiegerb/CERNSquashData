#! /usr/bin/env python
import sys
import json

from calculate_elo import sort_seasons
from squash_crawl import get_name

name = get_name(unicode(sys.argv[1]))

squash_data = None
with open('squash_data.json', 'r') as ifile:
	squash_data = json.load(ifile)

player_data = squash_data['players'].get(name)
if not player_data:
	print 'Player %s not found' % name
	sys.exit(-1)

print '{name} ({tot} total games, {wins} wins, {rate:.2%} winrate, Elo {elo:6.1f})'.format(
				 name=name,
	             tot=player_data['n_total_matches'],
	             wins=player_data['n_total_wins'],
	             rate=float(player_data['n_total_wins'])/player_data['n_total_matches'],
	             elo=player_data.get('last_elo', 1200))

# ## Dump to json file
# oname = 'player_data_%s.json' % name.replace(' ', '').lower()
# with open(oname, 'w') as ofile:
# 	json.dump(player_data, ofile, indent=2, sort_keys=True)


# ## Print all the matches
# all_matches = []
# for season,seas_data in player_data['seasons'].iteritems():
# 	for opp,res in seas_data['matches'].iteritems():
# 		all_matches.append((season,opp,res))

# print len(all_matches)
# for seas,opp,res in all_matches:
# 	print '%-12s: %-30s: %s' % (seas, opp, res)

all_seasons = sort_seasons(squash_data['seasons'])

message = ('{seas:12s} {month:>2}/{year:4} | {div:^3} | {nmat:^3} |'
	       ' {wins:^3} ({rate:6.1%}) | {elo:^6.1f} |')
header = ' Season              | Div | GP  |  Wins (%)    | Elo    |'
print header
print len(header)*'-'
for season,year,month in all_seasons:
	sdata = player_data['seasons'].get(season, None)
	if not sdata: continue
	winrate = float(sdata['n_wins'])/len(sdata['matches']) if len(sdata['matches']) else 0.
	print message.format(
			seas=season, year=year, month=month,
			div=sdata['division'],
			nmat=len(sdata['matches']),
			wins=sdata['n_wins'],
			rate=winrate,
			elo=sdata.get('elo'))
			# elo=sdata.get('elo', player_data['last_elo']))
print len(header)*'-'
