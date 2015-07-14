import json
import gzip
import sys
import math
import Levenshtein

import _mysql
import MySQLdb as mdb

INCOMING_LINK_NORM = 1000
EXTERNAL_LINK_NORM = 100
PAGE_SIZE_NORM = 50000
HEADING_NORM = 50
REDIRECT_NORM = 100

INCOMING_LINK_WEIGHT = 0.6
EXTERNAL_LINK_WEIGHT = 0.3
PAGE_SIZE_WEIGHT = 0.1
HEADING_WEIGTH = 0.2
REDIRECT_WEIGTH = 0.1

DISAMB_PENALITY = 0.3

DISAMB_TEMPLATE = "Template:Disambig"

# produce a weight from 0 to SCORE_INT_FACTOR
SCORE_INT_FACTOR = 10000

# multiplyer to the lenvenshtein ratio
REDIRECT_PENALITY_FACT = 1

# lenvenshtein ratio threshold, redirects with ratio higher
# are kept within the same suggestion
REDIRECT_LEVENSHTEIN_DISTANCE = 0.6

def score(page, penality):
	"Calculate score of page"
	normalizedIncomingLinks = math.log(page['incoming_links'] + 2) / math.log(INCOMING_LINK_NORM)
	if(normalizedIncomingLinks > 1):
		normalizedIncomingLinks = 1

	normalizedExternalLinks = math.log(len(page['external_link']) + 2) / math.log(EXTERNAL_LINK_NORM)
	if(normalizedExternalLinks > 1):
		normalizedExternalLinks = 1

	normalizedPageSize = math.log(page['text_bytes'] + 2) / math.log(PAGE_SIZE_NORM)
	if(normalizedPageSize > 1):
		normalizedPageSize = 1

	normalizedHeading = math.log(len(page['heading']) + 2) / math.log(HEADING_NORM)
	if(normalizedHeading > 1):
		normalizedHeading = 1

	normalizedRedirects = math.log(len(page['redirect']) + 2) / math.log(REDIRECT_NORM)
	if(normalizedRedirects > 1):
		normalizedRedirects = 1

	disambPenality = 1
	if(DISAMB_TEMPLATE in page['template']):
		disambPenality = DISAMB_PENALITY

	score = 0
	score += normalizedIncomingLinks * INCOMING_LINK_WEIGHT
	score += normalizedExternalLinks * EXTERNAL_LINK_WEIGHT
	score += normalizedPageSize * PAGE_SIZE_WEIGHT
	score += normalizedHeading * HEADING_WEIGTH
	score += normalizedRedirects * REDIRECT_WEIGTH
	score /= INCOMING_LINK_WEIGHT + EXTERNAL_LINK_WEIGHT + PAGE_SIZE_WEIGHT + HEADING_WEIGTH + REDIRECT_WEIGTH
	score *= penality
	score *= disambPenality
	detail = {
		"final":int(score * SCORE_INT_FACTOR),
		"score": score,
		"disambPenality": disambPenality,
		"distancePenality": penality,
		"redirect": normalizedRedirects,
		"heading":normalizedHeading,
		"pageSize":normalizedPageSize,
		"extLink":normalizedExternalLinks,
		"incLinks":normalizedIncomingLinks
	}
	return detail;

def levenshteinExplosion(page):
	orphans = list(page['redirect'])
	candidates = {}
	candidates[page['title']] = {"name": page['title'], "input": [page['title']], "penality": 1}
	while len(orphans) > 0:
		r = orphans.pop()
		rt = r['title']
		added = False;
		dist = Levenshtein.ratio(page['title'], rt)
		penality = dist * REDIRECT_PENALITY_FACT
		for k,c in candidates.iteritems():
			ct = k
			dist = Levenshtein.ratio(ct, rt)
			if dist > REDIRECT_LEVENSHTEIN_DISTANCE:
				candidates[k]["input"].append(rt)
				added = True
		if not added :
			candidates[rt] = {"name": rt, "input": [rt], "penality":penality};
	return candidates;

def dumpReader(dumpFile, geoDic, callback):
	with gzip.open(dumpFile, 'rb') as f:
		l = 0
		pageId = 0
		for line in f:
			l += 1;
			page = json.loads(line)
			if(l%2 == 1):
				pageId = page['index']['_id']
				continue
			if int(pageId) in geoDic:
				page['geo'] = geoDic[int(pageId)]
			callback(pageId, page)

def suggestConverter(pageId, page):
	"Export suggests in ES bulk format"
	exploded = levenshteinExplosion(page);
	for k,c in exploded.iteritems():
		name = c["name"]
		if(c["penality"] < 1):
			name = c["name"] + " (" + page["title"] + ")";
		scoreDetail = score(page, c["penality"])
		weight = scoreDetail['final']
		suggest = {
			"page": page['title'],
			"suggest": {
				"input": c["input"],
				"output": name,
				"payload": {
					"pageId": pageId,
					"weight": weight,
					"inputs": c["input"],
					"score": scoreDetail
				},
				"weight": weight
			},
			"suggest-nopos": {
				"input": c["input"],
				"output": name,
				"payload": {
					"pageId": pageId,
					"weight": weight,
					"inputs": c["input"],
					"score": scoreDetail
				},
				"weight": weight
			}
		}
		if 'geo' in page:
			suggest['suggest-geo'] = {
				"input": c["input"],
				"output": name,
				"context" : { 'location': page['geo'] },
				"payload": {
					"pageId": pageId,
					"weight": weight,
					"inputs": c["input"],
					"score": scoreDetail
				},
				"weight": weight
			};
			suggest['suggest-nopos-geo'] = {
				"input": c["input"],
				"output": name,
				"context" : { 'location': page['geo'] },
				"payload": {
					"pageId": pageId,
					"weight": weight,
					"inputs": c["input"],
					"score": scoreDetail
				},
				"weight": weight
			};
		print(json.dumps({"index":{"_id":name, "_type":"page"}}))
		print(json.dumps(suggest))

def statsExtractor(pageId, page):
	"Export raw stats"
	print(str(pageId) + "," + str(page['incoming_links']) + "," + str(len(page['external_link'])) + "," + str(page['text_bytes']) + "," + str(len(page['heading'])) + "," + str(len(page['redirect'])) + "," + str(DISAMB_TEMPLATE in page['template']));

#print(str(Levenshtein.ratio('United States', 'EEUU')))
#exit(1)
def dumpStats(dumpFile):
	print("pageId,incomingLinks,externalLinks,bytes,headings,redirects,disamb");
	dumpReader(sys.argv[1], {}, statsExtractor)

def getGeo():
	con = mdb.connect('localhost', 'root', '', 'simplewiki_geo');
	cursor = con.cursor()
	cursor.execute("SELECT gt_page_id,gt_lat,gt_lon FROM geo_tags")
	geoDic = {}
	for row in cursor:
		geoDic[row[0]] = {'lat' : row[1], 'lon' : row[2]}
	return geoDic

reload(sys)
sys.setdefaultencoding('utf-8')

geoDic = {}
geoDic = getGeo()
if(len(sys.argv) > 2 and sys.argv[2] == "-s"):
	dumpStats(sys.argv[1])
else:
	dumpReader(sys.argv[1], geoDic, suggestConverter)

