#! /usr/bin/env python
import sys
import re
import urllib2
import unicodedata

from bs4 import BeautifulSoup

BASEURL = "http://club-squash.web.cern.ch/club-squash/archives/%s"
EMPTYRESULT = ' - '

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

def get_name(tag):
	global PNAMES
	text = tag.get_text().strip().lower()
	text = text.replace('\n', '')
	text = text.replace('\r', '')
	text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')
	text = re.sub(r'home','', text)
	text = re.sub(r'(\s?-?\s?\(?(1st|2nd|3rd|[1-9]{1}th)\s+to\s+finish\)?)', '', text)
	text = re.sub(r'\s+-$', '', text, re.MULTILINE)
	text = re.sub(r'\s+out$', '', text, re.MULTILINE)
	text = re.sub(r'[\#\+0-9\)\(\.]','', text)
	text = re.sub(r'\s{2,}',' ', text)

	text = text.replace('unavailable', '')
	text = text.replace('out for summer', '')
	text = text.replace(' ?', '')
	text = text.strip()

	key = text.replace(' ', '')
	return PNAMES.setdefault(key, text.title())

def get_result(tag):
	res = re.match(r'(\d)-(\d)', tag.get_text().strip()) # '3-1', '2-3', etc.
	if res:
		return str(tag.get_text().strip())
	else:
		return EMPTYRESULT

def invert_result(result):
	if result == EMPTYRESULT: return result
	if result in ['1', '2', '3']: return '0'
	score = re.match(r'(\d)-(\d)', result)
	try:
		return '%d-%d' % (int(score.group(2)), int(score.group(1)))
	except ValueError, e:
		print "Wrong result format? %s" % result
		raise e

def get_division(tag):
	# Extract the division rank
	div_text = re.sub(r'[\n\r]+','', tag.get_text())
	rank_match = re.match(r'^Division\s*([\d]{1,2}).?$', div_text)
	if not rank_match:
		print 'Invalid division header:"%s"' % repr(tag.get_text())
		raise RuntimeError('Invalid division header')
	rank = int(rank_match.group(1))
	return rank

def process_page(url, printout=False, verbose=False):
	## Load page
	print '... processing %s' % url
	page_request = urllib2.urlopen(url)

	## Parse html
	soup = BeautifulSoup(page_request, 'html.parser')

	divisions   = {} # div rank -> list of player names
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
	for table in soup.find_all('table'):
		rows_iter = iter(table.find_all('tr'))
		for row in rows_iter:
			# Check if this starts a new division or not
			div = row.find('td', string=re.compile('Division'))
			if div:
				rank = get_division(div)

			# Player rows always start with a field containing A,B,C,...
			elif row.find('td', string=re.compile(r'\b[A-G]{1}\b')):
				# Player entry is then the second one in the row
				player_name = get_name(row.find_all('td')[1])
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
			pos = player_names.index(name1)
			match_results = player_rows[name1].find_all('td')[2:division_size+2]
			for pos2,entry in zip(range(pos+1, division_size), match_results[pos+1:]):
				name2 = player_names[pos2]
				result = get_result(entry)
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

	print ('  %2d divisions, %3d players, %3d played matches' %
		       (len(divisions), len(results), len(matches)))

	if verbose:
		for divrank,names in sorted(divisions.iteritems()):
			print '----- Division %d' % divrank
			for name in names:
				print '%-30s: ' % name, results[name]


	if printout:
		for divrank, names in divisions.iteritems():
			print 50*'-'
			print 'Division %d' % divrank
			for name in names:
				print '%-30s %s' % (name, ' '.join(results[name]))
		print 50*'-'


	return divisions, matches

def process_archives(url):
	## Load page
	page_request = urllib2.urlopen(url)

	## Parse html
	soup = BeautifulSoup(page_request, 'html.parser')
	hrefs = soup.find_all('a', href=re.compile('archives'))
	sites_to_process = [l['href'].replace('archives/','') for l in hrefs]

	failed_sites = []
	total_played_matches = 0
	valid_seasons = []
	all_players = set()
	for site in sites_to_process:

		## DEBUG
		# if not site in [u'08-09.html']: continue

		try:
			players, matches = process_page(BASEURL % site)

			# Store all players
			for div,names in players.iteritems():
				for name in names:
					all_players.add(name)

			# Store valid seasons
			if len(matches):
				valid_seasons.append(site)

			# Count number of matches
			total_played_matches += len(matches)

		except RuntimeError, e:
			print e
			if '0708' in site.lower() or 'summer' in site.lower(): continue
			failed_sites.append(site)
		except StopIteration:
			failed_sites.append(site)
		except urllib2.HTTPError, e:
			print e
			failed_sites.append(site)

	print 40*'='
	print 'Extracted %d played matches in %d seasons' % (total_played_matches, len(valid_seasons))
	print 'Found %d individual players' % len(all_players)
	print 'Failed for %d sites:' % len(failed_sites), failed_sites
	print 40*'='

def main():
	get_name_dictionary('player_names.txt')
	process_archives('http://club-squash.web.cern.ch/club-squash/resultats.html')


if __name__ == '__main__':
	main()



