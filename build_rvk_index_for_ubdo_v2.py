import concurrent.futures
import json
from os import listdir
from os.path import isfile, join
import re
import subprocess
import time
import timeit
import uuid
import xmltodict

from util_cleanup import cleanup_dir
from util_mailer import mailer
from util_sparql_client import sparql_query

import config_ubdo as config

# read data of lobid dump from EDS-ETL process
def read_data_from_lobid_dump(source):
    
    lobid_data = {}
    
    with open(source, 'r') as lobid_dump:
        
        lobid_data = xmltodict.parse(lobid_dump.read())
        
    return lobid_data


def read_sparql_query(sparql_file=''):

    sparql_query = ''
    with open(sparql_file, 'r') as sparql_file:
        for line in sparql_file:

            sparql_query += line

    return sparql_query


def __normalize_rvk_data(data=''):

    normalized_data = ''

    normalized_data = data.upper().replace('/', '')

    RVK_CLASS = re.compile(r'[A-Z]{2}\s\d{2,6}')
    RVK_CLASS_wo_space = re.compile(r'[A-Z]{2}\d{2,6}')
    RVK_CLASS_Cutter = re.compile(r'[A-Z]{2}\s\d{2,6}\s[A-Z]{1}\d{1,6}')

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


def get_rvk_notations_from_branch(solr_record=None):
    
    # get all rvk notations of the corresponding branch
    if solr_record.get('rvk_notations'):

        if len(solr_record['rvk_notations']) < 50:

            sparql_get_rvk_branch = read_sparql_query(sparql_file='sparql/get_rvk_branch.sparql')

            solr_record['rvk_branch_notations'] = []

            doit = True
            while doit:
                for notation in solr_record['rvk_notations']:
                    try:
                        rvk_branch_notations = sparql_query(query=sparql_get_rvk_branch % notation, endpoint=config.SPARQL_ENDPOINT)
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


def start_solrbulk(data_dir='', mode='update'):
    """ start indexing using solrbulk """

    message = ''

    # index data using solrbulk
    solr_index_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

    idx = 1
    for file in solr_index_files:
        # start solrbulk: https://github.com/miku/solrbulk
        # solrbulk -verbose -server https://localhost:7007/solr/biblio solr_add_data.json
        if mode != 'update' and idx == 1:
            message += subprocess.run(["/usr/sbin/solrbulk", "-purge", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)
        else:
            message += subprocess.run(["/usr/sbin/solrbulk", "-server", "%s" % config.SOLR_URL, "%s/%s" % (data_dir, file)], stdout=subprocess.PIPE)

        message += '\n'
        
        idx += 1
        
    return message


def get_data(source=''):

    lobid_data = read_data_from_lobid_dump(source)
    
    number_of_records = 0
    number_of_records_with_rvk = 0
    number_of_rvk_notations = 0

    with open(config.SOLR_DATA % str(uuid.uuid4()), 'w') as thedata:

        for record in lobid_data['lobid_records']['lobid_record']:
        
            number_of_records += 1

            solr_record = {
                'id': record['almaMmsId']
            }
        
            rvk_notations = []
            if 'subject' in record:
                if isinstance(record['subject'], list):
                    for subject in record['subject']:
                        if 'source' in subject and 'notation' in subject and 'RVK' in subject['source']['label']:
                            rvk_notations.append(subject['notation'])
                else:
                    if 'source' in record['subject'] and 'notation' in record['subject'] and 'RVK' in record['subject']['source']['label']:
                        rvk_notations.append(record['subject']['notation'])
            
            rvk_notations = list(set(rvk_notations))

            if rvk_notations:
                number_of_records_with_rvk += 1
                solr_record['rvk_notations'] = []

                for item in rvk_notations:
                    normalized_item = __normalize_rvk_data(item)
                    if normalized_item not in solr_record['rvk_notations']:
                        solr_record['rvk_notations'].append(normalized_item)
                        number_of_rvk_notations += 1
                        
            get_rvk_notations_from_branch(solr_record=solr_record)
            
            thedata.write(json.dumps(solr_record))
            thedata.write('\n')
            
    return number_of_records, number_of_records_with_rvk, number_of_rvk_notations


def process_rvk_data():

    # neuer Ansatz, da der vorige zu lange dauert und wir, wegen des künftig monatlichen Updates der CG-Daten in lobid-resources, 
    # Malibu nicht mehr benötigen.
    
    # read file list from daily lobid-resources dump
    # for each file, read the lobid-resources data, extract the RVK notations and get the RVK branches + build solr data 
    
    data_dir='data/lobid'

    sources = [join(data_dir, f) for f in listdir(data_dir) if isfile(join(data_dir, f))]
    print(sources)
        
    total_number_of_records = 0
    total_number_of_records_with_rvk = 0
    total_number_of_rvk_notations = 0
    message = ''
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:

        for number_of_records, number_of_records_with_rvk, number_of_rvk_notations in executor.map(get_data, sources):

            total_number_of_records += number_of_records
            total_number_of_records_with_rvk += number_of_records_with_rvk
            total_number_of_rvk_notations += number_of_rvk_notations

    message += 'ubdo_rvk_index.json ready.\n\n'
    message += '%s/%s records with RVK notations.\n' % (total_number_of_records_with_rvk, total_number_of_records)
    message += '%s notations.\n\n' % total_number_of_rvk_notations
                
    return message


if __name__ == '__main__':

    try:
        # cleanup
        cleanup_dir(data_dir=config.SOLR_DATA_DIR)

        # build data
        start = timeit.default_timer()

        message = process_rvk_data()
        
        stop = timeit.default_timer()
        duration = stop - start
        message += 'duration building RVK index data: %s\n' % duration # duration 9.846s -> ca. 2,7h

        # index data
        start = timeit.default_timer()

        message += start_solrbulk(data_dir=config.SOLR_DATA_DIR, mode='full')

        stop = timeit.default_timer()
        duration = stop - start
        message += 'duration indexing the data in solr: %s' % duration # duration 18 min
        report_status = 'successful'
        
    except Exception as e:
        print(e)
        report_status = 'failed'
        message = e
        
    mailer(
        sender=config.TU_DORTMUND_SMTP['sender'],
        receivers=config.TU_DORTMUND_SMTP['receivers'],
        subject='Building RVK-Index for DE-290 records from lobid-resources: %s' % report_status,
        message='%s' % message)

