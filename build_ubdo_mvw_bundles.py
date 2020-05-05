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

import simplejson as json

import config_ubdo as config

# read mapped_ids_file to mapped_ids_data
with open(config.MVW_BUNDLES_FILE, 'r') as json_data:

    mvw_cluster_data = json.load(json_data)

if mvw_cluster_data:

    with open(config.COMPLEX_WORKS_TTL_DATA, 'w') as rdfdata:

        for key in mvw_cluster_data.keys():

            if mvw_cluster_data[key]:

                for item in mvw_cluster_data[key]:
                    rdfdata.write(
                        '<http://lobid.org/resources/%s> <http://purl.org/dc/terms/hasPart> <http://lobid.org/resources/%s> .\n' % (key, item))
                    rdfdata.write(
                        '<http://lobid.org/resources/%s> <http://purl.org/dc/terms/isPartOf> <http://lobid.org/resources/%s> .\n' % (item, key))
