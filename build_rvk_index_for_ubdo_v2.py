import concurrent.futures
from itertools import islice
import json
from urllib import parse
import uuid
import requests

from util_malibu import get_rvk_data_from_malibu

import config_ubdo as config


def chunks(data, size=10000):
   it = iter(data)
   for i in range(0, len(data), size):
      yield {k:data[k] for k in islice(it, size)}
      

def read_identifier_map(identifier_map_file=''):
    identifier_map = {}
    with open(identifier_map_file, 'r') as identifier_map_file:
        for line in identifier_map_file:
            line = line.strip()
            if line:
                line = line.split('\t')
                if line[0] not in identifier_map and len(line) > 2:
                    identifier_map[line[0]] = line[2]

    return identifier_map


def get_rvk_notations_from_lobid_resources(record_id=None):
    
    if record_id is None:
        return []
    
    lobid_resources_url = 'https://lobid.org/resources/%s.json'
    
    response = requests.get(lobid_resources_url % record_id)
    
    rvk_notations = []
    
    if response.status_code == 200:
        data = response.json()
        
        if 'subject' in data.keys():
            for subject in data['subject']:
                if 'source' in subject.keys() and 'notation' in subject.keys() and 'RVK' in subject['source']['label'] and subject['notation'] not in rvk_notations:
                    rvk_notations.append(subject['notation'])
    
    return rvk_notations


def get_rvk_notations_from_malibu(isbns=None):
    
    if isbns is None:
        return []
    
    rvk_notations = get_rvk_data_from_malibu(isbns=isbns)
    
    return rvk_notations
    
    
def get_rvk_node_data(node=None, nodes=None):

    if nodes is None:
        nodes = []

    nodes.append(node.get('notation'))

    if node.get('ancestor'):
        return get_rvk_node_data(node=node['ancestor']['node'], nodes=nodes)
    else:
        return nodes


def get_rvk_branches(rvk_notations=None):
    
    if rvk_notations is None:
        return []

    branch_notations = []
    
    for notation in rvk_notations:
        rvk_target_url = 'https://dev.ub.tu-dortmund.de/neoserver/v1/taxonomy/ancestors/%s'
        response = requests.get(rvk_target_url % parse.quote(notation))
        if response.status_code == 200:
            json_data = response.json()
            if json_data.get('node') and json_data['node'].get('ancestor') and json_data['node']['ancestor'].get('node'):
                current_branch_notations = get_rvk_node_data(node=json_data['node']['ancestor']['node'], nodes=[])
                branch_notations.extend(current_branch_notations)

    return list(set(branch_notations))    


def build_index_records(identifier_map=None):

    malibu_request_counter = 0
    rvk_notations_from_lobid = 0
    rvk_notations_from_malibu = 0
    
    records_withouth_rvk = 0
            
    with open(config.SOLR_DATA % str(uuid.uuid4()), 'w') as thedata:
        for record_id, isbns in identifier_map.items():
            # get rvk notations from lobid resources
            rvk_notations = []
            if record_id.startswith('lobid:'):
                rvk_notations = get_rvk_notations_from_lobid_resources(record_id=record_id.replace('lobid:', ''))
                rvk_notations_from_lobid += len(rvk_notations)
            # get rvk notations from malibu
            if not rvk_notations and isbns:
                malibu_request_counter += 1
                rvk_notations = get_rvk_notations_from_malibu(isbns=isbns.split('|'))
                rvk_notations_from_malibu += len(rvk_notations)
            if not rvk_notations:
                records_withouth_rvk += 1
            # get rvk branches
            if rvk_notations:
                rvk_branch_notations = get_rvk_branches(rvk_notations=rvk_notations)
            else:
                rvk_branch_notations = []
            # build index records
            solr_record = {
                'id': record_id.replace('lobid:', '').replace('alma:', ''),
                'rvk_notations': rvk_notations,
                'rvk_branch_notations': rvk_branch_notations
            }

        # write index records to file
        thedata.write(json.dumps(solr_record))
        thedata.write('\n')
    
    return malibu_request_counter, rvk_notations_from_lobid, rvk_notations_from_malibu, records_withouth_rvk


def process(identifier_map=None):
    
    partitions = []
    for partition in chunks(identifier_map, 10000):
        partitions.append(partition)
    print('Partitions: %s' % len(partitions))
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:

        for malibu_request_counter, rvk_notations_from_lobid, rvk_notations_from_malibu, records_withouth_rvk in executor.map(build_index_records, partitions):

            print('Malibu request counter: %s' % malibu_request_counter)
            print('RVK notations from Lobid: %s' % rvk_notations_from_lobid)
            print('RVK notations from Malibu: %s' % rvk_notations_from_malibu)
            print('Records without RVK: %s' % records_withouth_rvk)

    
if __name__ == '__main__':

    identifier_map = read_identifier_map(identifier_map_file='data/identifier_map.tsv')
    process(identifier_map=identifier_map)
    