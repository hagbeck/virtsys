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

# TODO
# TODO - hole alle BVB-IDs aus CultureGraph
# TODO - hole für jede BVB-ID den LD-Record aus B3kat
# TODO - prüfe, ob darin eine OCN enthalten ist
# TODO - hole für alle OCN die Daten aus Worldcat
# TODO - für jeden Worldcat-Datensatz hole die DDC-Notationen und die exampleOfWork und workExample (<> isbn) Daten heraus
# TODO - für alle OCNs aus workExample hole die DDC-Notationen
