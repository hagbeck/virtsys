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
from os import listdir
from os.path import isfile, join
import re
import simplejson as json
from urllib.parse import quote_plus
import uuid
import xmltodict

from util_cleanup import cleanup_dir

import config_cg as config

data_dir = config.data_dir
graphdb_import = config.graphdb_import

cg_wrk_bundle_dir = '%s' % data_dir
cg_bundles_json = '%s/cg/json_data' % graphdb_import
cg_bundles_ttl = '%s/cg/ttl_data' % graphdb_import
cg_bundles_prov_ttl = '%s/cg/prov_data' % graphdb_import

base_uris = {
    "DE-101": "http://d-nb.info/%s",  # DNB
    "DE-576": "http://swb.bsz-bw.de/DB=2.1/PRS=rdf/PPNSET?PPN=%s",  # SWB
    "DE-601": "http://lobid.org/organisations/DE-601/resources/%s",  # GBV
    "DE-603": "http://lobid.org/organisations/DE-603/resources/%s",  # HeBIS
    "DE-604": "http://lod.b3kat.de/title/%s",  # BVB
    "DE-605": "http://lobid.org/resources/%s"  # HBZ
}


def __normalize_rvk_data(data=''):

    normalized_data = ''

    normalized_data = data.upper().replace('/', '')

    RVK_CLASS = re.compile('[A-Z]{2}\s\d{2,6}')
    RVK_CLASS_wo_space = re.compile('[A-Z]{2}\d{2,6}')

    #print(RVK_CLASS.match(normalized_data))
    if not RVK_CLASS.match(normalized_data):
        # print('\tnot valid')
        if RVK_CLASS_wo_space.match(normalized_data):
            # print('\tnow valid')
            normalized_data = normalized_data[0:2] + ' ' + normalized_data[2:]
        else:
            # print('\tstill not valid')
            normalized_data = ''

    return normalized_data


def __init_bundle_data(bundle=None):

    if not bundle:
        raise ValueError('No bundle data to work with!')

    bundle_data = {}

    for field in bundle['marc:controlfield']:

        if field['@tag'] == '001':
            record_id = field['#text']
            # print('record_id: ' + record_id)
            bundle_data['id'] = record_id
            tmp = record_id.split('_')
            bundle_data['prov'] = {
                "id": tmp[1],
                "agent": tmp[0],
                "timestamp": tmp[2]
            }

    return bundle_data


def __build_members_and_provs(bundle=None):

    if not bundle:
        raise ValueError('No bundle data to work with!')

    members = []
    provs = {}

    # get bundle data: members and provenance data
    for field in bundle['marc:datafield']:

        if type(field) is not str:

            # get bundle member
            if field['@tag'] == '035':
                member = ''
                member_prov_id = ''
                for subfield in field['marc:subfield']:
                    if subfield['@code'] == 'a':
                        member = subfield['#text']
                    if subfield['@code'] == '8':
                        member_prov_id = subfield['#text'].replace('\\', '')

                members.append(member)
                provs[member_prov_id] = {"id": member.split(')')[1], "agent": member.split(')')[0].replace('(', '')}

            # get prov data from 883
            if field['@tag'] == '883':
                prov = {}
                prov_id = ''
                try:
                    for subfield in field['marc:subfield']:
                        if subfield['@code'] == '8' and subfield.get('#text'):
                            prov_id = subfield['#text'].replace('\\', '')
                        if subfield['@code'] == 'w' and subfield.get('#text'):
                            prov["id"] = subfield['#text'].split(')')[1]
                            prov["agent"] = subfield['#text'].split(')')[0].replace('(', '')
                        if subfield['@code'] == 'q' and subfield.get('#text'):
                            prov["agent"] = subfield['#text']
                            prov["id"] = ''
                        if subfield['@code'] == 'c' and subfield.get('#text'):
                            prov["score"] = subfield['#text']
                        if subfield['@code'] == 'd' and subfield.get('#text'):
                            prov["date"] = subfield['#text']
                        if subfield['@code'] == 'a' and subfield.get('#text'):
                            prov["description"] = subfield['#text']
                    provs[prov_id] = prov
                except:
                    pass

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
                provs[member_prov_id] = {"id": member.split(')')[1], "agent": member.split(')')[0].replace('(', '')}
            # print('OTHER TYPE %s: %s' % (type(field), bundle['marc:datafield']))
            # print('OTHER TYPE member: %s' % members)
            break

    # print('members: %s' % members)
    # print('provs: %s' % provs)

    return members, provs


