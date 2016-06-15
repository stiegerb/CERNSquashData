#! /usr/bin/env python
import sys
import json

def print_player(data, mute=False):
	message = '{name:<30} -- Total games: {tot:3} ({wins:3} wins, {rate:.2%} percentage)'
	if not mute:
		print message.format(
					 name=name,
		             tot=data['n_total_matches'],
		             wins=data['n_total_wins'],
		             rate=float(data['n_total_wins'])/data['n_total_matches'])
	return float(data['n_total_wins'])/data['n_total_matches']

squash_data = None
with open('squash_data.json', 'r') as ifile:
	squash_data = json.load(ifile)

winrates = []

# Minimum number of played matches
try:
	CUTOFF = int(sys.argv[1])
except IndexError:
	CUTOFF = 50

for name, data in squash_data['players'].iteritems():
	if data['n_total_matches'] < CUTOFF: continue
	winrates.append((name,print_player(data, mute=True)))

for name,winrate in sorted(winrates, key=lambda x: x[1]):
	print_player(squash_data['players'][name], mute=False)
