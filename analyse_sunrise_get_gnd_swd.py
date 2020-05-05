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
import re
from urllib.parse import quote_plus

import simplejson as json
import xmltodict

# Benötigt wird:
# * 0902, 0907, 0912, 0917, 0922, 0927, 0932, 0937, 0942, 0947

sunrise_data_dir = 'data/sunrise/2018-12-07'
metadata_file = '%s/gnd-swd-2-ddc.tsv' % sunrise_data_dir

sunrise_gnd_mapping = {}
gnd_swd_in_sunrise = []
gnd_swd_to_ddc = {}


def read_sunrise_data():

    with open('%s/unload.TIT' % sunrise_data_dir, 'r') as title_data:

        for line in title_data:

            if line.startswith('0902') or line.startswith('0907') or line.startswith('0912') or line.startswith('0917') \
                    or line.startswith('0922') or line.startswith('0927') or line.startswith('0932') or line.startswith('0937') \
                    or line.startswith('0942') or line.startswith('0947'):

                value = line.strip().replace('IDN: ', '').split(':')[1]

                if value not in sunrise_gnd_mapping.keys():
                    sunrise_gnd_mapping[value] = ''

    print('sunrise_gnd_mapping: %s' % len(sunrise_gnd_mapping.keys()))

    with open('%s/unload.SWD' % sunrise_data_dir, 'r') as swd_data:

        sunrise_id = ''
        gnd_id = ''

        for line in swd_data:

            if line.startswith('9999:'):

                if sunrise_id in sunrise_gnd_mapping.keys():
                    sunrise_gnd_mapping[sunrise_id] = gnd_id

                sunrise_id = ''
                gnd_id = ''

            else:

                if line.startswith('0000:'):
                    sunrise_id = line.strip().split(':')[1]
                elif line.startswith('0002:'):
                    gnd_id = line.strip().split(':')[1].replace('(DE-588)', '')

    gnd_swd_in_sunrise = [x for x in sunrise_gnd_mapping.values() if x != '']

    print('gnd_swd_in_sunrise: %s' % len(gnd_swd_in_sunrise))


def get_ddc_for_gnd():

    gnd2ddc_file = 'data/coli-conc/gnd2ddc_mappings.csv'

    with open('%s' % gnd2ddc_file, 'r') as title_data:

        for line in title_data:

            if 'fromNotation' in line:
                continue

            values = line.strip().split(',')

            gnd_swd_to_ddc[values[0].replace('"', '')] = values[1].replace('"', '')

        print('gnd_swd_to_ddc: %s' % len(gnd_swd_to_ddc.keys()))


def build_linked_data():

    with open(metadata_file, 'w') as title_subjects:

        with open('%s/unload.TIT' % sunrise_data_dir, 'r') as title_data:

            hbz_id = ''
            swd_ids = []

            cnt_records_with_ddc_from_gnd = 0
            cnt_ddc_classes_from_gnd = 0

            for line in title_data:

                if line.startswith('9999:'):

                    if swd_ids:
                        cnt_records_with_ddc_from_gnd += 1

                        # TODO build linked data: hbz_id with its ddc classes

                    hbz_id = ''
                    swd_ids = []

                else:

                    if line.startswith('0010.'):

                        hbz_id = line.strip().split(':')[1]

                    if line.startswith('0902') or line.startswith('0907') or line.startswith('0912') or line.startswith('0917') \
                            or line.startswith('0922') or line.startswith('0927') or line.startswith('0932') or line.startswith('0937') \
                            or line.startswith('0942') or line.startswith('0947'):

                        value = line.strip().replace('IDN: ', '').split(':')[1]

                        if value in sunrise_gnd_mapping.keys() and sunrise_gnd_mapping[value] in gnd_swd_to_ddc.keys():

                            cnt_ddc_classes_from_gnd += 1

                            if gnd_swd_to_ddc[sunrise_gnd_mapping[value]] not in swd_ids:

                                swd_ids.append(gnd_swd_to_ddc[sunrise_gnd_mapping[value]])

    print('cnt_records_with_ddc_from_gnd: %s' % cnt_records_with_ddc_from_gnd)
    print('cnt_ddc_classes_from_gnd: %s' % cnt_ddc_classes_from_gnd)


if __name__ == '__main__':

    # prepare Sunrise data for building linked data
    read_sunrise_data()

    # get coli-conc data for gnd to ddc mappings
    get_ddc_for_gnd()

    # build bibliographic entities for ubdo
    build_linked_data()
