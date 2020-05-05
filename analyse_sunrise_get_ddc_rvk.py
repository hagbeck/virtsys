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
# * 0010: hbz-ID
# * 1701: RVK
# * 1705: DDC
# * 1716: DNB-SG
# * 0702: DDC

sunrise_data_dir = 'data/sunrise/2018-12-07'
metadata_file = '%s/subjects.tsv' % sunrise_data_dir


def read_sunrise_data():

    with open(metadata_file, 'w') as title_subjects:

        with open('%s/unload.TIT' % sunrise_data_dir, 'r') as title_data:

            record_id = ''
            record_rvk = []
            record_ddc = []
            record_dnb_sg = []
            record_ddc_alt = []

            record_rvk_cnt = 0
            record_ddc_cnt = 0
            record_ddc_sg_cnt = 0

            rvk_notations = []
            ddc_classes = []
            dnb_subjects = []
            ddc_alt_classes = []

            rvk_notations_cnt = 0
            ddc_classes_cnt = 0
            dnb_subjects_cnt = 0
            ddc_alt_classes_cnt = 0

            eki_bvb_cnt = 0
            eki_dnb_cnt = 0
            eki_gbv_cnt = 0
            eki_swb_cnt = 0
            eki_hbz_cnt = 0
            eki_other_cnt = 0

            for line in title_data:

                if line.startswith('9999:'):

                    if record_id and (record_ddc or record_rvk or record_ddc_alt or record_dnb_sg):

                        if record_rvk:
                            record_rvk_cnt += 1

                        if record_ddc or record_ddc_alt:
                            record_ddc_cnt += 1

                        if record_dnb_sg:
                            record_ddc_sg_cnt += 1

                        title_subjects.write('%s\t%s\t%s\t%s\t%s\n' % (record_id, record_rvk, record_ddc, record_dnb_sg, record_dnb_sg))

                    record_id = ''
                    record_rvk = []
                    record_ddc = []
                    record_dnb_sg = []
                    record_ddc_alt = []
                else:

                    if line.startswith('0010.001:'):

                        record_id = line.strip().replace('0010.001:', '')

                    elif line.startswith('1024'):

                        value = line.strip().split(':')[1]

                        if value.startswith('BVB'):
                            eki_bvb_cnt += 1
                        elif value.startswith('DNB'):
                            eki_dnb_cnt += 1
                        elif value.startswith('GBV'):
                            eki_gbv_cnt += 1
                        elif value.startswith('SWB'):
                            eki_swb_cnt += 1
                        elif value.startswith('HBZ'):
                            eki_hbz_cnt += 1
                        else:
                            eki_other_cnt += 1

                    elif line.startswith('1701.'):

                        rvk_notations_cnt += 1

                        notation = line.strip().split(':')[1]

                        if notation not in record_rvk:
                            record_rvk.append(notation)

                        if notation not in rvk_notations:
                            rvk_notations.append(notation)

                    elif line.startswith('1705.'):

                        ddc_classes_cnt += 1

                        notation = line.strip().split(':')[1]

                        if notation not in record_ddc:
                            record_ddc.append(notation)

                        if notation not in ddc_classes:
                            ddc_classes.append(notation)

                    elif line.startswith('1716.'):

                        dnb_subjects_cnt += 1

                        notation = line.strip().split(':')[1]

                        if notation not in record_dnb_sg:
                            record_dnb_sg.append(notation)

                        if notation not in dnb_subjects:
                            dnb_subjects.append(notation)

                    elif line.startswith('0702.'):

                        ddc_alt_classes_cnt += 1

                        notation = line.strip().split(':')[1]

                        if notation not in record_ddc_alt:
                            record_ddc_alt.append(notation)

                        if notation not in ddc_alt_classes:
                            ddc_alt_classes.append(notation)

    print('getting data ready.')
    print('rvk_notations: %s' %rvk_notations_cnt)
    print('ddc_classes: %s' % ddc_classes_cnt)
    print('dnb_subjects: %s' % dnb_subjects_cnt)
    print('ddc_alt_classes: %s' % ddc_alt_classes_cnt)

    print('distinct rvk_notations: %s' % len(rvk_notations))
    print('distinct ddc_classes: %s' % len(ddc_classes))
    print('distinct dnb_subjects: %s' % len(dnb_subjects))
    print('distinct ddc_alt_classes: %s' % len(ddc_alt_classes))

    print('manifestations with RVK: %s' % record_rvk_cnt)
    print('manifestations with DDC: %s' % record_ddc_cnt)
    print('manifestations with DNB-SG: %s' % record_ddc_sg_cnt)

    print('EKI HBZ: %s' % eki_hbz_cnt)
    print('EKI BVB: %s' % eki_bvb_cnt)
    print('EKI DNB: %s' % eki_dnb_cnt)
    print('EKI SWB: %s' % eki_swb_cnt)
    print('EKI GBV: %s' % eki_gbv_cnt)
    print('EKI other: %s' % eki_other_cnt)


if __name__ == '__main__':

    # prepare Sunrise data for building linked data
    read_sunrise_data()

    # build bibliographic entities for ubdo
    # build_linked_data()
