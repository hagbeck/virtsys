import json
from os import listdir
from os.path import isfile, join
import xmltodict


libraries_to_ignore = ['BHA', 'HA', "SHARE", "ZB"]
locations_to_ignore = ['abgegeben', 'Test', "s.", "Fach", "Medien_1", "Medien_2", "Medien_3", "Medienschr"]


# read data of lobid dump from EDS-ETL process
def read_data_from_lobid_dump(source):
    
    lobid_data = {}
    
    with open(source, 'r') as lobid_dump:
        
        lobid_data = xmltodict.parse(lobid_dump.read())
        
    return lobid_data

def analyse_rvk_in_lobid_by_year(record, rvk_notations, number_of_records_by_year, records_with_rvk_by_year):
        
    if 'publication' in record:
        if isinstance(record['publication'], list):
            for publication in record['publication']:
                if 'startDate' in publication:
                    if publication['startDate'] in number_of_records_by_year:
                        number_of_records_by_year[publication['startDate']] += 1
                    else:
                        number_of_records_by_year[publication['startDate']] = 1
        else:
            if 'startDate' in record['publication']:
                if record['publication']['startDate'] in number_of_records_by_year:
                    number_of_records_by_year[record['publication']['startDate']] += 1
                else:
                    number_of_records_by_year[record['publication']['startDate']] = 1
                    
    if len(rvk_notations) > 0 and 'publication' in record:
        if isinstance(record['publication'], list):
            for publication in record['publication']:
                if 'startDate' in publication:
                    if publication['startDate'] in records_with_rvk_by_year:
                        records_with_rvk_by_year[publication['startDate']] += 1
                    else:
                        records_with_rvk_by_year[publication['startDate']] = 1
        else:
            if 'startDate' in record['publication']:
                if record['publication']['startDate'] in records_with_rvk_by_year:
                    records_with_rvk_by_year[record['publication']['startDate']] += 1
                else:
                    records_with_rvk_by_year[record['publication']['startDate']] = 1


def analyse_rvk_in_lobid_by_pubtype(record, rvk_notations, number_of_records_by_pubtype, records_with_rvk_by_pubtype):

    for pubtype in record['type']:                
        if pubtype != 'BibliographicResource':
            if pubtype in number_of_records_by_pubtype:
                number_of_records_by_pubtype[pubtype] += 1
            else:
                number_of_records_by_pubtype[pubtype] = 1       
                
    if len(rvk_notations) > 0:
        
        for pubtype in record['type']:                
            if pubtype != 'BibliographicResource':
                if pubtype in records_with_rvk_by_pubtype:
                    records_with_rvk_by_pubtype[pubtype] += 1
                else:
                    records_with_rvk_by_pubtype[pubtype] = 1 
                         

def analyse_rvk_in_lobid_by_medium(record, rvk_notations, number_of_records_by_medium, records_with_rvk_by_medium):
    
    if 'medium' in record:
        if isinstance(record['medium'], list):
            for medium in record['medium']:
                if 'label' in medium:
                    if medium['label'] in number_of_records_by_medium:
                        number_of_records_by_medium[medium['label']] += 1
                    else:
                        number_of_records_by_medium[medium['label']] = 1
        else:
            if 'label' in record['medium']:
                if record['medium']['label'] in number_of_records_by_medium:
                    number_of_records_by_medium[record['medium']['label']] += 1
                else:
                    number_of_records_by_medium[record['medium']['label']] = 1
        
    if len(rvk_notations) > 0 and 'medium' in record:
        if isinstance(record['medium'], list):
            for medium in record['medium']:
                if 'label' in medium:
                    if medium['label'] in records_with_rvk_by_medium:
                        records_with_rvk_by_medium[medium['label']] += 1
                    else:
                        records_with_rvk_by_medium[medium['label']] = 1
        else:
            if 'label' in record['medium']:
                if record['medium']['label'] in records_with_rvk_by_medium:
                    records_with_rvk_by_medium[record['medium']['label']] += 1
                else:
                    records_with_rvk_by_medium[record['medium']['label']] = 1