def __build_classifications_and_subjects(bundle=None, provs=None):

    if not bundle or not provs:
        raise ValueError('No bundle or prov data to work with!')

    classifications = {}
    subjects = {}

    for field in bundle['marc:datafield']:

        item = {}

        if type(field) is not str:
            # get DDC (082)
            if field['@tag'] == '082':
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

                item = {'notation': code_a}
                for code in code_8:
                    if code in provs.keys():
                        if item.get('prov'):
                            item['prov'].append(provs[code])
                        else:
                            item['prov'] = [provs[code]]

                if not code_2:
                    code_2 = 'ddc'

                if classifications:

                    if classifications.get(code_2):
                        # TODO dedup item
                        classifications[code_2].append(item)
                    else:
                        classifications[code_2] = [item]

                else:
                    classifications = {code_2: [item]}

            # get Additional DDC (083)
            if field['@tag'] == '083':
                code_a = ''
                code_2 = ''
                code_8 = []
                for subfield in field['marc:subfield']:
                    if subfield['@code'] == '2' and subfield.get('#text'):
                        code_2 = subfield['#text']
                    if subfield['@code'] == 'a' and subfield.get('#text'):
                        code_a = subfield['#text']
                    if subfield['@code'] == '8' and subfield.get('#text'):
                        code_8.append(subfield['#text'].replace('\\', ''))

                item = {'notation': code_a}
                for code in code_8:
                    if code in provs.keys():
                        if item.get('prov'):
                            item['prov'].append(provs[code])
                        else:
                            item['prov'] = [provs[code]]

                if not code_2:
                    code_2 = 'altddc'

                if classifications:

                    if classifications.get(code_2):
                        # TODO dedup item
                        classifications[code_2].append(item)
                    else:
                        classifications[code_2] = [item]

                else:
                    classifications = {code_2: [item]}

            # get other subjects and classification
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

                if code_2:
                    item = {'notation': code_a}
                    for code in code_8:
                        if code in provs.keys():
                            if item.get('prov'):
                                item['prov'].append(provs[code])
                            else:
                                item['prov'] = [provs[code]]

                    if classifications:

                        if classifications.get(code_2):
                            # TODO dedup item
                            classifications[code_2].append(item)
                        else:
                            classifications[code_2] = [item]

                    else:
                        classifications = {code_2: [item]}

            # get all subjects (6xx)
            if field['@tag'].startswith('6'):
                code_a = ''
                code_2 = ''
                code_8 = []
                code_0 = []
                for subfield in field['marc:subfield']:
                    if subfield['@code'] == 'a' and subfield.get('#text'):
                        code_a = subfield['#text']
                    if subfield['@code'] == '2' and subfield.get('#text'):
                        code_2 = subfield['#text']
                    if subfield['@code'] == '8' and subfield.get('#text'):
                        code_8.append(subfield['#text'].replace('\\', ''))
                    if subfield['@code'] == '0' and subfield.get('#text'):
                        code_0.append(subfield['#text'])

                if code_2 == 'gnd' and code_0:
                    item = {'topic': code_a, 'id': code_0}
                    for code in code_8:
                        if code in provs.keys():
                            if item.get('prov'):
                                item['prov'].append(provs[code])
                            else:
                                item['prov'] = [provs[code]]

                    if subjects:

                        if subjects.get(code_2):
                            # TODO dedup item
                            subjects[code_2].append(item)
                        else:
                            subjects[code_2] = [item]

                    else:
                        subjects = {code_2: [item]}

    return classifications, subjects


def __build_json_data(bundle_data=None, filename=''):

    if not bundle_data:
        raise ValueError('No bundle data to write!')

    if not filename:
        raise ValueError('No filename defined!')

    with open(str('%s/%s.json' % (cg_bundles_json, filename.replace('.marcxml', ''))), 'a') as jsondata:
        jsondata.write(json.dumps(bundle_data))
        jsondata.write('\n')


