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
from urllib.parse import quote_plus

import xmltodict

register = []


def url_encode(query=''):

    return quote_plus(query)


def get_prefixes():
    prefixes = '''@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix rvk: <http://data.ub.tu-dortmund.de/resource/rvk/> .
@prefix rvk_reg: <http://data.ub.tu-dortmund.de/resource/rvk_register/> .
@prefix lobid_orga: <http://lobid.org/organisations/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix isdm: <http://data.ub.tu-dortmund.de/resource/isdm/> .
'''

    return prefixes


def get_general_data():

    general_data = '''<http://data.ub.tu-dortmund.de/resource/rvk> a skos:ConceptScheme, prov:Entity ;
  dct:title "Regensburger Verbundklassifikation Online (RVKO) - SKOS Version" ;
  prov:wasDerivedFrom isdm:rvko_source ;
  prov:wasGeneratedBy isdm:rvko_skosify ;
  dct:license "https://creativecommons.org/publicdomain/mark/1.0/"^^xsd:anyURI .

isdm:rvko_source a prov:Entity ;
  schema:name "Download der RVK-Datenbank als aktueller XML-Abzug" ;
  schema:version "2019_2" ;
  schema:url "https://rvk.uni-regensburg.de/regensburger-verbundklassifikation-online"^^xsd:anyURI ;
  schema:url "https://rvk.uni-regensburg.de/downloads/rvko_xml.zip"^^xsd:anyURI ;
  dct:license "https://creativecommons.org/publicdomain/mark/1.0/"^^xsd:anyURI .

isdm:rvko_skosify a prov:Activity ;
  prov:wasAssociatedWith prov:rvko2skos .

isdm:rvko2skos a prov:SoftwareAgent ;
  schema:name "RVKO to SKOS Transformer" ;
  prov:actedOnBehalfOf lobid_orga:DE-290 ;
  schema:url "https://github.org/hagbeck/rvko2skos"^^xsd:anyURI .
'''

    return general_data

# TODO skos:hasTopConcept
def build_node_data(node):

    notation = url_encode(node['@notation'].replace(' ', ''))

    node_data = 'rvk:%s a skos:Concept .\n' % notation
    node_data += 'rvk:%s skos:inScheme <http://data.ub.tu-dortmund.de/resource/rvk> .\n' % notation
    node_data += 'rvk:%s skos:notation "%s" .\n' % (notation, node['@notation'])
    node_data += 'rvk:%s skos:prefLabel "%s"@de .\n' % (notation, node['@benennung'].replace('"', '\\"'))

    if node.get('content'):
        node_data += 'rvk:%s skos:scopeNote "%s"@de .\n' % (notation, node['content']['@bemerkung'].replace('"', '\\"'))

    # add node to register
    if node.get('register'):

        if type(node['register']) is list:

            for reg in node['register']:

                reg_value = url_encode(reg.replace(' ', '').replace('.', '').replace(';', ''))
                node_data += 'rvk_reg:%s skos:member rvk:%s .\n' % (reg_value, notation)

                if reg not in register:
                    register.append(reg)

        elif type(node['register']) is str:

            reg_value = url_encode(node['register'].replace(' ', '').replace('.', '').replace(';', ''))
            node_data += 'rvk_reg:%s skos:member rvk:%s .\n' % (reg_value, notation)

            if node['register'] not in register:
                register.append(node['register'])

    # build children
    if node.get('children'):

        if type(node['children']['node']) is list:
            for child in node['children']['node']:
                child_notation = url_encode(child['@notation'].replace(' ', ''))
                node_data += 'rvk:%s skos:narrower rvk:%s .\n' % (notation, child_notation)
                node_data += 'rvk:%s skos:broader rvk:%s .\n' % (child_notation, notation)
                node_data += '%s' % build_node_data(child)
        elif type(node['children']['node']) is collections.OrderedDict:
            child_notation = url_encode(node['children']['node']['@notation'].replace(' ', ''))
            node_data += 'rvk:%s skos:narrower rvk:%s .\n' % (notation, child_notation)
            node_data += 'rvk:%s skos:broader rvk:%s .\n' % (child_notation, notation)
            node_data += '%s' % build_node_data(node['children']['node'])
        else:
            print('ERROR: children type not list nor dict')

    return '%s' % node_data


if __name__ == '__main__':

    rvko_data = 'data/rvko_xml/rvko_2019_2.xml'
    rvk_skos_data = 'data/rvko_xml/rvko_2019_2.skos.ttl'

    with open(rvk_skos_data, 'w') as metadata:

        # build ConceptScheme
        metadata.write(get_prefixes())
        metadata.write('\n')
        metadata.write(get_general_data())
        metadata.write('\n')

        with open(rvko_data, 'rb') as thedata:

            # read rvko XML data
            try:
                data = xmltodict.parse(thedata)['classification_scheme']
            except Exception as e:
                data = None
                print("ERROR: Couldn't read %s as XML." % rvko_data)
                print(e)

            if data:

                # build Concepts
                for data_node in data['node']:
                    metadata.write('%s' % build_node_data(data_node))

                # build register (= Collections)
                for item in register:

                    reg_value = url_encode(item.replace(' ', ''))

                    metadata.write('rvk_reg:%s a skos:Collection .\n' % reg_value.replace(' ', '').replace('.', '').replace(';', ''))
                    metadata.write('rvk_reg:%s skos:prefLabel "%s"@de .\n' % (reg_value.replace(' ', '').replace('.', '').replace(';', ''), item.replace('"', '\\"')))