def read_data_from_tsv(source):
        
    data = []
    
    with open(source, 'r') as f:
        for line in f:
            data.append(line.strip().split('\t'))
            
    shelfmark_map = {}
    
    for line in data:
        if len(line) > 1:
            shelfmark_map[line[3]] = line[4]
            
    return shelfmark_map

                    
def analyse_rvk_in_lobid_by_shelfmark(record, rvk_notations, number_of_records_by_shelfmark, records_with_rvk_by_shelfmark, shelfmark_map):
            
    if 'hasItem' in record:
                
        number_of_records_by_shelfmark_old = 0
        
        if isinstance(record['hasItem'], list):
            for item in record['hasItem']:
                if 'type' in item and 'Item' in item['type'] and item['heldBy']['isil'] == 'DE-290' and 'callNumber' in item:
                    
                    if item['currentLibrary'] in libraries_to_ignore or item['currentLocation'] in locations_to_ignore:
                        continue
                    
                    call_number = item['callNumber']
                    if call_number in shelfmark_map.keys():
                        call_number = shelfmark_map[call_number]
                        number_of_records_by_shelfmark_old += 1
                    
                    if item['currentLibrary'] not in number_of_records_by_shelfmark:
                        number_of_records_by_shelfmark[item['currentLibrary']] = {}
                    if item['currentLibrary'] == 'SFS':
                        shelfmark = call_number.split('/')[0]
                        if shelfmark in number_of_records_by_shelfmark[item['currentLibrary']]:
                            number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                    elif item['currentLibrary'] == 'SM':
                        if item['currentLocation'] == 'FOME-ZS':
                            shelfmark = ' '.join(call_number.split(' ')[0:2])
                            if shelfmark in number_of_records_by_shelfmark[item['currentLibrary']]:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                        elif item['currentLocation'] == 'FOME':
                            if 'FOME' not in number_of_records_by_shelfmark:
                                number_of_records_by_shelfmark['FOME'] = {}
                            shelfmark = call_number.split('/')[0].split('-')[0]
                            if shelfmark in number_of_records_by_shelfmark['FOME']:
                                number_of_records_by_shelfmark['FOME'][shelfmark] += 1
                            else:
                                number_of_records_by_shelfmark['FOME'][shelfmark] = 1
                        else:
                            shelfmark = call_number.split(' ')[0].split('-')[0]
                            if shelfmark in number_of_records_by_shelfmark[item['currentLibrary']]:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                    else:
                        if item['currentLibrary'] not in number_of_records_by_shelfmark:
                            number_of_records_by_shelfmark[item['currentLibrary']] = {}
                        if item['currentLocation'] == 'LB':
                            shelfmark = ' '.join(call_number.split(' ')[0:2])
                            if shelfmark in number_of_records_by_shelfmark[item['currentLibrary']]:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                        else:
                            shelfmark = call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0]
                            if shelfmark in number_of_records_by_shelfmark[item['currentLibrary']]:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                number_of_records_by_shelfmark[item['currentLibrary']][shelfmark] = 1
        else:
            if 'type' in record['hasItem'] and 'Item' in record['hasItem']['type'] and record['hasItem']['heldBy']['isil'] == 'DE-290' and 'callNumber' in record['hasItem']:
                
                if record['hasItem']['currentLibrary'] in libraries_to_ignore or record['hasItem']['currentLocation'] in locations_to_ignore:
                    return number_of_records_by_shelfmark_old
                
                call_number = record['hasItem']['callNumber']
                if call_number in shelfmark_map.keys():
                    call_number = shelfmark_map[call_number]
                    number_of_records_by_shelfmark_old += 1
                
                if record['hasItem']['currentLibrary'] not in number_of_records_by_shelfmark:
                    number_of_records_by_shelfmark[record['hasItem']['currentLibrary']] = {}
                if record['hasItem']['currentLibrary'] == 'SFS':
                    shelfmark = call_number.split('/')[0]
                    if shelfmark in number_of_records_by_shelfmark[record['hasItem']['currentLibrary']]:
                        number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                    else:
                        number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                elif record['hasItem']['currentLibrary'] == 'SM':
                    if record['hasItem']['currentLocation'] == 'FOME-ZS':
                        shelfmark = ' '.join(call_number.split(' ')[0:2])
                        if shelfmark in number_of_records_by_shelfmark[record['hasItem']['currentLibrary']]:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                    elif record['hasItem']['currentLocation'] == 'FOME':
                        if 'FOME' not in number_of_records_by_shelfmark:
                            number_of_records_by_shelfmark['FOME'] = {}
                        shelfmark = call_number.split('/')[0].split('-')[0]
                        if shelfmark in number_of_records_by_shelfmark['FOME']:
                            number_of_records_by_shelfmark['FOME'][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark['FOME'][shelfmark] = 1
                    else:
                        shelfmark = call_number.split(' ')[0].split('-')[0]
                        if shelfmark in number_of_records_by_shelfmark[record['hasItem']['currentLibrary']]:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                else:
                    if record['hasItem']['currentLocation'] == 'LB':
                        shelfmark = ' '.join(call_number.split(' ')[0:2])
                        if shelfmark in number_of_records_by_shelfmark[record['hasItem']['currentLibrary']]:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                    else:
                        shelfmark = call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0]
                        if shelfmark in number_of_records_by_shelfmark[record['hasItem']['currentLibrary']]:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            number_of_records_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1                       

    if len(rvk_notations) > 0 and 'hasItem' in record:
        if isinstance(record['hasItem'], list):
            for item in record['hasItem']:
                if 'type' in item and 'Item' in item['type'] and item['heldBy']['isil'] == 'DE-290' and 'callNumber' in item:
                    
                    call_number = item['callNumber']
                    if call_number in shelfmark_map.keys():
                        call_number = shelfmark_map[call_number]
                    
                    if item['currentLibrary'] not in records_with_rvk_by_shelfmark:
                        records_with_rvk_by_shelfmark[item['currentLibrary']] = {}
                    if item['currentLibrary'] == 'SFS':
                        shelfmark = call_number.split('/')[0]
                        if shelfmark in records_with_rvk_by_shelfmark[item['currentLibrary']]:
                            records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                    elif item['currentLibrary'] == 'SM':
                        if item['currentLocation'] == 'FOME-ZS':
                            shelfmark = ' '.join(call_number.split(' ')[0:2])
                            if shelfmark in records_with_rvk_by_shelfmark[item['currentLibrary']]:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                        elif item['currentLocation'] == 'FOME':
                            if 'FOME' not in records_with_rvk_by_shelfmark:
                                records_with_rvk_by_shelfmark['FOME'] = {}
                            shelfmark = call_number.split('/')[0].split('-')[0]
                            if shelfmark in records_with_rvk_by_shelfmark['FOME']:
                                records_with_rvk_by_shelfmark['FOME'][shelfmark] += 1
                            else:
                                records_with_rvk_by_shelfmark['FOME'][shelfmark] = 1
                        else:
                            shelfmark = call_number.split(' ')[0].split('-')[0]
                            if shelfmark in records_with_rvk_by_shelfmark[item['currentLibrary']]:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                    else:
                        if item['currentLibrary'] not in records_with_rvk_by_shelfmark:
                            records_with_rvk_by_shelfmark[item['currentLibrary']] = {}
                        if item['currentLocation'] == 'LB':
                            shelfmark = ' '.join(call_number.split(' ')[0:2])
                            if shelfmark in records_with_rvk_by_shelfmark[item['currentLibrary']]:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] = 1
                        else:
                            shelfmark = call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0]
                            if shelfmark in records_with_rvk_by_shelfmark[item['currentLibrary']]:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] += 1
                            else:
                                records_with_rvk_by_shelfmark[item['currentLibrary']][shelfmark] = 1
        else:
            if 'type' in record['hasItem'] and 'Item' in record['hasItem']['type'] and record['hasItem']['heldBy']['isil'] == 'DE-290' and 'callNumber' in record['hasItem']:
                
                call_number = record['hasItem']['callNumber']
                if call_number in shelfmark_map.keys():
                    call_number = shelfmark_map[call_number]
                    
                if record['hasItem']['currentLibrary'] not in records_with_rvk_by_shelfmark:
                    records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']] = {}
                if record['hasItem']['currentLibrary'] == 'SFS':
                    shelfmark = call_number.split('/')[0]
                    if shelfmark in records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']]:
                        records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                    else:
                        records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                elif record['hasItem']['currentLibrary'] == 'SM':
                    if record['hasItem']['currentLocation'] == 'FOME-ZS':
                        shelfmark = ' '.join(call_number.split(' ')[0:2])
                        if shelfmark in records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']]:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                    elif record['hasItem']['currentLocation'] == 'FOME':
                        if 'FOME' not in records_with_rvk_by_shelfmark:
                            records_with_rvk_by_shelfmark['FOME'] = {}
                        shelfmark = call_number.split('/')[0].split('-')[0]
                        if shelfmark in records_with_rvk_by_shelfmark['FOME']:
                            records_with_rvk_by_shelfmark['FOME'][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark['FOME'][shelfmark] = 1
                    else:
                        shelfmark = call_number.split(' ')[0].split('-')[0]
                        if shelfmark in records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']]:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                else:
                    if record['hasItem']['currentLocation'] == 'LB':
                        shelfmark = ' '.join(call_number.split(' ')[0:2])
                        if shelfmark in records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']]:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1
                    else:
                        shelfmark = call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0]
                        if shelfmark in records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']]:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] += 1
                        else:
                            records_with_rvk_by_shelfmark[record['hasItem']['currentLibrary']][shelfmark] = 1   

    return number_of_records_by_shelfmark_old


