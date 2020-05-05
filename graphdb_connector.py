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
from urllib.parse import unquote_plus

import requests


def get_request(endpoint='', function=''):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if function:
        function = '/' + function

    response = requests.get('%s%s' % (endpoint, function), headers={'accept': 'application/json'})
    status = response.status_code
    if status == 200:

       return response.content.decode("utf-8")

    else:
        raise ImportError('Getting data failed: %s - %s' % (status, response.content.decode("utf-8")))


def post_request(endpoint='', function='', data=None):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if not data:
        raise ValueError('data undefined!')

    if function:
        function = '/' + function

    response = requests.post('%s%s' % (endpoint, function), headers={'content-type': 'application/json'}, data=data)
    status = response.status_code
    if 200 <= status <= 299:

       return response.content.decode("utf-8")

    else:
        raise ImportError('Getting data failed: %s - %s' % (status, response.content.decode("utf-8")))


def delete_request(endpoint='', function='', param_string=''):

    if not endpoint:
        raise ValueError('endpoint undefined!')

    if function:
        function = '/' + function

    if param_string and not param_string.startswith('?'):
        param_string = '?' + param_string

    response = requests.delete('%s%s%s' % (endpoint, function, param_string), headers={'accept': 'text/plain'})
    status = response.status_code
    if 200 <= status <= 299:

       return 'Deleted: %s - %s' % (unquote_plus(param_string.split('=')[1]), response.content.decode("utf-8"))

    else:
        raise ImportError('Deleting data failed: %s - %s' % (status, response.content.decode("utf-8")))


