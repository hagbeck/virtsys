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

import re
import timeit
from urllib.parse import quote_plus

import simplejson as json

import config_ubdo as config


def read_sunrise_data():

    # erzeuge mediennummer_katkey_zweigstelle_signatur.tsv aus buchdaten.out
    with open(config.ITEMS_FILE, 'w') as holdings_data:

        with open('%s/buchdaten.out' % config.SUNRISE_DATA_DIR, 'r') as local_holdings_data:

            local_id = ''
            mediennummer = ''
            location = ''
            shelfmark = ''
            collection = ''

            for line in local_holdings_data:

                if line.startswith('9999:'):

                    if not mediennummer.startswith('@'):
                        holdings_data.write('%s\t%s\t%s\t%s\t%s\n' % (mediennummer, local_id, location, shelfmark, collection))

                    local_id = ''
                    mediennummer = ''
                    location = ''
                    shelfmark = ''
                    collection = ''

                else:

                    if line.startswith('0000:'):

                        mediennummer = line.strip().replace('0000:', '')

                    elif line.startswith('0004.001:'):

                        local_id = line.strip().replace('0004.001:', '')

                    elif line.startswith('0029.001:'):

                        location = line.strip().replace('0029.001:', '')

                    elif line.startswith('0014.001:'):

                        shelfmark = line.strip().replace('0014.001:', '')

                    elif line.startswith('0016.001:'):

                        collection = line.strip().replace('0016.001:', '')

    print('mediennummer_katkey_zweigstelle_signatur.tsv ready.')

    # erzeuge katkey_hbzid.tsv aus unload.TIT and collect data for the mvw bundles
    mvw_bundles = {}
    with open(config.MAPPED_IDS_FILE, 'w') as mapped_ids_data:

        with open('%s/unload.TIT' % config.SUNRISE_DATA_DIR, 'r') as title_data:

            local_id = ''
            hbz_id = ''

            mvw_ids = []

            for line in title_data:

                if line.startswith('9999:'):

                    if hbz_id:
                        mapped_ids_data.write('%s\t%s\n' % (local_id, hbz_id))

                        if mvw_ids:
                            for item in mvw_ids:

                                if mvw_bundles.get(item):
                                    mvw_bundles[item].append(hbz_id)
                                else:
                                    mvw_bundles[item] = [hbz_id]

                    local_id = ''
                    hbz_id = ''
                    mvw_ids = []
                else:

                    if line.startswith('0000:'):

                        local_id = line.strip().replace('0000:', '')

                    elif line.startswith('0010.001:'):

                        hbz_id = line.strip().replace('0010.001:', '')

                    elif line.startswith('0453'):

                        mvw_id = line.strip().split(':')[1]

                        if mvw_id  and mvw_id not in mvw_ids:
                            mvw_ids.append(mvw_id)

    print('katkey_hbzid.tsv ready.')

    # erzeuge mvw_bundles.json
    if mvw_bundles:

        with open(config.MVW_BUNDLES_FILE, 'w') as fp:

            json.dump(mvw_bundles, fp, indent=2)

        print('mvw_bundles.json ready.')