def analyse_rvk_in_lobid(lobid_data, shelfmark_map):
    
    number_of_records = 0
    number_of_records_by_year = {}
    number_of_records_by_pubtype = {}
    number_of_records_by_medium = {}
    number_of_records_by_shelfmark = {}
    
    records_with_rvk = 0
    rvk_notations_for_records = 0
    
    number_of_records_by_shelfmark_old = 0
    
    records_with_rvk_by_year = {}
    records_with_rvk_by_pubtype = {}
    records_with_rvk_by_medium = {}
    records_with_rvk_by_shelfmark = {}
    
    for record in lobid_data['lobid_records']['lobid_record']:
        
        number_of_records += 1
        
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
                  
        analyse_rvk_in_lobid_by_year(record, rvk_notations, number_of_records_by_year, records_with_rvk_by_year)
        analyse_rvk_in_lobid_by_pubtype(record, rvk_notations, number_of_records_by_pubtype, records_with_rvk_by_pubtype)
        analyse_rvk_in_lobid_by_medium(record, rvk_notations, number_of_records_by_medium, records_with_rvk_by_medium)
        number_of_records_by_shelfmark_old = analyse_rvk_in_lobid_by_shelfmark(record, rvk_notations, number_of_records_by_shelfmark, records_with_rvk_by_shelfmark, shelfmark_map)
                            
        if len(rvk_notations) > 0:
                                        
            records_with_rvk += 1
            rvk_notations_for_records += len(rvk_notations)
                
    return number_of_records, records_with_rvk, rvk_notations_for_records, number_of_records_by_year, records_with_rvk_by_year, number_of_records_by_pubtype, records_with_rvk_by_pubtype, number_of_records_by_medium, records_with_rvk_by_medium, number_of_records_by_shelfmark, records_with_rvk_by_shelfmark, number_of_records_by_shelfmark_old
    

