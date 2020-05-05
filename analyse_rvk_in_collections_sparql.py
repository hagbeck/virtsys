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
GET_ALL_SHELFMARK_LABELS = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
select distinct ?label where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative ?label .
}
order by ?label
'''

GET_ALL_TITLES_IN_SHELFMARKS = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
select ?label (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?item dct:isPartOf ?collection .
    ?collection dct:alternative ?label .
    ?item efrbroo:R7_is_example_of ?work .
}
group by ?collection ?label
order by ?label
'''

GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
select ?label (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative ?label .
    ?item dct:isPartOf ?collection .
    ?item efrbroo:R7_is_example_of ?work .
    FILTER EXISTS { ?work <http://purl.org/net/bundle#encapsulated_in> ?bundle . }
}
group by ?collection ?label
order by ?label
'''

GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE_WITH_RVK = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
select ?label (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative ?label .
    ?item dct:isPartOf ?collection .
    ?item efrbroo:R7_is_example_of ?work .
    ?work <http://purl.org/net/bundle#encapsulated_in> ?bundle .
    FILTER EXISTS { ?bundle dct:subject ?rvk . }
}
group by ?collection ?label
order by ?label
'''

GET_ALL_ISSUED_TITLES_OF_SHELFMARK = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select ?issued (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative "%s" .
    ?item dct:isPartOf ?collection .
    ?item efrbroo:R7_is_example_of ?work .
    ?work dct:issued ?issued .
    FILTER (xsd:integer(?issued) >= %s) .
    FILTER (xsd:integer(?issued) <= %s) .
}
group by ?collection ?issued
order by desc(?issued)
'''

GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select ?issued (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative "%s" .
    ?item dct:isPartOf ?collection .
    ?item efrbroo:R7_is_example_of ?work .
    ?work dct:issued ?issued .
    FILTER (xsd:integer(?issued) >= %s) .
    FILTER (xsd:integer(?issued) <= %s) .
    FILTER EXISTS { ?work <http://purl.org/net/bundle#encapsulated_in> ?bundle . }
}
group by ?collection ?issued
order by desc(?issued)
'''

GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE_WITH_RVK = '''
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select ?issued (COUNT(distinct ?work) AS ?cnt) where {
    <http://data.ub.tu-dortmund.de/resource/collection:DE-290-%s> dct:hasPart ?collection .    
    ?collection rdf:type dct:Collection .
    ?collection dct:alternative "%s" .
    ?item dct:isPartOf ?collection .
    ?item efrbroo:R7_is_example_of ?work .
    ?work dct:issued ?issued .
    FILTER (xsd:integer(?issued) >= %s) .
    FILTER (xsd:integer(?issued) <= %s) .
    ?work <http://purl.org/net/bundle#encapsulated_in> ?bundle .
    FILTER EXISTS { ?bundle dct:subject ?rvk . }
}
group by ?collection ?issued
order by desc(?issued)
'''

