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


def __normalize_rvk_data(data=''):

    normalized_data = ''

    normalized_data = data.upper().replace('/', '')

    RVK_CLASS = re.compile('[A-Z]{2}\s\d{2,6}')
    RVK_CLASS_wo_space = re.compile('[A-Z]{2}\d{2,6}')
    RVK_CLASS_Cutter = re.compile('[A-Z]{2}\s\d{2,6}\s[A-Z]{1}\d{1,6}')

    print(normalized_data)

    if not RVK_CLASS.match(normalized_data) and not RVK_CLASS_Cutter.match(normalized_data):
        print('\tnot valid')
        if RVK_CLASS_wo_space.match(normalized_data):
            # print('\tnow valid')
            normalized_data = normalized_data[0:2] + ' ' + normalized_data[2:]
        else:
            # print('\tstill not valid')
            normalized_data = ''

    elif RVK_CLASS_Cutter.match(normalized_data):
        print('\t-> Cutter')
        normalized_data = ' '.join(normalized_data.split(' ')[0:2])

    return normalized_data


if __name__ == '__main__':

    print(__normalize_rvk_data(data='ST 250'))
    print('')
    print(__normalize_rvk_data(data='ST 250 J35'))
    print('')
    print(__normalize_rvk_data(data='ST 250 J2'))
    print('')
    print(__normalize_rvk_data(data='ST 250 J352'))
