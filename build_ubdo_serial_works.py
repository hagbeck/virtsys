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
from urllib.parse import quote_plus

import config_ubdo as config

metadata_file = '%s/serial_works.tsv' % config.SUNRISE_DATA_DIR


def read_sunrise_data():

    with open(metadata_file, 'w') as mapped_ids_data:

        with open('%s/unload.TIT' % config.SUNRISE_DATA_DIR, 'r') as title_data:

            hbz_id = ''
            is_e_resource = False
            document_type = None
            shelfmarks = []

            for line in title_data:

                if line.startswith('9999:'):

                    if hbz_id and document_type and (document_type == 'p' or document_type == 'z' or document_type == 'r'):

                        if shelfmarks:

                            for shelfmark in shelfmarks:
                                mapped_ids_data.write('%s\t%s\t%s\t%s\n' % (hbz_id, document_type, is_e_resource, shelfmark))

                    hbz_id = ''
                    is_e_resource = False
                    document_type = ''
                    shelfmarks = []
                else:

                    if line.startswith('0010.001:'):

                        hbz_id = line.strip().replace('0010.001:', '')

                    elif line.startswith('0036:'):

                        document_type = line.strip().split(':')[1]

                    elif line.startswith('0807:'):

                        value = line.strip().split(':')[1]

                        if value == 'g':
                            is_e_resource = True

                    elif line.startswith('1204'):

                        shelfmarks.append(line.strip().split(':')[1])

                    # FOME, EGZ und co.
                    elif line.startswith('1206'):

                        shelfmarks.append(line.strip().split(':')[1])

        print('serial_works.tsv ready.')


def build_linked_data():

    with open(config.SERIALS_TTL_DATA, 'w') as rdfdata:

        rdfdata.write('@prefix dct: <http://purl.org/dc/terms/> .\n')
        rdfdata.write('@prefix ecrm: <http://erlangen-crm.org/current/> .\n')
        rdfdata.write('@prefix efrbroo: <http://erlangen-crm.org/efrbroo/> .\n')
        rdfdata.write('@prefix bibo: <http://purl.org/ontology/bibo/> .\n')

        with open(metadata_file, 'r') as thedata:

            for line in thedata:

                rdf_string = ''

                line_data = line.strip().split('\t')
                rdf_string += '<http://lobid.org/resources/%s> a efrbroo:F18_Serial_Work .\n' % line_data[0]
                if line_data[1] == 'p' or line_data[1] == 'z':
                    rdf_string += '<http://lobid.org/resources/%s> a bibo:Periodical .\n' % line_data[0]
                else:
                    rdf_string += '<http://lobid.org/resources/%s> a bibo:Series .\n' % line_data[0]
                rdf_string += '<http://lobid.org/resources/%s> dct:identifier "%s" .\n' % (line_data[0], line_data[0])

                rdf_string += '<http://lobid.org/resources/%s> dct:type "%s" .\n' % (line_data[0], line_data[1])

                if ast.literal_eval(line_data[2]):
                    rdf_string += '<http://lobid.org/resources/%s> dct:medium "digital" .\n' % line_data[0]
                else:
                    rdf_string += '<http://lobid.org/resources/%s> dct:medium "print" .\n' % line_data[0]

                    if line_data[1] == 'p' or line_data[1] == 'z':
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> a ecrm:E78_Curated_Holding, dct:Collection .\n' % quote_plus(line_data[3])
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> dct:identifier \"%s\" .\n' % (quote_plus(line_data[3]), line_data[3])
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> dct:relation <http://lobid.org/resources/%s> .\n' % (quote_plus(line_data[3]), line_data[0])
                        rdf_string += '<http://lobid.org/resources/%s> dct:relation <http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> .\n' % (line_data[0], quote_plus(line_data[3]))
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> dct:isPartOf <http://data.ub.tu-dortmund.de/resources/collection:DE-290-0:%s> .\n' % (quote_plus(line_data[3]), line_data[3].split(' ')[0])

                rdfdata.write(rdf_string)


if __name__ == '__main__':

    # prepare Sunrise data for building linked data
    read_sunrise_data()

    # build bibliographic entities for ubdo
    build_linked_data()