def build_data_to_analyse_from_lobid(lobid_data, shelfmark_map):
    
    records_to_analyse = []
    
    for record in lobid_data['lobid_records']['lobid_record']:
                
        record_to_analyse = {
            'mms_id': record['almaMmsId']
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
        record_to_analyse['rvk_notations'] = list(set(rvk_notations))
        
        years = []
        if 'publication' in record:
            if isinstance(record['publication'], list):
                for publication in record['publication']:
                    if 'startDate' in publication:
                        years.append(publication['startDate'])
            else:
                if 'startDate' in record['publication']:
                    years.append(record['publication']['startDate'])
        record_to_analyse['year'] = list(set(years))

        pubtypes = []
        for pubtype in record['type']:                
            if pubtype != 'BibliographicResource':
                pubtypes.append(pubtype)
        record_to_analyse['pubtype'] = list(set(pubtypes))
                            
        mediums = []
        if 'medium' in record:
            if isinstance(record['medium'], list):
                for medium in record['medium']:
                    if 'label' in medium:
                        mediums.append(medium['label'])
            else:
                if 'label' in record['medium']:
                    mediums.append(record['medium']['label'])
        record_to_analyse['medium'] = list(set(mediums))
                    
        collections = []
        if 'inCollection' in record:
            ignorable_collections = ['https://nrw.digibib.net/search/hbzvk/', 'http://lobid.org/organisations/DE-655#!']
            if isinstance(record['inCollection'], list):
                for in_collection in record['inCollection']:
                    if 'type' in in_collection and 'Collection' in in_collection['type'] and in_collection['id'] not in ignorable_collections:
                        collection = in_collection['id'].split('/')[-1].replace('#!', '')
                        collections.append(collection)
            else:
                if 'type' in record['inCollection'] and 'Collection' in record['inCollection']['type'] and record['inCollection']['id'] not in ignorable_collections:
                    collection = record['inCollection']['id'].split('/')[-1].replace('#!', '')
                    collections.append(collection)
        record_to_analyse['collections'] = list(set(collections))
        
        libraries = []
        if 'hasItem' in record:
            if isinstance(record['hasItem'], list):
                for item in record['hasItem']:
                    if 'type' in item and 'Item' in item['type'] and item['heldBy']['isil'] == 'DE-290':
                        if 'currentLibrary' in item:
                            libraries.append(item['currentLibrary'])
            else:
                if 'type' in record['hasItem'] and 'Item' in record['hasItem']['type'] and record['hasItem']['heldBy']['isil'] == 'DE-290':
                    if 'currentLibrary' in record['hasItem']:
                        libraries.append(record['hasItem']['currentLibrary'])
                        
        locations = []
        if 'hasItem' in record:
            if isinstance(record['hasItem'], list):
                for item in record['hasItem']:
                    if 'type' in item and 'Item' in item['type'] and item['heldBy']['isil'] == 'DE-290':
                        if 'currentLocation' in item:
                            locations.append(item['currentLocation'])
            else:
                if 'type' in record['hasItem'] and 'Item' in record['hasItem']['type'] and record['hasItem']['heldBy']['isil'] == 'DE-290':
                    if 'currentLocation' in record['hasItem']:
                        locations.append(record['hasItem']['currentLocation'])
        
        shelfmarks = []
        if 'hasItem' in record:
            if isinstance(record['hasItem'], list):
                for item in record['hasItem']:
                    if 'type' in item and 'Item' in item['type'] and item['heldBy']['isil'] == 'DE-290' and 'callNumber' in item:
                        call_number = item['callNumber']
                        if call_number in shelfmark_map.keys():
                            call_number = shelfmark_map[call_number]

                        if item['currentLibrary'] == 'SFS':
                            shelfmarks.append(call_number.split('/')[0])
                        elif item['currentLibrary'] == 'SM':
                            if item['currentLocation'] == 'FOME-ZS':
                                shelfmarks.append(' '.join(call_number.split(' ')[0:2]))
                            elif item['currentLocation'] == 'FOME':
                                libraries.append('FOME')
                                shelfmarks.append(call_number.split('/')[0].split('-')[0])
                            else:
                                shelfmarks.append(call_number.split(' ')[0].split('-')[0])
                        else:
                            if item['currentLocation'] == 'LB':
                                shelfmarks.append(' '.join(call_number.split(' ')[0:2]))
                            else:
                                shelfmarks.append(call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0])
            else:
                if 'type' in record['hasItem'] and 'Item' in record['hasItem']['type'] and record['hasItem']['heldBy']['isil'] == 'DE-290' and 'callNumber' in record['hasItem']:
                    call_number = record['hasItem']['callNumber']
                    if call_number in shelfmark_map.keys():
                        call_number = shelfmark_map[call_number]
                    
                    if record['hasItem']['currentLibrary'] == 'SFS':
                        shelfmarks.append(call_number.split('/')[0])
                    elif record['hasItem']['currentLibrary'] == 'SM':
                        if record['hasItem']['currentLocation'] == 'FOME-ZS':
                            shelfmarks.append(' '.join(call_number.split(' ')[0:2]))
                        elif record['hasItem']['currentLocation'] == 'FOME':
                            libraries.append('FOME')
                            shelfmarks.append(call_number.split('/')[0].split('-')[0])
                        else:
                            shelfmarks.append(call_number.split(' ')[0].split('-')[0])
                    else:
                        if record['hasItem']['currentLocation'] == 'LB':
                            shelfmarks.append(' '.join(call_number.split(' ')[0:2]))
                        else:
                            shelfmarks.append(call_number.split(' ')[0].split('-')[0].split('/')[0].split('<')[0])

        record_to_analyse['shelfmarks'] = list(set(shelfmarks))
                    
        record_to_analyse['libraries'] = list(set(libraries))
        
        # ignore records if libraries contains one of the libraries to ignore
        if any(library in libraries for library in libraries_to_ignore):
            continue
        
        # ignore records if locations contains one of the locations to ignore
        if any(location in locations for location in locations_to_ignore):
            continue

        records_to_analyse.append(record_to_analyse)
        
    return records_to_analyse   


