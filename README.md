# Suggester Prototype

This is is a rough prototype (quick and dirty) to evaluate the elasticsearch
completion suggester.

## Content

* readDump.py: main tool to read cirrus dump
  * Creates the suggester index in bulk format
  * Extracts stats and writes a CSV file
* index.html: frontend
  * Speaks directly with elasticsearch
  * Simulates aggregations that should be done in the backend
* createIndex.sh: script that creates the suggester index
* levenshtein.js & jquery-ui: JavaScript libraries used by index.html

## How to build the index

* Grab a cirrus dump somewhere
  * Simplewiki from beta is available from Deployment-bastion.deployment-prep.eqiad.wmflabs:/data/project/cirrus-dump/dump-simplewiki-content.gz
* Import localisation data
  * Get data from `https://dumps.wikimedia.org/simplewiki/20150702/simplewiki-20150702-geo_tags.sql.gz`
  * Import this data to your local mysql in the db `simplewiki_geo`
  * Or comment line 203 in readDump.py to disable geo context
* Create the suggester index:
```shell
sh createIndex.sh
```
* Convert and Import the suggester data:
```shell
python readDump.py /plat/cirrus-dump/dump-simplewiki-content.gz | parallel --pipe -L 2 -N 2000 -j3 --blocksize 3000000 'curl -s http://localhost:10200/title_suggest/_bulk --data-binary @- > /dev/null'
```
* Open index.html

## Configure Elasticsearch
CORS must be enable to allow the browser to talk directly to elasticsearch. Add this to your /etc/elasticsearch/elasticsearch.yml :

```
http.cors.enabled : true
http.cors.allow-origin : "*"
http.cors.allow-methods : OPTIONS, HEAD, GET, POST, PUT, DELETE
http.cors.allow-headers : X-Requested-With,X-Auth-Token,Content-Type, Content-Length
```

## Export scoring stats
You can export raw values used by the score function by running :
```shell
python readDump.py /plat/cirrus-dump/dump-simplewiki-content.gz -s > score_stats.csv
```
