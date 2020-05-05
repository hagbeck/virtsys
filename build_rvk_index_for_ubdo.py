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
import concurrent.futures
import datetime
import re
import sys
import time
import timeit
import uuid
from urllib import parse

import requests
import simplejson as json
import subprocess
from os import listdir
from os.path import isfile, join

from more_itertools import divide
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from util_cleanup import cleanup_dir
from util_sparql_client import sparql_query

import config_ubdo as config


def read_sparql_query(sparql_file=''):

    sparql_query = ''
    with open(sparql_file, 'r') as sparql_file:
        for line in sparql_file:

            sparql_query += line

    return sparql_query


def __normalize_rvk_data(data=''):

    normalized_data = ''

    normalized_data = data.upper().replace('/', '')

    RVK_CLASS = re.compile('[A-Z]{2}\s\d{2,6}')
    RVK_CLASS_wo_space = re.compile('[A-Z]{2}\d{2,6}')
    RVK_CLASS_Cutter = re.compile('[A-Z]{2}\s\d{2,6}\s[A-Z]{1}\d{1,6}')

    #print(normalized_data)

    if not RVK_CLASS.match(normalized_data) and not RVK_CLASS_Cutter.match(normalized_data):
        #print('\tnot valid')
        if RVK_CLASS_wo_space.match(normalized_data):
            # print('\tnow valid')
            normalized_data = normalized_data[0:2] + ' ' + normalized_data[2:]
        else:
            # print('\tstill not valid')
            normalized_data = ''

    elif RVK_CLASS_Cutter.match(normalized_data):
        print('-> Cutter: %s' % normalized_data)
        normalized_data = ' '.join(normalized_data.split(' ')[0:2])

    return normalized_data


def get_data(record_ids=None):

    if record_ids is None:
        record_ids = []

    cnt_rvk = 0
    hbz_more_than_50_rvk = 0

    if record_ids:

        sparql_get_rvk_branch = read_sparql_query(sparql_file='sparql/get_rvk_branch.sparql')

        with open(config.SOLR_DATA % str(uuid.uuid4()), 'w') as thedata:

            for record_id in record_ids:
                solr_record = {
                    'id': record_id,
                }

                # get rvk notations
                try:
                    query = 'id:%s' % record_id
                    response = requests.get(config.CG_HBZ_INDEX_URL % parse.quote_plus(query)).json()

                    if response and response['response']['numFound'] > 0:

                        if response['response']['docs'][0].get('rvk_notations'):
                            all_rvk_notations = response['response']['docs'][0]['rvk_notations']

                            if all_rvk_notations:
                                solr_record['rvk_notations'] = []

                                for item in all_rvk_notations:
                                    normalized_item = __normalize_rvk_data(item)
                                    if normalized_item not in solr_record['rvk_notations']:
                                        solr_record['rvk_notations'].append(normalized_item)
                                        cnt_rvk += 1
                    else:
                        print("WARN: no record for %s in cg_index! " % record_id, file=sys.stderr)
                        continue

                except Exception as e:
                    print("ERROR: %s! " % e, file=sys.stderr)
                    continue

                # get all rvk notations of the corresponding branch
                if solr_record.get('rvk_notations'):

                    if len(solr_record['rvk_notations']) < 50:

                        solr_record['rvk_branch_notations'] = []

                        doit = True
                        while doit:
                            for notation in solr_record['rvk_notations']:
                                try:
                                    rvk_branch_notations = sparql_query(query=sparql_get_rvk_branch % notation)
                                    doit = False

                                    if rvk_branch_notations:

                                        for item in rvk_branch_notations:
                                            if item.get('notation').get('value') not in solr_record['rvk_branch_notations']:
                                                solr_record['rvk_branch_notations'].append(item.get('notation').get('value'))

                                except Exception as e:
                                    print(e)
                                    print('ERROR connecting to SPARQL endpoint. Waiting ...')
                                    time.sleep(5)

                    else:
                        # cleanup because of potentially cg bundle with errors
                        solr_record['rvk_notations'] = []
                        solr_record['rvk_branch_notations'] = []

                        hbz_more_than_50_rvk += 1
                        print("WARN: more than 50 RVK notations! hbz_id=%s" % record_id, file=sys.stderr)

                thedata.write(json.dumps(solr_record))
                thedata.write('\n')

    return cnt_rvk, hbz_more_than_50_rvk


def build_index_record(mode='update'):

    # TODO read hbz-IDs into list
    record_ids = []
    with open('%s/unload.TIT' % config.SUNRISE_DATA_DIR, 'r') as title_data:

        creation_date = ''
        hbz_id = ''
        for line in title_data:
            if line.startswith('0002:'):
                creation_date = line.strip().replace('0002:', '')
            elif line.startswith('0010.001:'):
                hbz_id = line.strip().replace('0010.001:', '')
            elif line.startswith('9999:'):
                if mode == 'update' and datetime.datetime.strptime(creation_date, '%d.%m.%Y') >= datetime.datetime.strptime((datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y%m%d'), '%Y%m%d'):
                    record_ids.append(hbz_id)
                elif mode == 'full':
                    record_ids.append(hbz_id)
                creation_date = ''
                hbz_id = ''

    number_of_pool_workers = 4
    number_of_partitions = 1000

    print('%s record to enrich.' % len(record_ids))

    # split record_ids into number_of_workers partitions
    partitions = [list(x) for x in divide(number_of_partitions, record_ids)]

    # init thread pool with a queue of partitions and get data for them from graphdb
    total_rvk_notation_counter = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=number_of_pool_workers) as executor:

        for rvk_notation_counter, hbz_more_than_50_rvk in executor.map(get_data, partitions):

            total_rvk_notation_counter += rvk_notation_counter
            print('%s notations; %s records with > 50 notations.' % (rvk_notation_counter, hbz_more_than_50_rvk))

    print('ubdo_rvk_index.json ready.')
    print('%s notations.' % total_rvk_notation_counter)


def start_solrbulk(data_dir='', mode='update'):
    """ start indexing using solrbulk """

    # index data using solrbulk
    solr_index_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

    idx = 1
    for file in solr_index_files:
        # start solrbulk: https://github.com/miku/solrbulk
        # solrbulk -verbose -server https://localhost:7007/solr/biblio solr_add_data.json
        if mode != 'update' and idx == 1:
            result = subprocess.run(["/usr/sbin/solrbulk", "-purge", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)
        else:
            result = subprocess.run(["/usr/sbin/solrbulk", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)

        print(result)

        idx += 1


if __name__ == '__main__':

    mode = 'full'

    # cleanup
    cleanup_dir(data_dir=config.SOLR_DATA_DIR)

    # build data
    start = timeit.default_timer()

    build_index_record(mode=mode)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration building RVK index data: %s' % duration) # TODO duration 9.846s -> ca. 2,7h

    # index data
    start = timeit.default_timer()

    start_solrbulk(data_dir=config.SOLR_DATA_DIR, mode=mode)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration indexing the data in solr: %s' % duration) # TODO duration 18 min
