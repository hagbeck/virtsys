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
from os import listdir
from os.path import isfile, join
import simplejson as json
import subprocess
from urllib.parse import quote_plus
import xmltodict

import config_rvk as config


def url_encode(query=''):

    return quote_plus(query)


def build_index_data(node):

    json_data = ''

    document = {'id': url_encode(node['@notation']), 'notation': node['@notation'], 'label': node['@benennung']}

    if node.get('register'):

        document['register'] = node['register']

    json_data += '%s\n' % json.dumps(document)

    # build children
    if node.get('children'):
        if type(node['children']['node']) is list:
            for child in node['children']['node']:
                json_data += build_index_data(child)
        elif type(node['children']['node']) is collections.OrderedDict:
            json_data += build_index_data(node['children']['node'])

    return json_data


def start_solrbulk(data_dir=''):
    """ start indexing using solrbulk """

    # index data using solrbulk
    solr_index_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

    idx = 1
    for file in solr_index_files:
        # start solrbulk: https://github.com/miku/solrbulk
        # solrbulk -verbose -server https://localhost:7007/solr/biblio solr_add_data.json
        if idx == 1:
            result = subprocess.run(["/usr/sbin/solrbulk", "-purge", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)
        else:
            result = subprocess.run(["/usr/sbin/solrbulk", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)

        print(result)

        idx += 1


if __name__ == '__main__':

    with open(config.RVK_XML, 'rb') as thedata:

        # read rvko XML data
        try:
            data = xmltodict.parse(thedata)['classification_scheme']
        except Exception as e:
            data = None
            print("ERROR: Couldn't read %s as XML." % config.RVK_XML)
            print(e)

    if data:

        with open('%srvk.index.json' % config.SOLR_DATA, 'w') as thedata:

            for data_node in data['node']:
                thedata.write(build_index_data(data_node))

        start_solrbulk(data_dir=config.SOLR_DATA)
