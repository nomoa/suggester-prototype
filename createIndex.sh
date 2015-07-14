curl -X PUT localhost:10200/title_suggest
curl -X PUT localhost:10200/title_suggest/page/_mapping -d '{
	"page" : {
		"properties" : {
			"page" : { "type" : "string" },
			"suggest" : {
				"type" : "completion",
				"index_analyzer" : "standard",
				"search_analyzer" : "standard",
				"payloads" : true
			},
			"suggest-nopos": {
				"type" : "completion",
				"index_analyzer" : "stop",
				"search_analyzer" : "stop",
				"payloads" : true,
				"preserve_separators" : false,
				"preserve_position_increments" : false
			},
			"suggest-geo" : {
				"type" : "completion",
				"index_analyzer" : "standard",
				"search_analyzer" : "standard",
				"payloads" : true,
				"context": {
					"location": {
						"type": "geo",
						"precision": ["1km", "10km", "50km", "100km"],
						"neighbors": true
					}
				}
			},
			"suggest-nopos-geo": {
				"type" : "completion",
				"index_analyzer" : "stop",
				"search_analyzer" : "stop",
				"payloads" : true,
				"preserve_separators" : false,
				"preserve_position_increments" : false,
				"context": {
					"location": {
						"type": "geo",
						"precision": ["1km", "10km", "50km", "100km"],
						"neighbors": true
					}
				}
			}
		}
	}
}'

