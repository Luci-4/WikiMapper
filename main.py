from bs4 import BeautifulSoup
from graph import createGraph
from time import sleep
import requests
import re
import sqlite3
import sys
import threading
import os


relations = []


def userInput():
    global path
    global firstPage
    global depth
    global queue
    global threads

    while len(path := input('Name:')) == 0:
        print('Error: Name can\'t be empty!')

    while len(firstPage := input('Link:')) == 0 or not re.search(r'https://en\.wikipedia\.org/wiki/', firstPage):
        print('Error: Given link is not valid!')

    while not(depth := input('Depth:').isdigit()):
        print('Error: depth must be integer!')

    while (threads := input('Multithreading (yes/no):') not in ('yes', 'no')):
        print('Error')
    if threads == 'yes':
        threads = True
    else:
        threads = False

    if not os.path.exists(path):
        os.mkdir(path)

    queue = [firstPage]


def database():
    """Save to database"""

    con = sqlite3.connect(os.path.join(path, f'{path}.db'))
    cur = con.cursor()
    cur.execute('''Create TABLE IF NOT EXISTS relations
        (Parent text,
        Child text
    )''')

    for relation in relations:
        cur.execute('insert into relations values (?,?)',
                    (relation[0], relation[1]))

    con.commit()
    con.close()
    print("\nSaved to database")


def progressBar(count: int, total: int, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def walk(spider, thisDepth: int, queen=False):
    for current in range(thisDepth):
        spider.live(queue.pop(0))
        if queen:
            progressBar(current, thisDepth)


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
        Cut out article name from link 
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
        print(len(temp_visited) == 1)
        for a in self.soup.find_all('a', href=True):

            if child := self.formatter(a['href']):
                if child not in temp_visited:
                    temp_visited.add(child)
                    queue.append('https://en.wikipedia.org/wiki/' + child)
                    relations.append([self.parent, child])

    def live(self, link: str):
        """All functionality here"""
        self.pageLoader(link)
        if self.parent and self.visitChecker():
            self.relate()


if __name__ == '__main__':
    userInput()

    spiders = []
    print("Processing...")
    queenSpider = Crawler()
    walk(queenSpider, depth)
    if threads:
        for _ in range(len(queue)):
            spiders.append(Crawler())

        for spider in spiders:
            x = threading.Thread(target=walk, args=(spider, depth-1,))
            x.start()

    walk(queenSpider, depth-1, True)

    while threading.active_count() != 1:
        sleep(1)

    database()
    createGraph(path)
