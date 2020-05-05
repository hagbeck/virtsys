# The MIT License
#
#  Copyright 2018-2020 Hans-Georg Becker <https://orcid.org/0000-0003-0432-294X>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
import simplejson as json

from graphdb_connector import get_request, delete_request, post_request

import config_graphdb as config

named_graph_for_rvk = 'http://data.ub.tu-dortmund.de/graph/rvk'

# get repostitory status:
#  curl -X GET --header 'Accept: application/json' 'http://pc233:7200/rest/repositories/VirtuelleSystematik/size'
print(get_request(endpoint=config.graphdb_rest_repository_endpoint, function='size'))

# cleanup target graphs
#  curl -X DELETE --header 'Accept: text/plain' 'http://pc233:7200/repositories/VirtuelleSystematik/statements?context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fcg%2Fdata%3E'
print(delete_request(endpoint=config.graphdb_repository_endpoint, function='statements', param_string='context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Frvk%3E'))
print(get_request(endpoint=config.graphdb_rest_repository_endpoint, function='size'))

# for each file in ttl_data:
#  curl -X POST --header 'Content-Type: application/json' 'http://pc233:7200/rest/data/import/server/VirtuelleSystematik'
data_template = {
  "fileNames": [],
  "importSettings": {
    "baseURI": "",
    "context": "",
    "data": "",
    "forceSerial": True,
    "format": "",
    "message": "",
    "name": "",
    "parserSettings": {
      "failOnUnknownDataTypes": True,
      "failOnUnknownLanguageTags": True,
      "normalizeDataTypeValues": True,
      "normalizeLanguageTags": True,
      "preserveBNodeIds": True,
      "stopOnError": True,
      "verifyDataTypeValues": True,
      "verifyLanguageTags": True,
      "verifyRelativeURIs": True,
      "verifyURISyntax": True
    },
    "replaceGraphs": [],
    "status": "PENDING",
    "timestamp": 0,
    "type": "",
    "xRequestIdHeaders": ""
  }
}

data = data_template.copy()
data['fileNames'].append('rvk')
data['importSettings']['baseURI'] = config.base_uri
data['importSettings']['context'] = named_graph_for_rvk
print(data)
print(post_request(endpoint=config.graphdb_rest_repository_import_endpoint, function='', data=json.dumps(data)))