def build_linked_data():

    # read mapped_ids_file to mapped_ids_data
    mapped_ids_data = {}
    with open(config.MAPPED_IDS_FILE, 'r') as mapped_ids:

        for line in mapped_ids:

            tmp = line.strip().split('\t')
            mapped_ids_data[tmp[0]] = tmp[1]

    print('%s mapped IDs loaded.' % len(mapped_ids_data.keys()))

    # build linked data
    lbs_reg = re.compile("L [A-Z][a-z] .*")
    efb_a_reg = re.compile("^A [0-9][0-9][0-9] .*")
    efb_p_reg = re.compile("^P[A-G,S][A-Z].*")

    with open(config.ITEMS_TTL_DATA, 'w') as rdfdata:

        rdfdata.write('@prefix dct: <http://purl.org/dc/terms/> .\n')
        rdfdata.write('@prefix ecrm: <http://erlangen-crm.org/current/> .\n')
        rdfdata.write('@prefix efrbroo: <http://erlangen-crm.org/efrbroo/> .\n')
        rdfdata.write('\n')

        with open(config.ITEMS_FILE, 'r') as thedata:

            for line in thedata:

                line_data = line.strip().split('\t')

                if mapped_ids_data.get(line_data[1]) and len(line_data) >= 4:

                    rdf_string = ''

                    signatur = line_data[3]

                    subcollection = None
                    if len(line_data) == 5:
                        subcollection = line_data[4]

                    if 's. Zeitschrift' in signatur:
                        continue

                    location = 'DE-290-%s' % line_data[2]
                    collection = None

                    if line_data[2] == '0' and subcollection and (subcollection == '23' or subcollection == '80'):
                        location = 'DE-290-23'
                        collection = signatur.split('/')[0]
                    elif line_data[2] == '0' and subcollection and subcollection == '18':
                        location = 'DE-290-0:FOME'
                        collection = signatur.split(' ')[0]
                    elif line_data[2] == '0' and subcollection and subcollection == '8':
                        collection = 'Rara'
                    elif line_data[2] == '0' and subcollection and (subcollection == '7' or subcollection == '11'):
                        print('Alte Signaturgruppe: %s' % line_data)
                        continue
                    elif line_data[2] == '0' and subcollection and (subcollection == '3' or subcollection == '5'):
                        collection = 'HB'
                    elif line_data[2] == '0'and lbs_reg.match(signatur):
                        collection = '%s%s' % (signatur.split(' ')[0], signatur.split(' ')[1])
                    elif line_data[2] == '12'and efb_a_reg.match(signatur):
                        collection = signatur[:5].replace(' ', '')
                    elif line_data[2] == '12' and efb_p_reg.match(signatur):
                        collection = signatur[:2]
                    elif line_data[2] == '9':
                        print("Signatur 9: %s" % signatur)
                        collection = signatur.split('/')[0]
                        if not collection.startswith('X'):
                            if 'Buero' in collection:
                                print('Formatfehler in Signatur: %s' % line_data)
                                continue
                            elif collection.startswith('65'):
                                collection = '65'
                            elif collection.startswith('85'):
                                collection = '85'
                            else:
                                collection = collection[:1]
                        else:
                            collection = collection.split(' ')[0]
                        print("\t -> collection: %s" % collection)
                    elif line_data[2] == '10':
                        print("Signatur 10: %s" % signatur)
                        collection = signatur.split('/')[0]
                        if not collection.startswith('Y'):
                            if 'Buero' in collection:
                                print('Formatfehler in Signatur: %s' % line_data)
                                continue
                            elif collection.startswith('16'):
                                collection = '16'
                            else:
                                collection = collection[:1] + '0'
                        else:
                            collection = collection.split(' ')[0]
                        print("\t -> collection: %s" % collection)
                    elif line_data[2] == '0' or line_data[2] == '12':
                        if ' ' not in signatur:
                            print('Formatfehler in Signatur: %s' % line_data)
                            continue
                        else:
                            part = signatur.split(' ')[0]
                            if '-' in part:
                                collection = part.split('-')[0]
                            else:
                                collection = part

                    if collection:
                        collection = quote_plus(collection)

                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/item:%s> a efrbroo:F5_Item .\n' % quote_plus(line_data[0])
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/item:%s> dct:identifier "%s" .\n' % (quote_plus(line_data[0]), line_data[0])
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/item:%s> dct:title "%s" .\n' % (quote_plus(line_data[0]), line_data[3])
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/item:%s> efrbroo:R7_is_example_of <http://lobid.org/resources/%s> .\n' % (quote_plus(line_data[0]), mapped_ids_data[line_data[1]])
                        rdf_string += '<http://lobid.org/resources/%s> efrbroo:R7i_has_example <http://data.ub.tu-dortmund.de/resources/item:%s> .\n' % (mapped_ids_data[line_data[1]], quote_plus(line_data[0]))
                        rdf_string += '<http://data.ub.tu-dortmund.de/resources/item:%s> dct:isPartOf <http://data.ub.tu-dortmund.de/resource/collection:%s:%s> .\n' % (quote_plus(line_data[0]), location, collection)
                        rdfdata.write(rdf_string)
                    else:
                        print('Keine Kollektion: %s' % line_data)


if __name__ == '__main__':

    start = timeit.default_timer()

    # prepare Sunrise data for building linked data
    read_sunrise_data()

    # build bibliographic entities for ubdo
    build_linked_data()

    stop = timeit.default_timer()
    duration = stop - start
    print('duration build_ubdo_print_items: %s' % duration)
