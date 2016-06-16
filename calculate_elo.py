#! /usr/bin/env python
import sys
import json

from operator import itemgetter

from squash_crawl import parse_result

BASEELO = 1200

def expected_score(rating_diff):
    return 1.0 / (1+10**(-1.0*rating_diff/400.))

def calculate_elo(elo1, elo2, result):
    """
    Calculate the change in elo for two players
    `result` is a string that is accepted by `parse_result`,
    e.g. '3-1', '2-3', '2', etc.

    See here for the algorithm: http://www.eloratings.net/system.html
    """
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

def sort_seasons(sdata):
    """Sort seasons by date"""
    seasons = [(k, v['year'], v['month']) for k,v in sdata.iteritems()]
    seasons.sort(key=itemgetter(1,2))
    return seasons


def main():
    """
    Go through the squash data dictionary and add elo ratings for each
    player.

    Adds a 'last_elo' field for the player data, corresponding to the current
    rating and an 'elo' field to each season for that seasons rating.

    Also prints the highest elo ranking and the player and season where it
    occurred.

    Writes the new dictionary back to the original json file.
    """
    squash_data = None
    with open('squash_data.json', 'r') as ifile:
        squash_data = json.load(ifile)

    ## Set everybody's default elo to the base
    reset = True
    for name in squash_data['players'].keys():
        if reset:
            squash_data['players'][name]['last_elo'] = BASEELO
        else:
            squash_data['players'][name].setdefault('last_elo', BASEELO)

    seasons = sort_seasons(squash_data['seasons'])
    max_elo, max_name, max_season = BASEELO, None, None

    for season,_,_ in seasons:
        sdata = squash_data['seasons'][season]
        # Keep track of all played matches this season
        counted_matches = {}
        for pname in sdata['players']:
            pdata = squash_data['players'][pname]
            matches = pdata['seasons'][season]['matches']
            elo1 = pdata['seasons'][season].setdefault('elo', pdata['last_elo'])
            for pname2, result in matches.iteritems():
                # Avoid double counting
                if ((pname, pname2) in counted_matches or
                    (pname2, pname) in counted_matches): continue
                pdata2 = squash_data['players'][pname2]

                elo2 = pdata2['seasons'][season].setdefault('elo', pdata2['last_elo'])
                elo1, elo2 = calculate_elo(pdata['last_elo'], pdata2['last_elo'], result)

                # Store the latest elo rating
                pdata['last_elo']  = elo1
                pdata2['last_elo'] = elo2
                # Store the elo for this season
                pdata['seasons'][season]['elo']  = elo1
                pdata2['seasons'][season]['elo'] = elo2

                if elo1 > max_elo:
                    max_name = pname
                    max_season = season
                    max_elo = elo1
                if elo2 > max_elo:
                    max_name = pname2
                    max_season = season
                    max_elo = elo2

                counted_matches[(pname, pname2)] = None


    print max_elo, max_name, max_season

    ## Dump to json file
    with open('squash_data.json', 'w') as ofile:
        json.dump(squash_data, ofile, indent=2, sort_keys=True)

if __name__ == '__main__':
    main()