def __build_ttl_data(bundle_data=None, filename=''):

    if not bundle_data:
        raise ValueError('No bundle data to write!')

    if not filename:
        raise ValueError('No filename defined!')

    with open(str('%s/%s.ttl' % (cg_bundles_ttl, filename.replace('.marcxml', ''))), 'a') as rdfdata:
        tmp = bundle_data['id'].split('_')
        bundle_id = '%s_%s' % (tmp[0], tmp[1])
        # print(bundle_id)

        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> a <http://purl.org/net/bundle#Bundle> .\n' % bundle_id)
        if bundle_data.get('members'):
            for item in bundle_data['members']:
                tmp = item.split(')')
                try:
                    item_as_uri = base_uris[tmp[0].replace('(', '')] % tmp[1]
                    rdfdata.write(
                        '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://purl.org/net/bundle#encapsulates> <%s> .\n' % (
                        bundle_id, item_as_uri))
                    rdfdata.write(
                        '<%s> <http://purl.org/net/bundle#encapsulated_in> <http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> .\n' % (
                        item_as_uri, bundle_id))
                except:
                    #print("ERROR: %s" % item)
                    pass

            # classifications
            if bundle_data.get('classifications'):
                for classification in bundle_data.get('classifications').keys():
                    for item in bundle_data.get('classifications').get(classification):
                        notation = quote_plus(item.get('notation').replace(' ', ''))
                        rdfdata.write(
                            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://purl.org/dc/terms/subject> <http://data.ub.tu-dortmund.de/resource/%s/%s> .\n' % (
                            bundle_id, quote_plus(classification.replace(' ', '')), notation))
            # subjects
            if bundle_data.get('subjects'):
                for item in bundle_data.get('subjects').get('gnd'):
                    try:
                        for subject_id in item['id']:
                            if subject_id.startswith('(DE-588)'):
                                gnd_id = quote_plus(subject_id.replace('(DE-588)', ''))
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://purl.org/dc/terms/subject> <https://d-nb.info/gnd/%s> .\n' % (
                                    bundle_id, gnd_id))
                    except Exception as e:
                        # print(e)
                        # print(item)
                        pass
        else:
            # print('ERROR no members: %s' % bundle_data)
            pass


