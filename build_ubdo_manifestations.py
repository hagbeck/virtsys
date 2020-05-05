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
import ast

import config_ubdo as config

# Benötigt wird:
# * hbz-ID
#  * 0807:g, falls es sich um eine E-Resource handelt
#  * 0036 ohne p,z,r
#  * 0425 (issued)

metadata_file = '%s/ubdo_manifestation_data.tsv' % config.SUNRISE_DATA_DIR


def read_sunrise_data():

    with open(metadata_file, 'w') as mapped_ids_data:

        with open('%s/unload.TIT' % config.SUNRISE_DATA_DIR, 'r') as title_data:

            hbz_id = ''
            is_e_resource = False
            document_type = None
            issued = None

            for line in title_data:

                if line.startswith('9999:'):

                    if hbz_id and document_type and document_type != 'p' and document_type != 'z' and document_type != 'r':

                        if issued:
                            issued = issued.split('-')[0]
                            issued = issued.split(',')[0]
                            issued = issued.split('/')[0]

                            issued = issued.replace('[', '').replace(']', '').replace(' ', '').replace('?', '')\
                                .replace('ca.', '').replace('P', '').replace('p', '').replace('C', '').replace('c', '') \
                                .replace('©', '').replace('X', '0').replace('(', '').replace(')', '')

                            if issued.startswith('s.a.') or issued.startswith('N/A') or issued.startswith('o.J.'):
                                issued = ''

                            if issued:
                                try:
                                    mapped_ids_data.write('%s\t%s\t%s\t%s\n' % (hbz_id, document_type, is_e_resource, int(issued)))
                                except:
                                    print('DATE-ERROR (0425) for %s: %s' % (hbz_id, issued))
                                    mapped_ids_data.write('%s\t%s\t%s\t%s\n' % (hbz_id, document_type, is_e_resource, ''))
                                    pass
                            else:
                                mapped_ids_data.write('%s\t%s\t%s\t%s\n' % (hbz_id, document_type, is_e_resource, ''))
                        else:
                            mapped_ids_data.write('%s\t%s\t%s\t%s\n' % (hbz_id, document_type, is_e_resource, ''))

                    hbz_id = ''
                    is_e_resource = False
                    document_type = ''
                    issued = None
                else:

                    if line.startswith('0010.001:'):

                        hbz_id = line.strip().replace('0010.001:', '')

                    elif line.startswith('0028:'):

                        document_type = line.strip().split(':')[1]

                    elif line.startswith('0036:'):

                        document_type = line.strip().split(':')[1]

                    elif line.startswith('0807:'):

                        value = line.strip().split(':')[1]

                        if value == 'g':
                            is_e_resource = True

                    elif line.startswith('0425.001'):

                        issued = line.strip().split(':')[1]


        print('metadata.tsv ready.')


def build_linked_data():

    with open(config.MANIFESTATIONS_TTL_DATA, 'w') as rdfdata:

        rdfdata.write('@prefix dct: <http://purl.org/dc/terms/> .\n')
        rdfdata.write('@prefix ecrm: <http://erlangen-crm.org/current/> .\n')
        rdfdata.write('@prefix efrbroo: <http://erlangen-crm.org/efrbroo/> .\n')
        rdfdata.write('@prefix bibo: <http://purl.org/ontology/bibo/> .\n')

        with open(metadata_file, 'r') as thedata:

            for line in thedata:

                rdf_string = ''

                line_data = line.strip().split('\t')

                if line_data[1] == 'n':
                    rdf_string += '<http://lobid.org/resources/%s> a efrbroo:F15_Complex_Work .\n' % line_data[0]
                    rdf_string += '<http://lobid.org/resources/%s> a bibo:MultiVolumeBook .\n' % line_data[0]
                else:
                    rdf_string += '<http://lobid.org/resources/%s> a efrbroo:F3_Manifestation_Product_Type .\n' % line_data[0]
                    rdf_string += '<http://lobid.org/resources/%s> a bibo:Book .\n' % line_data[0]

                rdf_string += '<http://lobid.org/resources/%s> dct:identifier "%s" .\n' % (line_data[0], line_data[0])

                if len(line_data) == 4 and line_data[3]:
                    rdf_string += '<http://lobid.org/resources/%s> dct:issued "%s"^^xsd:integer .\n' % (line_data[0], line_data[3])

                if line_data[1]:
                    rdf_string += '<http://lobid.org/resources/%s> dct:type "%s" .\n' % (line_data[0], line_data[1])

                if ast.literal_eval(line_data[2]):
                    rdf_string += '<http://lobid.org/resources/%s> dct:medium "digital" .\n' % line_data[0]
                else:
                    rdf_string += '<http://lobid.org/resources/%s> dct:medium "print" .\n' % line_data[0]

                rdfdata.write(rdf_string)


if __name__ == '__main__':

    # prepare Sunrise data for building linked data
    read_sunrise_data()

    # build bibliographic entities for ubdo
    build_linked_data()
