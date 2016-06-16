## CERN squash club data mining

http://club-squash.web.cern.ch/club-squash/

Collection of scripts to data mine the archives of the CERN squash club. Extract the names of players and the matches they played in each season.

Run `squash_crawl.py` to extract the data and store it in `squash_data.json`.

`calculate_elo.py` will read the data, calculate Elo rankings for each player and add it to the json file.

A few other scripts are there to print tables and individual player stats.