def __build_prov_data(bundle_data=None, filename=''):

    if not bundle_data:
        raise ValueError('No bundle data to write!')

    if not filename:
        raise ValueError('No filename defined!')

    with open(str('%s/%s.ttl' % (cg_bundles_prov_ttl, filename.replace('.marcxml', ''))), 'a') as rdfdata:
        tmp = bundle_data['id'].split('_')
        bundle_id = '%s_%s' % (tmp[0], tmp[1])
        # print(bundle_id)

        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> a <http://www.w3.org/ns/prov#Entity> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> a <http://erlangen-crm.org/current/E1_CRM_Entity> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://www.w3.org/ns/prov#wasGeneratedBy> <http://data.ub.tu-dortmund.de/resource/cg/activity/%s>.\n' % (
            bundle_id, bundle_id))
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://www.w3.org/ns/prov#wasAttributedTo> <http://data.ub.tu-dortmund.de/resource/cg/agent/%s>.\n' % (
            bundle_id, bundle_id))

        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/activity/%s> a <http://www.w3.org/ns/prov#Activity> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/activity/%s> a <http://erlangen-crm.org/current/E7_Activity> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/activity/%s> <http://www.w3.org/ns/prov#endedAtTime> "%s"^^xsd:dateTime .\n' % (
            bundle_id, bundle_data['prov']['timestamp']))
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/activity/%s> <http://www.w3.org/ns/prov#wasAssociatedWith> <http://data.ub.tu-dortmund.de/resource/cg/agent/%s> .\n' % (
            bundle_id, bundle_id))

        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/agent/%s> a <http://www.w3.org/ns/prov#SoftwareAgent> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/agent/%s> a <http://erlangen-crm.org/current/E39_Actor> .\n' % bundle_id)
        rdfdata.write(
            '<http://data.ub.tu-dortmund.de/resource/cg/agent/%s> <http://www.w3.org/ns/prov#actedOnBehalfOf> <http://lobid.org/organisations/DE-101> .\n' % bundle_id)
        rdfdata.write('<http://lobid.org/organisations/DE-101> a <http://www.w3.org/ns/prov#Agent> .\n')

        if bundle_data.get('members'):

            # classifications
            if bundle_data.get('classifications'):
                for classification in bundle_data.get('classifications').keys():
                    for item in bundle_data.get('classifications').get(classification):
                        notation = quote_plus(item.get('notation').replace(' ', ''))
                        if item['prov']:
                            for prov in item['prov']:
                                try:
                                    if prov['id']:
                                        prov_id = '%s_%s' % (prov['agent'], prov['id'])
                                    else:
                                        prov_id = '%s_%s' % (prov['agent'], str(uuid.uuid4()))
                                except Exception as e:
                                    print('%s: %s' % (e, classification))

                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://erlangen-crm.org/current/P41i_was_classified_by> <http://data.ub.tu-dortmund.de/resource/activity/%s> .\n' % (
                                    bundle_id, prov_id))
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://erlangen-crm.org/current/P41_classified>  <http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s>.\n' % (
                                    prov_id, bundle_id))

                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/%s/%s> a <http://erlangen-crm.org/current/E55_Type> .\n' % (
                                    quote_plus(classification.replace(' ', '')), notation))
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/%s/%s> <http://erlangen-crm.org/current/P42i_was_assigned_by> <http://data.ub.tu-dortmund.de/resource/activity/%s> .\n' % (
                                    quote_plus(classification.replace(' ', '')), notation, prov_id))
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://erlangen-crm.org/current/P42_assigned> <http://data.ub.tu-dortmund.de/resource/%s/%s> .\n' % (
                                    prov_id, quote_plus(classification.replace(' ', '')), notation))

                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/activity/%s> a <http://www.w3.org/ns/prov#Activity> .\n' % prov_id)
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/activity/%s> a <http://erlangen-crm.org/current/E17_Type_Assignment> .\n' % prov_id)
                                if prov.get('timestamp'):
                                    rdfdata.write(
                                        '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/ns/prov#endedAtTime> "%s"^^xsd:dateTime .\n' % (
                                        prov_id, prov['timestamp']))
                                if prov.get('description'):
                                    rdfdata.write(
                                        '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://purl.org/dc/terms/description> "%s" .\n' % (
                                        prov_id, prov['description']))
                                if prov.get('score'):
                                    rdfdata.write(
                                        '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> "%s"^^xsd:decimal .\n' % (
                                        prov_id, prov['score'].replace(',', '.')))
                                rdfdata.write(
                                    '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/ns/prov#wasAssociatedWith> <http://lobid.org/organisations/%s> .\n' % (
                                    prov_id, prov['agent']))

                                rdfdata.write(
                                    '<http://lobid.org/organisations/%s> a <http://www.w3.org/ns/prov#Agent> .\n' %
                                    prov['agent'])
                                rdfdata.write(
                                    '<http://lobid.org/organisations/%s> a <http://erlangen-crm.org/current/E39_Actor> .\n' %
                                    prov['agent'])

            # subjects
            if bundle_data.get('subjects'):
                for item in bundle_data.get('subjects').get('gnd'):
                    try:
                        for subject_id in item['id']:
                            if subject_id.startswith('(DE-588)'):
                                gnd_id = quote_plus(subject_id.replace('(DE-588)', ''))
                                if item['prov']:
                                    for prov in item['prov']:
                                        try:
                                            if prov['id']:
                                                prov_id = '%s_%s' % (prov['agent'], prov['id'])
                                            else:
                                                prov_id = '%s_%s' % (prov['agent'], str(uuid.uuid4()))
                                        except Exception as e:
                                            print('%s: %s' % (e, classification))

                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://purl.org/dc/terms/subject> <https://d-nb.info/gnd/%s> .\n' % (
                                            bundle_id, gnd_id))
                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s> <http://erlangen-crm.org/current/P41i_was_classified_by> <http://data.ub.tu-dortmund.de/resource/activity/%s> .\n' % (
                                            bundle_id, prov_id))
                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://erlangen-crm.org/current/P41_classified>  <http://data.ub.tu-dortmund.de/resource/cg/wrk_bundle/%s>.\n' % (
                                            prov_id, bundle_id))

                                        rdfdata.write(
                                            '<https://d-nb.info/gnd/%s> a <http://erlangen-crm.org/current/E55_Type> .\n' % gnd_id)
                                        rdfdata.write(
                                            '<https://d-nb.info/gnd/%s> <http://erlangen-crm.org/current/P42i_was_assigned_by> <http://data.ub.tu-dortmund.de/resource/activity/%s> .\n' % (
                                            gnd_id, prov_id))
                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://erlangen-crm.org/current/P42_assigned> <https://d-nb.info/gnd/%s> .\n' % (
                                            prov_id, gnd_id))

                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/activity/%s> a <http://www.w3.org/ns/prov#Activity> .\n' % prov_id)
                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/activity/%s> a <http://erlangen-crm.org/current/E17_Type_Assignment> .\n' % prov_id)
                                        if prov.get('timestamp'):
                                            rdfdata.write(
                                                '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/ns/prov#endedAtTime> "%s"^^xsd:dateTime .\n' % (
                                                prov_id, prov['timestamp']))
                                        if prov.get('description'):
                                            rdfdata.write(
                                                '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://purl.org/dc/terms/description> "%s" .\n' % (
                                                prov_id, prov['description']))
                                        if prov.get('score'):
                                            rdfdata.write(
                                                '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> "%s"^^xsd:decimal .\n' % (
                                                prov_id, prov['score'].replace(',', '.')))
                                        rdfdata.write(
                                            '<http://data.ub.tu-dortmund.de/resource/activity/%s> <http://www.w3.org/ns/prov#wasAssociatedWith> <http://lobid.org/organisations/%s> .\n' % (
                                            prov_id, prov['agent']))

                                        rdfdata.write(
                                            '<http://lobid.org/organisations/%s> a <http://www.w3.org/ns/prov#Agent> .\n' %
                                            prov['agent'])
                                        rdfdata.write(
                                            '<http://lobid.org/organisations/%s> a <http://erlangen-crm.org/current/E39_Actor> .\n' %
                                            prov['agent'])
                    except Exception as e:
                        print(e)
                        print(item)
        else:
            # print('ERROR no members: %s' % bundle_data)
            pass


