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
import locale
import timeit

from analyse_rvk_in_collections_sparql import GET_ALL_SHELFMARK_LABELS, GET_ALL_TITLES_IN_SHELFMARKS, \
    GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE, GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE_WITH_RVK, \
    GET_ALL_ISSUED_TITLES_OF_SHELFMARK, GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE, \
    GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE_WITH_RVK
from util_sparql_client import sparql_query


START_ISSUED = 2010
END_ISSUED = 2019


def _rvk_in_collections(branch='0'):
    locale.setlocale(locale.LC_ALL, '')

    all_titles = sparql_query(query=GET_ALL_TITLES_IN_SHELFMARKS % branch)
    all_titles_in_bundles = sparql_query(query=GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE % branch)
    all_titles_in_bundles_with_rvk = sparql_query(query=GET_ALL_TITLES_IN_SHELFMARKS_IN_BUNDLE_WITH_RVK % branch)

    results = ['collection\ttitles\tbundles\tno bundle\tquota bundles\trvk\tno rvk\tquota rvk']

    for entry in all_titles:
        shelfmark = entry['label']['value']
        if 'EGM' not in shelfmark and 'EGZ' not in shelfmark:
            cnt = int(entry['cnt']['value'])
            bundles = 0
            for entry1 in all_titles_in_bundles:
                if entry1['label']['value'] == shelfmark:
                    bundles = int(entry1['cnt']['value'])
                    break
            rvk = 0
            for entry1 in all_titles_in_bundles_with_rvk:
                if entry1['label']['value'] == shelfmark:
                    rvk = int(entry1['cnt']['value'])
                    break

            diff_bundles = cnt - bundles
            diff_rvk = cnt - rvk

            quota_bundles = 0
            if bundles > 0:
                quota_bundles = bundles / cnt * 100

            quota_rvk = 0
            if rvk > 0:
                quota_rvk = rvk / cnt * 100

            results.append('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                shelfmark, cnt, bundles, diff_bundles, locale.format("%.2f", quota_bundles), rvk, diff_rvk, locale.format("%.2f", quota_rvk)
            ))

    return results


def _rvk_in_issued_by_shelfmark(branch='0'):
    locale.setlocale(locale.LC_ALL, '')

    SHELF_MARKS = sparql_query(query=GET_ALL_SHELFMARK_LABELS % branch)

    results = ['shelfmark\tissued\ttitles\tbundles\tno bundle\tquota bundles\trvk\tno rvk\tquota rvk']

    for item in SHELF_MARKS:
        shelfmark = item['label']['value']

        all_titles = sparql_query(query=GET_ALL_ISSUED_TITLES_OF_SHELFMARK % (branch, shelfmark, START_ISSUED, END_ISSUED))
        all_titles_in_bundles = sparql_query(query=GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE % (branch, shelfmark, START_ISSUED, END_ISSUED))
        all_titles_in_bundles_with_rvk = sparql_query(query=GET_ALL_ISSUED_TITLES_OF_SHELFMARK_IN_BUNDLE_WITH_RVK % (branch, shelfmark, START_ISSUED, END_ISSUED))

        for entry in all_titles:
            try:
                issued = entry['issued']['value']
                cnt = int(entry['cnt']['value'])

                bundles = 0
                for entry1 in all_titles_in_bundles:
                    if entry1['issued']['value'] == issued:
                        bundles = int(entry1['cnt']['value'])
                        break

                rvk = 0
                for entry1 in all_titles_in_bundles_with_rvk:
                    if entry1['issued']['value'] == issued:
                        rvk = int(entry1['cnt']['value'])
                        break

                diff_bundles = cnt - bundles
                diff_rvk = cnt - rvk

                quota_bundles = 0
                if bundles > 0:
                    quota_bundles = bundles / cnt * 100

                quota_rvk = 0
                if rvk > 0:
                    quota_rvk = rvk / cnt * 100

                results.append('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %(
                    shelfmark, issued, cnt, bundles, diff_bundles, locale.format("%.2f", quota_bundles), rvk, diff_rvk, locale.format("%.2f", quota_rvk)
                ))
            except:
                print(entry)

    return results


if __name__ == '__main__':

    start = timeit.default_timer()

    branches = ['0', '9', '10', '12']

    for branch in branches:
        results = _rvk_in_collections(branch=branch)
        with open('data/analyse/rvk_in_signaturgruppen_DE-290-%s.tsv' % branch, 'w') as thedata:
            for entry in results:
                thedata.write('%s\n' % entry)

        results = _rvk_in_issued_by_shelfmark(branch=branch)
        with open('data/analyse/rvk_in_signaturgruppen_per_erschjahr_DE-290-%s.tsv' % branch, 'w') as thedata:
            for entry in results:
                thedata.write('%s\n' % entry)

    stop = timeit.default_timer()
    duration = stop - start
    print('duration RVK data analysis for UB Dortmund collections: %s' % duration)
