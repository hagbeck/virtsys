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

import redis
import simplejson as json
import subprocess
from urllib.parse import quote_plus
import xmltodict

import config_rvk as config


def url_encode(query=''):

    return quote_plus(query)


def build_index_data(node, level):

    json_data = ''

    json_data = '"%s": {"label": "%s", "level": %s},\n' % (node['@notation'], node['@benennung'].replace('"', '\\"'), level)

    #json_data += '%s,\n' % json.dumps(document)

    # build children
    if node.get('children'):
        level += 1
        if type(node['children']['node']) is list:
            for child in node['children']['node']:
                json_data += build_index_data(child, level)
        elif type(node['children']['node']) is collections.OrderedDict:
            json_data += build_index_data(node['children']['node'], level)

    return json_data


def data_to_redis():

    r = redis.StrictRedis(host=config.HOLDINGS_REDIS_HOST, port=config.HOLDINGS_REDIS_PORT, db=config.HOLDINGS_REDIS_DB)

    print(r.dbsize())
    r.flushdb()
    print(r.dbsize())

    with open('%srvk.facet.json' % config.FACET_DATA, 'r') as thedata:

        jsondata = json.load(thedata)

        for key in jsondata.keys():

            r.hset(key, 'label', jsondata[key]['label'])
            r.hset(key, 'level', jsondata[key]['level'])

    print(r.dbsize())
    print(r.hgetall('AA 10970'))


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

        with open('%srvk.facet.json' % config.FACET_DATA, 'w') as thedata:

            thedata.write('{\n')
            cnt_nodes = len(data['node'])
            cnt = 0
            for data_node in data['node']:
                node_data = build_index_data(node=data_node, level=0)
                cnt += 1
                if cnt == cnt_nodes:
                    node_data = node_data[:-2] + '\n'
                thedata.write(node_data)
            thedata.write('}\n')

        #data_to_redis()
