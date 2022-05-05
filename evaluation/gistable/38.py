from BeautifulSoup import BeautifulSoup as Soup
import urllib

raw_page = urllib.urlopen('http://www.sfrandonneurs.org/home.htm')
soup = Soup(raw_page)


class MarkdownTable:

    @staticmethod
    def table_columns(headers=[]):
        to_ret = "|"
        to_ret += "|".join(headers)
        to_ret += "|"
        to_ret += "\n" + MarkdownTable.header(len(headers))
        return to_ret

    @staticmethod
    def header(col_num):
        return "" + "|---" * col_num + "|\n"

    @staticmethod
    def table_row(row):
        return "|" + "|".join(row) + "|"


class SFRRiders:
    def __init__(self):
        self.r_table = soup.find('table', {'id': 'registeredRiders'})

    def __str__(self):
        to_ret = MarkdownTable.table_columns(self.headers)
        to_ret += "\n".join([MarkdownTable.table_row(row) for row in self.body])
        return to_ret

    @property
    def headers(self):
        return [th.text for th in self.r_table.find('thead').findAll('th')]

    @property
    def body(self):
        return map(self._get_tds, self.r_table.find('tbody').findAll('tr'))

    def to_string(self):
        return self.__str__()

    def _get_tds(self, trow):
        return [item.text for item in trow]