def process_data_new(data_dir):
    
    sources = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]
    print(sources)
    
    # Durch die Umsignierung ist die Auswertung der Shelfmarks nicht mehr so aussagekräftig. Um hier doch noch Aussagen treffen zukönnen, müssen die alten Signaturen geholt werden. 
    # Dazu wird es in Analytics eine Liste unter /Geteilte Ordner/Technische Universitaet Dortmund 49HBZ_UBD/Reports/Printmendien/Umsignierung geben.
    # path=%2Fshared%2FTechnische Universitaet Dortmund 49HBZ_UBD%2FReports%2FPrintmedien%2FUmsignierung%2FAbbildung alte auf neue Signaturen
    # -> /home/mhagbeck/DataProjects/alma/api_sandbox/data.tsv
    shelfmark_map = read_data_from_tsv('/home/mhagbeck/DataProjects/alma/api_sandbox/2024-10-09_data.tsv')
    print('Number of old shelfmarks in map: %d' % len(shelfmark_map))

    for source in sources:
        lobid_data = read_data_from_lobid_dump(data_dir + '/' + source)
        records_to_analyse = build_data_to_analyse_from_lobid(lobid_data, shelfmark_map)
        # write as json file
        with open('data/4report/' + source + '.json', 'w') as f:
            json.dump(records_to_analyse, f, indent=2)


