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
import timeit

import simplejson as json
import subprocess
from os import listdir
from os.path import isfile, join

from util_sparql_client import sparql_query

#CG_DATA_DIR = 'data/cg/json_data'
#CG_RVK_INDEX_DIR = 'data/rvk/solr'
CG_DATA_DIR = '/export/storage/graphdb/import/cg/json_data'
CG_RVK_INDEX_DIR = '/export/virtuelle_systematik/data/solr/cg_index'


def read_sparql_query(sparql_file=''):

    sparql_query = ''
    with open(sparql_file, 'r') as sparql_file:
        for line in sparql_file:

            sparql_query += line

    return sparql_query


def get_rvk_branches(notation):

    if not notation:
        return None

    # TODO use SPARQL query to get the branch notations
    GET_ALL_BRANCH_NOTATIONS = '''
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?notation WHERE { 
  <http://data.ub.tu-dortmund.de/resource/rvk/%s> skos:broader ?subject .
  ?subject skos:notation ?notation .
}
    '''
    try:
        branches_data = sparql_query(query=GET_ALL_BRANCH_NOTATIONS % notation.replace(' ', ''))
        branches = []
        for entry in branches_data:
            branches.append(entry['notation']['value'])

        # return branches
        return branches

    except Exception as e:
        print('ERROR SPARQL for notation %s - %s' % (notation, e))
        return []


def get_cg_data(file=''):

    rvk_notation_counter = 0

    with open('%s/%s' % (CG_RVK_INDEX_DIR, file), 'w') as idxdata:
        with open('%s/%s' % (CG_DATA_DIR, file), 'r') as cg_data:
            for line in cg_data:
                record = json.loads(line)
                # print(record)

                index_record = {
                    "id": record['id'].split('T')[0],
                    "members": [],
                    "rvk_notation": [],
                    "rvk_branch_notations": [],
                    "cg_member_collection": []
                }

                for item in record['members']:
                    if ')' in item:
                        index_record['members'].append(item.split(')')[1])
                        member_id = item.split(')')[0].replace('(', '')
                        if member_id not in index_record['cg_member_collection']:
                            index_record['cg_member_collection'].append(member_id)

                    else:
                        index_record['members'].append(item)

                for item in record['classifications']:
                    if item == 'rvk':
                        for notation in record['classifications'][item]:
                            index_record['rvk_notation'].append(notation['notation'])

                            branches = get_rvk_branches(notation=notation['notation'])
                            if branches:
                                for branch in branches:
                                    if branch not in index_record['rvk_branch_notations'] and branch != notation['notation']:
                                        index_record['rvk_branch_notations'].append(branch)

                idxdata.write(json.dumps(index_record))
                idxdata.write('\n')
                rvk_notation_counter += len(index_record['rvk_notation'])

    return rvk_notation_counter


def build_index_record():

    cg_files = [f for f in listdir(CG_DATA_DIR) if isfile(join(CG_DATA_DIR, f))]
    #print(cg_files)

    total_rvk_notation_counter = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:

        for rvk_notation_counter in executor.map(get_cg_data, cg_files):

            total_rvk_notation_counter += rvk_notation_counter
            print(rvk_notation_counter)

    print('ubdo_rvk_index.json ready.')
    print('%s notations.' % total_rvk_notation_counter)


def start_solrbulk(data_dir=''):
    """ start indexing using solrbulk """

    SOLR_URL = 'http://localhost:8888/solr/cg_index'

    # index data using solrbulk
    solr_index_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

    idx = 1
    for file in solr_index_files:
        # start solrbulk: https://github.com/miku/solrbulk
        # solrbulk -verbose -server https://localhost:7007/solr/biblio solr_add_data.json
        if idx == 1:
            result = subprocess.run(["/usr/sbin/solrbulk", "-purge", "-server", "%s" % SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)
        else:
            result = subprocess.run(["/usr/sbin/solrbulk", "-server", "%s" % SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)

        print(result)

        idx += 1


if __name__ == '__main__':

    # build data
    start = timeit.default_timer()

    #build_index_record()

    stop = timeit.default_timer()
    duration = stop - start
    print('duration building RVK index data: %s' % duration) # TODO duration 28619s ca. 8h

    # index data
    start = timeit.default_timer()

    start_solrbulk(data_dir=CG_RVK_INDEX_DIR)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration indexing the data in solr: %s' % duration) # TODO duration 18 min