def __build_the_data(file=''):

    data = ''

    # print('file: %s' % '%s%s' % (cg_wrk_bundle_dir, file))
    with open('%s/%s' % (cg_wrk_bundle_dir, file), 'r') as xmldata:
        for line in xmldata:
            data += line.strip()

    try:
        thedata = xmltodict.parse(data)
    except Exception as e:
        return 'ERROR in processing %s: %s' % (file, e), 0

    bundle_counter = 0
    if 'marc:collection' in thedata:

        # for each record (= CG bundle)
        for bundle in thedata['marc:collection']['marc:record']:

            # print(bundle)

            # get bundle ID and init bundle_data
            bundle_data = __init_bundle_data(bundle=bundle)

            # get bundle data: members and provenance data
            members, provs = __build_members_and_provs(bundle=bundle)

            # next if bundle not contains members of DE-605
            is_bundle_with_hbz = False
            for member in members:
                if '(DE-605)' in member:
                    is_bundle_with_hbz = True
                    break

            if is_bundle_with_hbz:

                bundle_data['members'] = members
                bundle_counter += 1

                # get bundle data: subjects and classifications
                classifications, subjects = __build_classifications_and_subjects(bundle=bundle, provs=provs)
                bundle_data['classifications'] = classifications
                bundle_data['subjects'] = subjects

                # build data files for json as jsonl
                __build_json_data(bundle_data=bundle_data, filename=file)

                # build data files for ttl
                __build_ttl_data(bundle_data=bundle_data, filename=file)

                # build data files for prov data in ttl
                __build_prov_data(bundle_data=bundle_data, filename=file)

    return '%s processed. %s bundles with member DE-605 found.' % (file, bundle_counter), bundle_counter


def __process():

    # get relevant(!) files as sources
    cg_wrk_bundle_files = [f for f in listdir(cg_wrk_bundle_dir) if isfile(join(cg_wrk_bundle_dir, f))]

    files_to_work_with = []
    for file in cg_wrk_bundle_files:

        if file.endswith('.marcxml'):
            files_to_work_with.append(file)

    # work on the data
    total_bundles = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=config.number_of_pool_workers) as executor:

        for message, bundle_counter in executor.map(__build_the_data, cg_wrk_bundle_files):

            total_bundles += bundle_counter
            print(message)

    print('>>> SUMMARY <<<')
    print('Worked on %s CG data files.' % len(files_to_work_with))
    print('%s bundles with member DE-605 found.' % total_bundles)


if __name__ == '__main__':

    start = timeit.default_timer()

    # cleanup
    cleanup_dir(data_dir=cg_bundles_json)
    cleanup_dir(data_dir=cg_bundles_ttl)
    cleanup_dir(data_dir=cg_bundles_prov_ttl)

    # process
    __process()

    stop = timeit.default_timer()
    duration = stop - start
    print('duration of building CultureGraph linked data: %s\n' % duration)
