#! /usr/bin/env python
import sys
import re
import json
import urllib2
import unicodedata
import argparse

from bs4 import BeautifulSoup
from collections import defaultdict

BASEURL = "http://club-squash.web.cern.ch/club-squash/archives/%s"
EMPTYRESULT = None

PNAMES = None
def get_name_dictionary(filename):
    global PNAMES
    if not PNAMES:
        PNAMES = {}
        with open(filename, 'r') as ifile:
            for line in ifile:
                if not len(line.strip()): continue
                key,value = tuple(line.strip().split(',', 1))
                PNAMES[key] = value.strip()
    return len(PNAMES)

def get_name(text):
    """
    Clean the text of a player name field, then look up the name
    in the dictionary, or store it there if it doesn't exist yet.

    FIXME: If the dictionary changes, we should write it back to the file.
    """
    global PNAMES
    if not PNAMES: get_name_dictionary('player_names.txt')
    text = text.strip().lower()
    text = text.replace('\n', '')
    text = text.replace('\r', '')
    # Replace unicode characters by ascii ones
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')
    # Sometimes there's a 'home' in there (from phone numbers, I assume)
    text = re.sub(r'home','', text)
    # Remove the '1st/2nd/3rd/... to finish'
    text = re.sub(r'(\s?-?\s?\(?(1st|2nd|3rd|[1-9]{1}th)\s+to\s+finish\)?)', '', text)
    # Remove trailing dashes
    text = re.sub(r'\s+-$', '', text, re.MULTILINE)
    # Remove trailing 'out's
    text = re.sub(r'\s+out$', '', text, re.MULTILINE)
    # Remove #,(,) and numbers
    text = re.sub(r'[\#\+0-9\)\(\.]','', text)
    # Replace double spaces by single spaces
    text = re.sub(r'\s{2,}',' ', text)

    # Some more custom cleaning
    text = text.replace('unavailable', '')
    text = text.replace('out for summer', '')
    text = text.replace(' ?', '')
    text = text.strip()

    key = text.replace(' ', '')
    return PNAMES.setdefault(key, text.title())

def get_result(text):
    """
    Process a result text to return either the clean string
    ('3-1', '2-3', etc.) or return the empty result if the match
    wasn't played.
    """
    text = text.strip()
    text = re.sub(r'[\n\r]+','', text)
    if re.match(r'(\d{1})-(\d{1})', text): # '3-1', '2-3', etc.
        return str(text)
    elif re.match(r'3', text): # 3
        return '3'
    else:
        return EMPTYRESULT

def invert_result(result):
    if result == EMPTYRESULT: return result
    if result in ['1', '2', '3']: return '0'
    score = re.match(r'(\d{1})-(\d{1})', result)
    try:
        return '%d-%d' % (int(score.group(2)), int(score.group(1)))
    except ValueError, e:
        print "Wrong result format? %s" % result
        raise e

def parse_result(result):
    """Return the game difference as an integer"""
    if result == EMPTYRESULT: return EMPTYRESULT
    try:
        score = re.match(r'(\d{1})-(\d{1})', result)
        return int(score.group(1))-int(score.group(2))
    except AttributeError:
        try:
            score = re.match(r'^(\d{1})$', result)
            return int(score.group(1))
        except AttributeError:
            return EMPTYRESULT

def get_division(text):
    """Extract the division rank from a string like 'Division 5'"""
    div_text = re.sub(r'[\n\r]+','', text)
    rank_match = re.match(r'.*\bDivision\s*([\d]{1,2}).?$', div_text)
    if not rank_match:
        print 'Invalid division header:"%s"' % repr(text)
        raise RuntimeError('Invalid division header')
    rank = int(rank_match.group(1))
    return rank

