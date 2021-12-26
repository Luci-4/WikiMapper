from bs4 import BeautifulSoup
from time import sleep
from graph import createGraph
import requests
import re
import sqlite3
import sys
import threading


firstPage = r'https://en.wikipedia.org/wiki/Wroc%C5%82aw'


relations = []
queue = [firstPage]

spiderPopulation = 30
depth = 15


class Crawler:

    visited = set()

    def pageLoader(self, link: str):
        """Loads and parses into usefull format given page """

        r = requests.get(link).text
        soup = BeautifulSoup(r, 'html.parser')
        self.soup = soup
        # All links here will be in correct format
        self.parent = self.formatter(link)

    def formatter(self, OtherLink: str):
        """
        Cut out article name from link name
        Check if page is interesting one
        """

        garbage = [
            'Special:',
            'Talk:',
            'Portal:',
            'Wikipedia:',
            'Help:',
            'Cookie_statement',
            'File:',
            'Author:',
            'Privacy_policy',
            'Cookie_statement',
            'Terms_of_Use',
            'Main_Page',
            'Category:'

        ]

        if title := re.search(r'\/wiki\/', OtherLink):
            OtherLink = OtherLink[title.end()::]

            for unwanted in garbage:
                if re.search(unwanted, OtherLink):
                    OtherLink = False
                    break
        else:
            OtherLink = False

        return OtherLink

    def visitChecker(self):
        """Check if site was previously visited"""
        if self.parent in self.visited:
            return False
        else:
            self.visited.add(self.parent)

        return True

    def relate(self):
        """Create relation between base link and links retrived from site"""

        temp_visited = set()
        temp_visited.add(self.parent)

        for a in self.soup.find_all('a', href=True):

            if child := self.formatter(a['href']):
                if child not in temp_visited:
                    temp_visited.add(child)
                    queue.append('https://en.wikipedia.org/wiki/' + child)
                    relations.append([self.parent, child, self.jump])

    def live(self, link: str):
        """All functionality here"""
        self.pageLoader(link)
        self.jump = jump

        if self.parent and self.visitChecker():
            self.relate()


def database():
    """Save to database"""

    con = sqlite3.connect('wikiProject.db')
    cur = con.cursor()
    cur.execute('''Create TABLE IF NOT EXISTS relations
        (Parent text,
        Child text,
    )''')

    for relation in relations:
        cur.execute('insert into relations values (?,?)',
                    (relation[0], relation[1]))

    con.commit()
    con.close()
    print("\nSaved to database")


def progress(count: int, total: int, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def clutter(spider, thisDepth, queen=False):
    for current in range(thisDepth):
        spider.live(queue.pop(0))
        if queen:
            progress(current, thisDepth)


if __name__ == '__main__':

    spiders = []

    for _ in range(spiderPopulation):
        spiders.append(Crawler())

    print("Processing...")
    # TO FIX: DEPENDENCY ON LENGTH OF QUEUE
    queenSpider = Crawler()
    clutter(queenSpider, 2)

    for spider in spiders:
        x = threading.Thread(target=clutter, args=(spider, depth,))
        x.start()

    clutter(queenSpider, depth, True)

    while threading.active_count() != 1:
        sleep(1)
    database()
    print('\nFinished')
    createGraph()
