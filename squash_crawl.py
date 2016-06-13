#! /usr/bin/env python
import sys
import re
import urllib2
import unicodedata

from bs4 import BeautifulSoup

from pprint import pprint

BASEURL = "http://club-squash.web.cern.ch/club-squash/archives/%s"
try:
	SEASON = sys.argv[1]
except IndexError:
	SEASON = '1605'

EMPTYRESULT = ' - '

PNAMES = None
def get_name_dictionary(filename):
	global PNAMES
	if not PNAMES:
		PNAMES = {}
		with open(filename, 'r') as ifile:
			# PNAMES = dict([tuple(l.split(' ', 1)) for l in ifile if len(l)])
			for line in ifile:
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

	# text = text.replace('vidal', '')
	# text = text.replace('packagea', '')
	# text = text.replace('zein assi', 'zein-assi')
	# text = text.replace('alanackroyd', 'alan ackroyd')
	# text = text.replace('alexanderpicolet pack a', 'alexander picolet')
	# text = text.replace('alexander picolet packagea', 'alexander picolet')
	# text = text.replace('andersunnervik', 'anders unnervik')
	# text = text.replace('andersunnervik', 'anders unnervik')
	# text = text.replace('spears', 'speirs')
	# text = text.replace('angusspears', 'angus speirs')
	# text = text.replace('angusspeirs', 'angus speirs')
	# text = text.replace('antonyromero', 'antony romero')
	# text = text.replace('arunyachevalley', 'arunya chevalley')
	# text = text.replace('borjamanero', 'borja manero')
	# text = text.replace('brennangoddard', 'brennan goddard')
	# text = text.replace('brunobalhan', 'bruno balhan')
	# text = text.replace('carlosolivera', 'carlos olivera')
	# text = text.replace('carlos oliviera', 'carlos olivera')
	# text = text.replace('cathernine goodrich', 'catherine goodrich')
	# text = text.replace('christian carli', 'christian carli')
	# text = text.replace('dave whitacker', 'dave whittaker')
	# text = text.replace('davewhittaker', 'dave whittaker')
	# text = text.replace('davidnisbet', 'david nisbet')
	# text = text.replace('declancahill', 'declan cahill')
	# text = text.replace('don mc donald', 'don macdonald')
	# text = text.replace('donmacdonald', 'don macdonald')
	# text = text.replace('donmc donald', 'don macdonald')
	# text = text.replace('edgar mauricio fajardo hernandez', 'edgar fajardo-hernadez')
	# text = text.replace('edgar mauricio fajardo-hernandez', 'edgar fajardo-hernadez')
	# text = text.replace('eliseo duenos', 'eliseo perez-duenas')
	# text = text.replace('eliseoduenos', 'eliseo perez-duenas')
	# text = text.replace('eliseoperez-duenas', 'eliseo perez-duenas')
	# text = text.replace('florianliebenau', 'florian liebenau')
	# text = text.replace('fredricklaugier', 'fredrick laugier')
	# text = text.replace('gabrielmetral', 'gabriel metral')
	# text = text.replace('gerdabenedikt', 'gerda benedikt')
	# text = text.replace('german carrillo', 'german carrillo montoya')
	# text = text.replace('german montoya', 'german carrillo montoya')
	# text = text.replace('gert coelingh', 'gert-jan coelingh')
	# text = text.replace('gert-jan coehling', 'gert-jan coelingh')
	# text = text.replace('guillaume kantzmann', 'guillaume kautzmann')
	# text = text.replace('guillaumeduvaux', 'guillaume duvaux')
	# text = text.replace('guillaumeduvoux', 'guillaume duvaux')
	# text = text.replace('guycrockford', 'guy crockford')
	# text = text.replace('heribert castilla', 'heriberto castilla-valdez')
	# text = text.replace('hubertrammer', 'hubert rammer')
	# text = text.replace('ianturnbull', 'ian turnbull')
	# text = text.replace('ivolobmaier', 'ivo lobmaier')
	# text = text.replace('jakub mosciki', 'jakub moscicki')
	# text = text.replace('janelacy', 'jane lacy')
	# text = text.replace('jean-chrisophemartin', 'jean-christophe martin')
	# text = text.replace('jean-chrisophe martin', 'jean-christophe martin')
	# text = text.replace('jean-pierreneras', 'jean-pierre neras')
	# text = text.replace('juan palacios', 'juan palacio')
	# text = text.replace('juan knaster', 'juan knaster')
	# text = text.replace('jurgende jonghe', 'jurgen de jonghe')
	# text = text.replace('jurgen dejonghe', 'jurgen de jonghe')
	# text = text.replace('kacper szkudiarek', 'kacper szkudlarek')
	# text = text.replace('keithjones', 'keith jones')
	# text = text.replace('klausbarth', 'klaus barth')
	# text = text.replace('laurent theimer-liehard', 'laurent theimer-lienhard')
	# text = text.replace('lionelherblin', 'lionel herblin')

	return text.title()