def process_page(url, printout=False, verbose=False):
    """
    Extract the players and matches from a single squash archive page
    First open the url, then parse the html using BeautifulSoup.

    The code looks for a table that contains a row with 'Division' in it.
    Then looks for rows with players and results.

    Returns two dictionaries, one with all the players for each division,
    one with all the results for each match played.
    """
    print '... processing %s' % url
    page_request = urllib2.urlopen(url)

    soup = BeautifulSoup(page_request, 'html.parser')

    divisions = {} # div rank -> list of player names
    results   = {} # player name -> list of results
    matches   = {} # (name1, name2) -> result

    ## Some seasons use a sub file to store the results
    if not len(soup.find_all('table')):
        frame = soup.find('link', href=re.compile(r'sheet[\d]+?\.htm'))
        suburl = '%s/%s' % (url.rsplit('/',1)[0], frame['href'])
        return process_page(suburl)

    ## First pass: collect all divisions and players in each division
    rank = -1
    player_rows = {} # name -> row
    found_table = False # Break after a valid table is found
    for table in soup.find_all('table'):
        if found_table: break
        for row in table.find_all('tr'):
            # Check if this starts a new division or not
            div = row.find('td', text=re.compile('Division'), recursive=False)
            if div:
                rank = get_division(div.get_text())
                found_table = True

            # Player rows always start with a field containing A,B,C,...
            elif row.find('td', text=re.compile(r'\b[A-G]{1}\b'), recursive=False):
                # Player entry is then either the second or third entry in the row
                player_name = get_name(row.find_all('td')[1].get_text())
                if re.match(r'\b[A-G]{1}\b', player_name): # There was an empty field first
                    player_name = get_name(row.find_all('td')[2].get_text())

                divisions.setdefault(rank,[]).append(player_name)
                player_rows[player_name] = row

    ## Second pass: now that we know the number of players in each division,
    ##              extract the results from the rows.
    for divrank, player_names in divisions.iteritems():
        division_size = len(player_names)

        if verbose:
            print 'Division %d with %d players:' % (divrank, len(player_names)),
            print ' %s' % ', '.join(player_names)

        # Go through the rows and extract the match results
        for name1 in player_names:
            # Results start in 3rd position and we know how many to expect
            # However we can start at the position of the player+1 to avoid
            # double counting the matches.
            ## FIXME: this breaks when player name is not in second field
            pos = player_names.index(name1)
            match_results = player_rows[name1].find_all('td')[2:division_size+2]
            for pos2,entry in zip(range(pos+1, division_size), match_results[pos+1:]):
                name2 = player_names[pos2]
                result = get_result(entry.get_text())
                matches[(name1, name2)] = result
                results.setdefault(name1, []).append(result)
                results.setdefault(name2, []).append(invert_result(result))
                if verbose:
                    print '  %-30s vs. %-30s:' % (name1,name2),
                    print result


    # Remove empty player names
    for divrank,names in divisions.iteritems():
        divisions[divrank] = [n for n in names if len(n)]
    # Remove divisions with no players
    divisions = {r:ps for r,ps in divisions.iteritems() if len(ps)}
    results.pop('', None)
    matches.pop(('',''), None)
    # Remove empty matches
    matches = {k:m for k,m in matches.iteritems() if m != EMPTYRESULT}
    # Check that there are no duplicate matches
    assert(set(matches.keys()).isdisjoint(set([(y,x) for x,y in matches.keys()])))

    print ('  %2d divisions, %3d players, %3d played matches' %
               (len(divisions), len(results), len(matches)))

    if verbose:
        for divrank,names in sorted(divisions.iteritems()):
            print '----- Division %d' % divrank
            for name in names:
                print '%-30s: ' % name, results.get(name)


    if printout:
        for divrank, names in divisions.iteritems():
            print 50*'-'
            print 'Division %d' % divrank
            for name in names:
                print '%-30s %s' % (name, ' '.join(results.get(name)))
        print 50*'-'


    return divisions, matches

