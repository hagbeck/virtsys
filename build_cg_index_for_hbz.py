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
import subprocess
import uuid

import simplejson as json
import sys
import timeit
from os import listdir
from os.path import isfile, join

import xmltodict

import config_cg

hbz_data = {}
rvk_label = {}


def get_prov_date(bundle=None):

    if not bundle:
        raise ValueError('No bundle data to work with!')

    cg_id = ''
    cg_prov_data = ''

    for field in bundle['marc:controlfield']:

        if field['@tag'] == '001':
            record_id = field['#text']
            # print('record_id: ' + record_id)
            tmp = record_id.split('_')
            cg_id = tmp[1]
            cg_prov_data = tmp[2]
            break

    return cg_id, cg_prov_data


def get_bundle_members(bundle=None):

    if not bundle:
        raise ValueError('No bundle data to work with!')

    members = []

    # get bundle data: members and provenance data
    for field in bundle['marc:datafield']:

        if type(field) is not str:

            # get bundle member
            if field['@tag'] == '035':
                member = ''
                for subfield in field['marc:subfield']:
                    if subfield['@code'] == 'a':
                        member = subfield['#text']

                members.append(member)

        else:
            # only one datafield; i think its only 035
            # get bundle member
            if bundle['marc:datafield']['@tag'] == '035':
                member = ''
                member_prov_id = ''
                for subfield in bundle['marc:datafield']['marc:subfield']:
                    if subfield['@code'] == 'a':
                        member = subfield['#text']
                    if subfield['@code'] == '8':
                        member_prov_id = subfield['#text']

                members.append(member)
            # print('OTHER TYPE %s: %s' % (type(field), bundle['marc:datafield']))
            # print('OTHER TYPE member: %s' % members)
            break

    return members


def get_rvk_notations(bundle=None):

    if not bundle:
        raise ValueError('No bundle data to work with!')

    classifications = []

    for field in bundle['marc:datafield']:

        if type(field) is not str:
            if field['@tag'] == '084':
                code_a = ''
                code_2 = ''
                code_8 = []
                for subfield in field['marc:subfield']:
                    if subfield['@code'] == 'a' and subfield.get('#text'):
                        code_a = subfield['#text']
                    if subfield['@code'] == '2' and subfield.get('#text'):
                        code_2 = subfield['#text']
                    if subfield['@code'] == '8' and subfield.get('#text'):
                        code_8.append(subfield['#text'].replace('\\', ''))

                if code_2 == 'rvk':

                    if code_a not in classifications:
                        classifications.append(code_a)

    return classifications


def build_index_record(file=''):

    # TODO read file
    data = ''

    with open('%s/%s' % (config_cg.data_dir, file), 'r') as xmldata:
        for line in xmldata:
            data += line.strip()

    try:
        thedata = xmltodict.parse(data)
    except Exception as e:
        return 'ERROR in processing %s: %s' % (file, e), 0

    bundle_counter = 0
    if 'marc:collection' in thedata:

        with open('%s/%s.%s.json' % ('data/solr/hbz', file.replace('.marcxml', ''), str(uuid.uuid4())),
                  'w') as solrdata:

            # for each record (= CG bundle)
            for bundle in thedata['marc:collection']['marc:record']:

                index_record = {}

                cg_id, cg_prov_date = get_prov_date(bundle=bundle)

                members = get_bundle_members(bundle=bundle)

                # next if bundle not contains members of DE-605
                is_bundle_with_hbz = False
                hbz_id = ''
                for member in members:
                    if '(DE-605)' in member:
                        bundle_counter += 1

                        index_record['id'] = member.replace('(DE-605)', '')
                        index_record['cg_bundle_id'] = cg_id
                        index_record['cg_bundle_date'] = cg_prov_date
                        index_record['cg_bundle_member'] = members

                        actors = []
                        for item in members:
                            actor = item.split(')')[0].replace('(', '')
                            if actor not in actors:
                                actors.append(actor)
                        index_record['cg_bundle_actor'] = actors

                        # TODO index_record['hbz_owner'] = get_hbz_owner(hbz_id=hbz_id)
                        rvk_notations = get_rvk_notations(bundle=bundle)

                        if len(rvk_notations) > 50:
                            print("WARN: more than 50 RVK notations! hbz_id=%s, cg_id=%s" % (hbz_id, cg_id), file=sys.stderr)
                        else:
                            index_record['rvk_notations'] = rvk_notations

                        # TODO write record to jsonlines file for solrbulk
                        solrdata.write(json.dumps(index_record))
                        solrdata.write('\n')

    return '%s processed. %s bundles with member DE-605 found.' % (file, bundle_counter), bundle_counter


def start_solrbulk(data_dir='', mode='update'):
    """ start indexing using solrbulk """

    # index data using solrbulk
    solr_index_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

    idx = 1
    for file in solr_index_files:
        # start solrbulk: https://github.com/miku/solrbulk
        # solrbulk -verbose -server https://localhost:7007/solr/biblio solr_add_data.json
        if mode != 'update' and idx == 1:
            result = subprocess.run(["/usr/sbin/solrbulk", "-purge", "-server", "%s" % config_cg.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)
        else:
            result = subprocess.run(["/usr/sbin/solrbulk", "-server", "%s" % config_cg.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)

        print(result)

        idx += 1


def process():

    start = timeit.default_timer()

    # get files from cg source folder
    source_files = [f for f in listdir(config_cg.data_dir) if isfile(join(config_cg.data_dir, f))]

    # for each file start build process
    with concurrent.futures.ProcessPoolExecutor(max_workers=config_cg.number_of_pool_workers) as executor:
        for message in executor.map(build_index_record, source_files):
            print(message)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration metafacture process: %s' % duration) # TODO duration 15.119s -> 4,2h


if __name__ == '__main__':

    process()

    # index data
    start = timeit.default_timer()

    #start_solrbulk(data_dir='data/solr/hbz', mode='full')

    stop = timeit.default_timer()
    duration = stop - start
    print('duration indexing the data in solr: %s' % duration) # TODO duration 10 min
