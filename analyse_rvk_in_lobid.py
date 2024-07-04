from os import listdir
from os.path import isfile, join
import xmltodict

# read data of lobid dump from EDS-ETL process
def read_data_from_lobid_dump(source):
    
    lobid_data = {}
    
    with open(source, 'r') as lobid_dump:
        
        lobid_data = xmltodict.parse(lobid_dump.read())
        
    return lobid_data


def analyse_rvk_in_lobid(lobid_data):
    
    number_of_records = 0
    number_of_records_by_year = {}
    number_of_records_by_pubtype = {}
    number_of_records_by_medium = {}
    
    records_with_rvk = 0
    rvk_notations_for_records = 0
    
    records_with_rvk_by_year = {}
    records_with_rvk_by_pubtype = {}
    records_with_rvk_by_medium = {}
    
    for record in lobid_data['lobid_records']['lobid_record']:
        
        number_of_records += 1
        
        rvk_notations = []
                  
        for pubtype in record['type']:                
            if pubtype != 'BibliographicResource':
                if pubtype in number_of_records_by_pubtype:
                    number_of_records_by_pubtype[pubtype] += 1
                else:
                    number_of_records_by_pubtype[pubtype] = 1                
                        
        if 'subject' in record:
            if isinstance(record['subject'], list):
                for subject in record['subject']:
                    if 'source' in subject and 'notation' in subject and 'RVK' in subject['source']['label']:
                        rvk_notations.append(subject['notation'])
            else:
                if 'source' in record['subject'] and 'notation' in record['subject'] and 'RVK' in record['subject']['source']['label']:
                    rvk_notations.append(record['subject']['notation'])
        
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
                            
        rvk_notations = list(set(rvk_notations))
    
        if len(rvk_notations) > 0:
            
            for pubtype in record['type']:                
                if pubtype != 'BibliographicResource':
                    if pubtype in records_with_rvk_by_pubtype:
                        records_with_rvk_by_pubtype[pubtype] += 1
                    else:
                        records_with_rvk_by_pubtype[pubtype] = 1 
                        
            if 'publication' in record:
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

            if 'medium' in record:
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
                            
            records_with_rvk += 1
            rvk_notations_for_records += len(rvk_notations)
                
    # build map with RVK classified records based on local classification

    return number_of_records, records_with_rvk, rvk_notations_for_records, number_of_records_by_year, records_with_rvk_by_year, number_of_records_by_pubtype, records_with_rvk_by_pubtype, number_of_records_by_medium, records_with_rvk_by_medium
    

if __name__ == '__main__':
    
    data_dir = 'data/lobid'
    # list of files in data directory
    sources = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]
    print(sources)
    
    total_number_of_records = 0
    total_records_with_rvk = 0
    total_rvk_notations_for_records = 0

    total_number_of_records_by_year = {}
    total_records_with_rvk_by_year = {}
    
    total_records_with_rvk_by_pubtype = {}
    total_number_of_records_by_pubtype = {}

    total_number_of_records_by_medium = {}
    total_records_with_rvk_by_medium = {}
        
    for source in sources:
        lobid_data = read_data_from_lobid_dump(data_dir + '/' + source)
        number_of_records, records_with_rvk, rvk_notations_for_records, number_of_records_by_year, records_with_rvk_by_year, number_of_records_by_pubtype, records_with_rvk_by_pubtype, number_of_records_by_medium, records_with_rvk_by_medium = analyse_rvk_in_lobid(lobid_data)
        
        total_number_of_records += number_of_records
        total_records_with_rvk += records_with_rvk
        total_rvk_notations_for_records += rvk_notations_for_records
        
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
    
    print('Number of records: %d' % total_number_of_records)
    print('Records with RVK: %d' % total_records_with_rvk)
    print('RVK notations for records: %d' % total_rvk_notations_for_records)
    
    print('Records by publication year: %s' % total_number_of_records_by_year)
    print('Records with RVK by publication year: %s' % total_records_with_rvk_by_year)
    
    print('Records by publication type: %s' % total_number_of_records_by_pubtype)
    print('Records with RVK by publication type: %s' % total_records_with_rvk_by_pubtype)
    
    print('Records by medium: %s' % total_number_of_records_by_medium)
    print('Records with RVK by medium: %s' % total_records_with_rvk_by_medium)

    print('---')
    
    with open('data/rvk_in_lobid.tsv', 'w') as f:
        f.write('Number of records\t%d\n' % total_number_of_records)
        f.write('Records with RVK\t%d\n' % total_records_with_rvk)
        f.write('RVK notations for records\t%d\n' % total_rvk_notations_for_records)
                
    # get rvk notations for pubtype in percent
    with open('data/rvk_in_lobid_by_pubtype.tsv', 'w') as f:
        for pubtype in total_number_of_records_by_pubtype:
            if pubtype in total_records_with_rvk_by_pubtype:
                f.write('%s\t%s\t%s\t%f\n' % (pubtype, total_number_of_records_by_pubtype[pubtype], total_records_with_rvk_by_pubtype[pubtype], (total_records_with_rvk_by_pubtype[pubtype] / total_number_of_records_by_pubtype[pubtype]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (pubtype, total_number_of_records_by_pubtype[pubtype]))
            
    # get rvk notations for year in percent sorted by year descending
    with open('data/rvk_in_lobid_by_year.tsv', 'w') as f:
        for year in sorted(total_number_of_records_by_year, reverse=True):
            if year in total_records_with_rvk_by_year:
                f.write('%s\t%s\t%s\t%f\n' % (year, total_number_of_records_by_year[year], total_records_with_rvk_by_year[year], (total_records_with_rvk_by_year[year] / total_number_of_records_by_year[year]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (year, total_number_of_records_by_year[year]))
                
    # get rvk notations for medium in percent
    with open('data/rvk_in_lobid_by_medium.tsv', 'w') as f:
        for medium in total_number_of_records_by_medium:
            if medium in total_records_with_rvk_by_medium:
                f.write('%s\t%s\t%s\t%f\n' % (medium, total_number_of_records_by_medium[medium], total_records_with_rvk_by_medium[medium], (total_records_with_rvk_by_medium[medium] / total_number_of_records_by_medium[medium]) * 100))
            else:
                f.write('%s\t%s\t0\t0\n' % (medium, total_number_of_records_by_medium[medium]))