SEASONS = None
def get_season(season_key, filename='seasons.txt'):
    global SEASONS
    if not SEASONS:
        SEASONS = {}
        with open(filename, 'r') as ifile:
            for line in ifile:
                if not len(line.strip()): continue
                key,value = tuple(line.strip().split(',', 1))
                year, month = tuple(value.strip().split(' '))
                assert(month in ['%02d'%d for d in range(1,13)])
                SEASONS[key] = (int(year), int(month))
        if not season_key in SEASONS:
            raise RuntimeError("Season key %s not in '%s' file, please add" % (season_key, filename))
    if 'summer' in season_key.lower():
        return (int('20' + season_key.lower().split('summer')[1]), 7)
    return SEASONS.get(season_key)

def process_archives(url, verbose=False):
    """
    Extract a list from the archives page and process each season.
    Then store the data in a dictionary and dump it to a json file.
    """
    page_request = urllib2.urlopen(url)

    soup = BeautifulSoup(page_request, 'html.parser')
    hrefs = soup.find_all('a', href=re.compile('archives'))
    sites_to_process = [l['href'].replace('archives/','') for l in hrefs]

    failed_sites = [] # Keep track if something went wrong
    total_played_matches = 0

    squash_data = defaultdict(dict)
    for site in sites_to_process:

        ## DEBUG
        # if not site in [u'05-06.html']: continue
        season = site.rsplit('.')[0] # drop the file ending

        try:
            divisions, matches = process_page(BASEURL % site, verbose=verbose)

            # Store all result for all players
            for div,names in divisions.iteritems():
                for name1 in names:
                    player_data = squash_data['players'].setdefault(name1, defaultdict(int))
                    player_data['n_seasons_played'] += 1

                    sdata = player_data.setdefault('seasons', {}).setdefault(season, {})
                    sdata['matches'] = {}
                    sdata['division'] = div
                    sdata['n_wins'] = 0
                    for name2 in names:
                        if name1 == name2: continue
                        result = matches.get((name1, name2))
                        if not result:
                            result = invert_result(matches.get((name2,name1)))
                        if result:
                            sdata['matches'][name2] = result
                            if parse_result(result) > 0:
                                sdata['n_wins'] += 1


                    player_data['n_total_wins'] += sdata['n_wins']
                    player_data['n_total_matches'] += len(sdata['matches'])

            # Store valid seasons
            if len(matches):
                season_data = squash_data['seasons'].setdefault(season, {})
                year, month = get_season(season)
                season_data['year'] = year
                season_data['month'] = month
                season_data['n_divisions'] = len(divisions)
                n_players = sum([len(n) for n in divisions.values()])
                season_data['n_players'] = n_players
                season_data['players'] = [n for ns in divisions.values() for n in ns]
                season_data['n_matches'] = len(matches)
                n_expected_matches = sum([len(n)*(len(n)-1)/2 for n in divisions.values()])
                season_data['completion_rate'] = float(len(matches)) / n_expected_matches

            # Count number of matches
            total_played_matches += len(matches)

        except RuntimeError, e:      # Something wrong with parsing the data
            print e
            # Skip summer leagues
            if '0708' in site.lower() or 'summer' in site.lower(): continue
            failed_sites.append(site)
        except AssertionError:       # Some inconsistency after processing the data
            failed_sites.append(site)
        except urllib2.HTTPError, e: # Something wrong with the url
            print e
            failed_sites.append(site)

    print 40*'='
    print ('Extracted %d played matches in %d seasons' %
                   (total_played_matches, len(squash_data['seasons'])))
    print 'Found %d individual players' % len(squash_data['players'])
    if failed_sites:
        print 'Failed for %d sites:' % len(failed_sites), failed_sites
    print 40*'='


    ## Write to json file
    with open('squash_data.json', 'w') as ofile:
        json.dump(squash_data, ofile, indent=2, sort_keys=True)

def main():
    parser = argparse.ArgumentParser(
        description="Crawl the CERN squash club archives and get match data")
    parser.add_argument('-v', '--verbose', help='Verbose mode', action="store_true")
    args = parser.parse_args()

    process_archives('http://club-squash.web.cern.ch/club-squash/resultats.html', verbose=args.verbose)


if __name__ == '__main__':
    main()



