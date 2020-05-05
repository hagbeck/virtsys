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
# * hbz-ID
#  * 0807:g, falls es sich um eine E-Resource handelt
#  * 0036 = p,z
#  * 0425 (issued)
#  * 1204 (Signatur)

sunrise_data_dir = 'data/sunrise/2018-12-07'
manifestation_set = 'data/ubdo/ubdo_manifestation_set.ttl'


def read_sunrise_data():

    with open(manifestation_set, 'w') as manifestation_set_data:

        manifestation_set_data.write('@prefix dct: <http://purl.org/dc/terms/> .\n')

        with open('%s/unload.TIT' % sunrise_data_dir, 'r') as title_data:

            hbz_id = ''

            for line in title_data:

                if line.startswith('9999:'):

                    if hbz_id:
                        manifestation_set_data.write('<http://lobid.org/resources/%s> a <http://erlangen-crm.org/efrbroo/F3_Manifestation_Product_Type> .\n' % hbz_id)
                        manifestation_set_data.write('<http://lobid.org/resources/%s> dct:isReferencedBy <https://www.ub.tu-dortmund.de/katalog> .\n' % hbz_id)

                    hbz_id = ''
                else:

                    if line.startswith('0010.001:'):

                        hbz_id = line.strip().replace('0010.001:', '')

        print('ubdo_manifestation_set.ttl ready.')


if __name__ == '__main__':

    read_sunrise_data()
