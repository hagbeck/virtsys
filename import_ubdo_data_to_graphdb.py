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
from urllib.parse import unquote_plus

import requests
import simplejson as json

graphdb_repository_endpoint = 'http://localhost:7200/repositories/VirtuelleSystematik'
graphdb_rest_repository_endpoint = 'http://localhost:7200/rest/repositories/VirtuelleSystematik'
graphdb_rest_repository_import_endpoint = 'http://localhost:7200/rest/data/import/server/VirtuelleSystematik'

base_uri = 'http://data.ub.tu-dortmund.de/resources/'

named_graph_for_items = 'http://data.ub.tu-dortmund.de/graph/ubdo/items'
named_graph_for_manifestations = 'http://data.ub.tu-dortmund.de/graph/ubdo/manifestations'
named_graph_for_complex_works = 'http://data.ub.tu-dortmund.de/graph/ubdo/complex_works'
named_graph_for_serial_works = 'http://data.ub.tu-dortmund.de/graph/ubdo/serial_works'


def __get_request(endpoint='', function=''):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if function:
        function = '/' + function

    response = requests.get('%s%s' % (endpoint, function), headers={'accept': 'application/json'})
    status = response.status_code
    if status == 200:

       return response.content.decode("utf-8")

    else:
        raise ImportError('Getting data failed: %s - %s' % (status, response.content.decode("utf-8")))


def __post_request(endpoint='', function='', data=None):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if not data:
        raise ValueError('data undefined!')

    if function:
        function = '/' + function

    response = requests.post('%s%s' % (endpoint, function), headers={'content-type': 'application/json'}, data=data)
    status = response.status_code
    if 200 <= status <= 299:

       return response.content.decode("utf-8")

    else:
        raise ImportError('Getting data failed: %s - %s' % (status, response.content.decode("utf-8")))


def __delete_request(endpoint='', function='', param_string=''):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if function:
        function = '/' + function

    if param_string and not param_string.startswith('?'):
        param_string = '?' + param_string

    response = requests.delete('%s%s%s' % (endpoint, function, param_string), headers={'accept': 'text/plain'})
    status = response.status_code
    if 200 <= status <= 299:

       return 'Deleted: %s - %s' % (unquote_plus(param_string.split('=')[1]), response.content.decode("utf-8"))

    else:
        raise ImportError('Deleting data failed: %s - %s' % (status, response.content.decode("utf-8")))


# get repostitory status:
#  curl -X GET --header 'Accept: application/json' 'http://pc233:7200/rest/repositories/VirtuelleSystematik/size'
print(__get_request(endpoint=graphdb_rest_repository_endpoint, function='size'))

# cleanup target graphs
#  curl -X DELETE --header 'Accept: text/plain' 'http://pc233:7200/repositories/VirtuelleSystematik/statements?context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fcg%2Fdata%3E'
print(__delete_request(endpoint=graphdb_repository_endpoint, function='statements', param_string='context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fubdo%2Fitems%3E'))
print(__delete_request(endpoint=graphdb_repository_endpoint, function='statements', param_string='context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fubdo%2Fmanifestations%3E'))
print(__delete_request(endpoint=graphdb_repository_endpoint, function='statements', param_string='context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fubdo%2Fcomplex_works%3E'))
print(__delete_request(endpoint=graphdb_repository_endpoint, function='statements', param_string='context=%3Chttp%3A%2F%2Fdata.ub.tu-dortmund.de%2Fgraph%2Fubdo%2Fserial_works%3E'))
print(__get_request(endpoint=graphdb_rest_repository_endpoint, function='size'))

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
data['fileNames'].append('ubdo/items.ttl')
data['importSettings']['baseURI'] = base_uri
data['importSettings']['context'] = named_graph_for_items
print(data)
print(__post_request(endpoint=graphdb_rest_repository_import_endpoint, function='', data=json.dumps(data)))

data = data_template.copy()
data['fileNames'].append('ubdo/manifestations.ttl')
data['importSettings']['baseURI'] = base_uri
data['importSettings']['context'] = named_graph_for_manifestations
print(data)
print(__post_request(endpoint=graphdb_rest_repository_import_endpoint, function='', data=json.dumps(data)))

data = data_template.copy()
data['fileNames'].append('ubdo/complex_works.ttl')
data['importSettings']['baseURI'] = base_uri
data['importSettings']['context'] = named_graph_for_complex_works
print(data)
print(__post_request(endpoint=graphdb_rest_repository_import_endpoint, function='', data=json.dumps(data)))

data = data_template.copy()
data['fileNames'].append('ubdo/serial_works.ttl')
data['importSettings']['baseURI'] = base_uri
data['importSettings']['context'] = named_graph_for_serial_works
print(data)
print(__post_request(endpoint=graphdb_rest_repository_import_endpoint, function='', data=json.dumps(data)))
