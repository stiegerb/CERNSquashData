#! /usr/bin/env python
import sys
import json

def print_player(data, mute=False):
    message = '{name:<30} | {elo:6.1f} | {tot:4} | {wins:4} | {rate:7.2%} | {seasons:4} |'
    if not mute:
        print message.format(
                     name=name,
                     tot=data['n_total_matches'],
                     wins=data['n_total_wins'],
                     rate=float(data['n_total_wins'])/data['n_total_matches'],
                     elo=data.get('last_elo', 1000),
                     seasons=data['n_seasons_played'])

    return float(data['n_total_wins'])/data['n_total_matches'], data.get('last_elo', 1000)

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

header = "Player name                    | Elo    | Tot  | Win  | Winrate | Seas |"
print header
print len(header)*"-"
for name,(winrate, elo) in sorted(winrates, key=lambda x: x[1][1], reverse=True):
    print_player(squash_data['players'][name], mute=False)
print len(header)*"-"