def process_data(data_dir):
    
    sources = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]
    print(sources)
    
    # Durch die Umsignierung ist die Auswertung der Shelfmarks nicht mehr so aussagekräftig. Um hier doch noch Aussagen treffen zukönnen, müssen die alten Signaturen geholt werden. 
    # Dazu wird es in Analytics eine Liste unter /Geteilte Ordner/Technische Universitaet Dortmund 49HBZ_UBD/Reports/Printmendien/Umsignierung geben.
    # path=%2Fshared%2FTechnische Universitaet Dortmund 49HBZ_UBD%2FReports%2FPrintmedien%2FUmsignierung%2FAbbildung alte auf neue Signaturen
    # -> /home/mhagbeck/DataProjects/alma/api_sandbox/data.tsv
    shelfmark_map = read_data_from_tsv('/home/mhagbeck/DataProjects/alma/api_sandbox/2024-10-09_data.tsv')
    print('Number of old shelfmarks in map: %d' % len(shelfmark_map))
    
    total_number_of_records = 0
    total_records_with_rvk = 0
    total_rvk_notations_for_records = 0
    total_number_of_records_by_shelfmark_old = 0

    total_number_of_records_by_year = {}
    total_records_with_rvk_by_year = {}
    
    total_records_with_rvk_by_pubtype = {}
    total_number_of_records_by_pubtype = {}

    total_number_of_records_by_medium = {}
    total_records_with_rvk_by_medium = {}
    
    total_number_of_records_by_shelfmark = {}
    total_records_with_rvk_by_shelfmark = {}
        
    for source in sources:
        lobid_data = read_data_from_lobid_dump(data_dir + '/' + source)
        number_of_records, records_with_rvk, rvk_notations_for_records, number_of_records_by_year, records_with_rvk_by_year, number_of_records_by_pubtype, records_with_rvk_by_pubtype, number_of_records_by_medium, records_with_rvk_by_medium, number_of_records_by_shelfmark, records_with_rvk_by_shelfmark, number_of_records_by_shelfmark_old = analyse_rvk_in_lobid(lobid_data, shelfmark_map)
        
        total_number_of_records += number_of_records
        total_records_with_rvk += records_with_rvk
        total_rvk_notations_for_records += rvk_notations_for_records
        total_number_of_records_by_shelfmark_old += number_of_records_by_shelfmark_old
        
        for year in number_of_records_by_year:
            if year in total_number_of_records_by_year:
                total_number_of_records_by_year[year] += number_of_records_by_year[year]
            else:
                total_number_of_records_by_year[year] = number_of_records_by_year[year]
                
        for year in records_with_rvk_by_year:
            if year in total_records_with_rvk_by_year:
                total_records_with_rvk_by_year[year] += records_with_rvk_by_year[year]
            else:
                total_records_with_rvk_by_year[year] = records_with_rvk_by_year[year]
                
        for pubtype in number_of_records_by_pubtype:
            if pubtype in total_number_of_records_by_pubtype:
                total_number_of_records_by_pubtype[pubtype] += number_of_records_by_pubtype[pubtype]
            else:
                total_number_of_records_by_pubtype[pubtype] = number_of_records_by_pubtype[pubtype]
                
        for pubtype in records_with_rvk_by_pubtype:
            if pubtype in total_records_with_rvk_by_pubtype:
                total_records_with_rvk_by_pubtype[pubtype] += records_with_rvk_by_pubtype[pubtype]
            else:
                total_records_with_rvk_by_pubtype[pubtype] = records_with_rvk_by_pubtype[pubtype]
                
        for medium in number_of_records_by_medium:
            if medium in total_number_of_records_by_medium:
                total_number_of_records_by_medium[medium] += number_of_records_by_medium[medium]
            else:
                total_number_of_records_by_medium[medium] = number_of_records_by_medium[medium]
                
        for medium in records_with_rvk_by_medium:
            if medium in total_records_with_rvk_by_medium:
                total_records_with_rvk_by_medium[medium] += records_with_rvk_by_medium[medium]
            else:
                total_records_with_rvk_by_medium[medium] = records_with_rvk_by_medium[medium]
                
        for library in number_of_records_by_shelfmark:
            for shelfmark in number_of_records_by_shelfmark[library]:
                if library not in total_number_of_records_by_shelfmark:
                    total_number_of_records_by_shelfmark[library] = {}
                if shelfmark in total_number_of_records_by_shelfmark[library]:
                    total_number_of_records_by_shelfmark[library][shelfmark] += number_of_records_by_shelfmark[library][shelfmark]
                else:
                    total_number_of_records_by_shelfmark[library][shelfmark] = number_of_records_by_shelfmark[library][shelfmark]

        for library in records_with_rvk_by_shelfmark:
            for shelfmark in records_with_rvk_by_shelfmark[library]:
                if library not in total_records_with_rvk_by_shelfmark:
                    total_records_with_rvk_by_shelfmark[library] = {}
                if shelfmark in total_records_with_rvk_by_shelfmark[library]:
                    total_records_with_rvk_by_shelfmark[library][shelfmark] += records_with_rvk_by_shelfmark[library][shelfmark]
                else:
                    total_records_with_rvk_by_shelfmark[library][shelfmark] = records_with_rvk_by_shelfmark[library][shelfmark]                
    
    print('Number of records: %d' % total_number_of_records)
    print('Records with RVK: %d' % total_records_with_rvk)
    print('RVK notations for records: %d' % total_rvk_notations_for_records)
    print('Number of records by old shelfmark: %d' % total_number_of_records_by_shelfmark_old)
        
    write_data_to_file(total_number_of_records, total_records_with_rvk, total_rvk_notations_for_records, total_number_of_records_by_year, total_records_with_rvk_by_year, total_number_of_records_by_pubtype, total_records_with_rvk_by_pubtype, total_number_of_records_by_medium, total_records_with_rvk_by_medium, total_number_of_records_by_shelfmark, total_records_with_rvk_by_shelfmark)

    
