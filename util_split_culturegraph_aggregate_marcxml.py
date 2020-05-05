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
import os
from os import listdir
from os.path import isfile, join
import timeit

input_dir = '/export/virtuelle_systematik/data/culture_graph/aggregate_marcxml/'
input_file = 'aggregate.marcxml'

output_dir = '/export/virtuelle_systematik/data/culture_graph/aggregate_marcxml/splitted/'
output_file = 'aggregate.%s.marcxml'


def cleanup_dir(data_dir=''):

    if data_dir:
        results_files = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]
        print('%s records to delete ...' % len(results_files))
        if results_files:
            for file in results_files:
                os.remove(join(data_dir, file))


if __name__ == '__main__':

    print('begin cleanup output_dir ...')
    cleanup_dir(data_dir=output_dir)
    print('cleanup output_dir finished.')

    record_cnt = 0

    record_limit = 5000
    file_cnt = 1

    file_content_prefix = '<?xml version="1.0" encoding="UTF-8"?>\n<marc:collection xmlns:marc="http://www.loc.gov/MARC21/slim">\n'

    start = timeit.default_timer()

    with open("%s%s" % (input_dir, input_file), "r") as ins:

        thedata = ''
        record = ''

        for line in ins:

            if '<marc:record' in line and record_cnt > 0:

                thedata += record
                record_cnt += 1

                if record_cnt % record_limit == 0:
                    # write thedata
                    with open('%s%s' % (output_dir, output_file % file_cnt), 'w') as data:
                        if record_cnt > 1:
                            data.write(file_content_prefix)
                        data.write(thedata)
                        data.write('</marc:collection>')

                    # reset variables
                    file_cnt += 1
                    thedata = ''

                    if file_cnt % 100 == 0:
                        print('... %s files written.' % file_cnt)

                # reset the the record
                record = '%s\n' % line.strip()

            else:
                if '<marc:record' in line and record_cnt == 0:
                    record_cnt += 1

                record += '%s\n' % line.strip()

        thedata += record
        record_cnt += 1

        # write thedata
        with open('%s%s' % (output_dir, output_file % file_cnt), 'w') as data:
            data.write(file_content_prefix)
            data.write(thedata)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration splitting the data to smaller files of %s: %s\n' % (record_limit, duration))

    print('records read: %s' % record_cnt)
    print('files written: %s' % file_cnt)
