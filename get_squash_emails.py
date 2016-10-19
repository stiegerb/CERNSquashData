#! /usr/bin/env python
import os
import re
import urllib2
import unicodedata
import argparse
import pickle

from bs4 import BeautifulSoup
from collections import defaultdict

_cachefiles = []
def cachify(func):
    """
    Simple decorator to store the output of a function to cache, then read
    the cache instead of calling the function again.
    """
    global _cachefiles
    cachefile = '.'+func.__name__+'.cache'
    _cachefiles.append(cachefile)

    def cached_func(*args):
        if not os.path.exists(cachefile):
            value = func(*args)
            with open(cachefile, 'w') as ofile:
                pickle.dump(value, ofile, pickle.HIGHEST_PROTOCOL)
            return value
        else:
            with open(cachefile, 'r') as ifile:
                value = pickle.load(ifile)
            return value

    return cached_func

def get_name(text):
    """Clean the text of a player name field"""
    text = text.strip().lower()
    text = text.replace('\n', '')
    text = text.replace('\r', '')
    # Replace unicode characters by ascii ones
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')
    # Remove '#','(',')', and numbers
    text = re.sub(r'[\#\+0-9\)\(\.]','', text)
    # Replace double spaces by single spaces
    text = re.sub(r'\s{2,}',' ', text)

    return text.strip().title()

def reduce_name(name):
    return name.lower().replace(' ', '')

def get_division(text):
    """Extract the division rank from a string like 'Division 5'"""
    div_text = re.sub(r'[\n\r]+','', text)
    rank_match = re.match(r'.*\bDivision\s*([\d]{1,2}).?$', div_text)
    if not rank_match:
        print 'Invalid division header:"%s"' % repr(text)
        raise RuntimeError('Invalid division header')
    rank = int(rank_match.group(1))
    return rank

@cachify
def load_divisions(url="http://club-squash.web.cern.ch/club-squash/leagues.htm", verbose=False):
    """
    Extract the players from the squash league table
    First open the url, then parse the html using BeautifulSoup.

    The code looks for a table that contains a row with 'Division' in it.
    Then looks for rows with players and results.

    Returns a dictionary the players for each division
    """
    page_request = urllib2.urlopen(url)
    soup = BeautifulSoup(page_request, 'html.parser')

    divisions = defaultdict(list) # div rank -> list of player names

    ## Collect all divisions and players in each division
    rank = -1
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

                divisions[rank].append(player_name)

    # Remove empty player names
    for divrank,names in divisions.iteritems():
        divisions[divrank] = [n for n in names if len(n)]
    # Remove divisions with no players
    divisions = {r:ps for r,ps in divisions.iteritems() if len(ps)}

    if verbose:
        for divrank,names in sorted(divisions.iteritems()):
            print '----- Division %d' % divrank
            for name in names:
                print '%-30s' % name

    return divisions

@cachify
def load_emails(url="http://club-squash.web.cern.ch/club-squash/club.html"):
    page_request = urllib2.urlopen(url)
    soup = BeautifulSoup(page_request, 'html.parser')

    emails = {}
    email_item = soup.find('td', { 'class':'MainContainerCell'}).find_all('p')[1]
    for line in email_item.text.split('\n'):
        line = line.strip()
        if not len(line): continue

        name, emailantispam = line.split('::')

        user,host = re.match(r'([\.\-\w\d]*)AT([\.\-\w\d]*)', emailantispam.strip()).groups()
        email = '%s@%s' % (user.replace('DOT', '.'), host.replace('DOT', '.'))

        emails[reduce_name(name)] = email

    return emails

def get_player_email(name, emails):
    email = emails.get(reduce_name(name))
    if not email:
        firstname, lastname = (x.lower() for x in name.strip().rsplit(' ', 1))
        matching_keys = [k for k in emails.keys() if lastname in k or firstname in k]
        if len(matching_keys) == 1:
            return emails[matching_keys[0]]

        elif len(matching_keys) > 1:
            less_matching_keys = [k for k in matching_keys if lastname in emails[k]]
            if len(less_matching_keys) == 1:
                return emails[less_matching_keys[0]]

            else:
                return "multiple entries: %s" % ' '.join([emails[n] for n in matching_keys])

    return email if email else 'not found'

def main():
    parser = argparse.ArgumentParser(
        description="Crawl the CERN squash club archives and get match data")
    parser.add_argument('-v', '--verbose', help='Verbose mode', action="store_true")
    parser.add_argument('-r', '--refresh', help='Reload caches', action="store_true")
    parser.add_argument('division', help='Division', type=int)
    args = parser.parse_args()

    divisions = load_divisions()
    emails = load_emails()

    if args.refresh:
        print '...removing cachefiles:',
        for cfile in _cachefiles:
            print cfile,
            os.remove(cfile)
        print ''

    if not args.division in divisions.keys():
        print "Division %d not found" % args.division
        return -1

    for name in divisions[args.division]:
        email = get_player_email(name, emails)
        print '%-40s : %s' % (name, email)

    return 0


if __name__ == '__main__':
    main()