def write_data_to_file(total_number_of_records, total_records_with_rvk, total_rvk_notations_for_records, total_number_of_records_by_year, total_records_with_rvk_by_year, total_number_of_records_by_pubtype, total_records_with_rvk_by_pubtype, total_number_of_records_by_medium, total_records_with_rvk_by_medium, total_number_of_records_by_shelfmark, total_records_with_rvk_by_shelfmark):
    
    with open('data/rvk_in_lobid.tsv', 'w') as f:
        f.write('Number of records\t%d\n' % total_number_of_records)
        f.write('Records with RVK\t%d\n' % total_records_with_rvk)
        f.write('RVK notations for records\t%d\n' % total_rvk_notations_for_records)
                
    # get rvk notations for pubtype in percent
    with open('data/rvk_in_lobid_by_pubtype.tsv', 'w') as f:
        f.write('Publication Type\tNumber of Records\tNumber of Records with RVK\tPercent\n')
        for pubtype in total_number_of_records_by_pubtype:
            if pubtype in total_records_with_rvk_by_pubtype:
                f.write('%s\t%s\t%s\t%f\n' % (pubtype, total_number_of_records_by_pubtype[pubtype], total_records_with_rvk_by_pubtype[pubtype], (total_records_with_rvk_by_pubtype[pubtype] / total_number_of_records_by_pubtype[pubtype]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (pubtype, total_number_of_records_by_pubtype[pubtype]))
            
    # get rvk notations for year in percent sorted by year descending
    with open('data/rvk_in_lobid_by_year.tsv', 'w') as f:
        f.write('Publication Year\tNumber of Records\tNumber of Records with RVK\tPercent\n')
        for year in sorted(total_number_of_records_by_year, reverse=True):
            if year in total_records_with_rvk_by_year:
                f.write('%s\t%s\t%s\t%f\n' % (year, total_number_of_records_by_year[year], total_records_with_rvk_by_year[year], (total_records_with_rvk_by_year[year] / total_number_of_records_by_year[year]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (year, total_number_of_records_by_year[year]))
                
    # get rvk notations for medium in percent
    with open('data/rvk_in_lobid_by_medium.tsv', 'w') as f:
        f.write('Medium\tNumber of Records\tNumber of Records with RVK\tPercent\n')
        for medium in total_number_of_records_by_medium:
            if medium in total_records_with_rvk_by_medium:
                f.write('%s\t%s\t%s\t%f\n' % (medium, total_number_of_records_by_medium[medium], total_records_with_rvk_by_medium[medium], (total_records_with_rvk_by_medium[medium] / total_number_of_records_by_medium[medium]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (medium, total_number_of_records_by_medium[medium]))
                
    # get rvk notations for shelfmark in percent
    for library in total_number_of_records_by_shelfmark:
        with open('data/rvk_in_lobid_by_shelfmark_for_%s.tsv' % library.lower(), 'w') as f:
            f.write('Shelfmark\tNumber of Records\tNumber of Records with RVK\tPercent\n')
            for shelfmark in total_number_of_records_by_shelfmark[library]:
                if library not in total_records_with_rvk_by_shelfmark:
                    f.write('%s\t%s\t0\t0\n' % (shelfmark, total_number_of_records_by_shelfmark[library][shelfmark]))
                else:
                    if shelfmark in total_records_with_rvk_by_shelfmark[library]:
                        f.write('%s\t%s\t%s\t%f\n' % (shelfmark, total_number_of_records_by_shelfmark[library][shelfmark], total_records_with_rvk_by_shelfmark[library][shelfmark], (total_records_with_rvk_by_shelfmark[library][shelfmark] / total_number_of_records_by_shelfmark[library][shelfmark]) * 100))
                    else:
                        f.write('%s\t%s\t0\t0\n' % (shelfmark, total_number_of_records_by_shelfmark[library][shelfmark]))


if __name__ == '__main__':
        
    process_data_new(data_dir='data/lobid')
