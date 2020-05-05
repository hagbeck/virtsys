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
import collections
import requests
import simplejson as json
import urllib
from urllib.parse import quote_plus
import xmltodict

# TODO
# TODO - read rvko
# TODO - traverse rvko and get the manifestation count via solr query for each notation

solr_endpoint = 'http://localhost:8983/solr'


def url_encode(query=''):

    return quote_plus(query)


def build_node_data(node):

    notation = url_encode(node['@notation'])

    # TODO get manifestation counter from solr index 'rvk': http://localhost:8983/solr/rvk/select?q=rvk_notation%3A%22QL%20400%20-%20QL%20710%22&rows=1&start=0
    solr_request = '%s/rvk/select?q=%s&rows=1&start=0' % (solr_endpoint, urllib.parse.quote('rvk_notation:"%s"' % notation))
    response = requests.get(url=solr_request)

    if response.status_code == 200:

        solr_result = json.loads(response.content.decode('utf-8'))
        cnt = solr_result['response']['numFound']
    else:
        cnt = 0

    node_data = {'notation': notation, 'label': node['@benennung'], 'cnt': cnt}

    # build children
    if node.get('children'):

        children = []

        if type(node['children']['node']) is list:
            for child in node['children']['node']:
                children.append(build_node_data(child))
        elif type(node['children']['node']) is collections.OrderedDict:
            children.append(build_node_data(node['children']['node']))

        node_data['children'] = children

    return node_data


if __name__ == '__main__':

    # TODO update process for rvko.xml
    rvko_data = 'data/rvk/rvko_2018_4.xml'

    rvk_tree_data = 'data/rvk/rvk.tree.json'

    rvk_tree = []

    with open(rvko_data, 'rb') as thedata:

        # read rvko XML data
        try:
            data = xmltodict.parse(thedata)['classification_scheme']
        except Exception as e:
            data = None
            print("ERROR: Couldn't read %s as XML." % rvko_data)
            print(e)

    if data:

        for data_node in data['node']:
            rvk_tree.append(build_node_data(data_node))

    if rvk_tree:
        with open(rvk_tree_data, 'w') as thedata:

            json.dump({'rvk_tree': rvk_tree}, thedata, indent=2)