def get_result(tag):
	res = re.match(r'(\d)-(\d)', tag.get_text().strip()) # '3-1', '2-3', etc.
	if res:
		return tag.get_text().strip()
	else:
		return EMPTYRESULT

def get_division(tag):
	# Extract the division rank
	rank_match = re.match(r'^Division\s[\n\r]?([\d]{1,2}).?$', tag.get_text())
	if not rank_match:
		print 'Invalid division header:"%s"' % repr(tag.get_text())
		raise RuntimeError('Invalid division header')
	rank = int(rank_match.group(1))
	return rank



def process_page(url, printout=False):
	## Load page
	print '... processing %s' % url
	page_request = urllib2.urlopen(url)

	## Parse html
	soup = BeautifulSoup(page_request, 'html.parser')

	players   = {} # div rank -> list of player names
	results   = {} # player name -> list of results
	matches   = {} # (name1, name2) -> result
	division_size = -1

	## First pass: collect all divisions and players in each division
	for table in soup.find_all('table'):
		rows_iter = iter(table.find_all('tr'))
		for row in rows_iter:
			# Check if this starts a new division or not
			div = row.find('td', string=re.compile('Division'))
			# FIXME This is not going to work if the cell doesn't read 'Division ..'
			if div:
				rank = get_division(div)

				# Extract the division size (once)
				if division_size < 0:
					res_cols = row.find_all('td', string=re.compile(r'\b[A-G]{1}\b'))
					division_size = len(res_cols)

				# Store the next N rows as player rows
				prows = [next(rows_iter) for _ in range(division_size)]

				# Player entry is always the second one in the row
				players[rank] = [get_name(r.find_all('td')[1]) for r in prows]

				# print '     players: %s' % ', '.join(players[rank])

				# Go through the rows and extract the match results
				for name,prow in zip(players[rank], prows):
					# Results start in 3rd position and we know how many to expect
					# However we can start at the position of the player+1 to avoid
					# double counting the matches.
					pos = players[rank].index(name)
					match_results = prow.find_all('td')[2:division_size+2]

					for pos2,entry in zip(range(pos+1, division_size), match_results[pos+1:]):
						player2_name = players[rank][pos2]
						# print '     vs. %-30s:' % player2_name,
						result = get_result(entry)
						# print result
						matches[(name, player2_name)] = result

					for entry in match_results:
						result = get_result(entry)
						results.setdefault(name, []).append(result)

				####### DEBUG
				# break

	# Remove empty player names
	for divrank,names in players.iteritems():
		players[divrank] = [n for n in names if len(n)]
	# Remove divisions with no players
	players = {r:ps for r,ps in players.iteritems() if len(ps)}
	results.pop('', None)
	matches.pop(('',''), None)
	# Remove empty matches
	matches = {k:m for k,m in matches.iteritems() if m != EMPTYRESULT}

	print ('  %d divisions of size %d, (%d played matches)' %
		       (len(players), division_size, len(matches)))

	try:
		# Make sure nothing was filled in the -1 rank
		assert players.get(-1, None) is None
		# Make sure we found a division size
		assert division_size > 0
		# Make sure all divisions are the same size
		# assert all([len(p) == division_size for p in players.values()])
	except AssertionError:
		if division_size > 0:
			pprint(players)
		else:
			print "No valid divisions found"
			raise RuntimeError('Invalid format')

	if printout:
		for divrank, names in players.iteritems():
			print 50*'-'
			print 'Division %d' % divrank
			for name in names:
				print '%-30s %s' % (name, ' '.join(results[name]))
		print 50*'-'


	return players, matches

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
		try:
			players, matches = process_page(BASEURL % site)
		except RuntimeError, e:
			failed_sites.append(site)
		except StopIteration:
			failed_sites.append(site)
		except urllib2.HTTPError, e:
			print e
			failed_sites.append(site)

		# Store all players
		for div,names in players.iteritems():
			for name in names:
				all_players.add(name)

		# Store valid seasons
		if len(matches):
			valid_seasons.append(site)

		# Count number of matches
		total_played_matches += len(matches)
	print 40*'='
	print 'Extracted %d played matches in %d seasons' % (total_played_matches, len(valid_seasons))
	print 'Found %d individual players' % len(all_players)
	# print 'Failed for %d sites:' % len(failed_sites), failed_sites
	print 40*'='
	for name in sorted(all_players): print repr(name)
	with open('player_names.txt', 'w') as ofile:
		for name in all_players:
			ofile.write('%s\n'%name)
		ofile.write('\n')
	print 40*'='

def main():
	get_name_dictionary('player_names.txt')
	process_archives('http://club-squash.web.cern.ch/club-squash/resultats.html')


if __name__ == '__main__':
	main()



