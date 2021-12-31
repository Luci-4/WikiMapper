from bs4 import BeautifulSoup
from graph import createGraph
from time import sleep
import requests
import re
import sqlite3
import sys
import threading
import os

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

    def relate(self, queue, relations):
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

    def live(self, link: str, queue, relations):
        """All functionality here"""
        self.pageLoader(link)
        if self.parent and self.visitChecker():
            self.relate(queue, relations)

class App:
    relations = []
        
    def main(self) -> None: 
        self.userInput()
        self.spiders = []
        print("Processing...")
        queenSpider = Crawler()
        self.walk(queenSpider, self.depth)
        if self.threads:
            for _ in range(len(self.queue)):
                self.spiders.append(Crawler())

            for spider in self.spiders:
                x = threading.Thread(target=self.walk, args=(spider, self.depth-1,))
                x.start()

        self.walk(queenSpider, self.depth-1, True)

        while threading.active_count() != 1:
            sleep(1)

        self.database()
        createGraph(self.path)
        
    def userInput(self):
        while len(path := input('Name:')) == 0:
            print('Error: Name can\'t be empty!')
        self.path = path

        while len(firstPage := input('Link:')) == 0 or not re.search(r'https://en\.wikipedia\.org/wiki/', firstPage):
            print('Error: Given link is not valid!')
        self.firstPage = firstPage

        while not(depth := input('Depth:').isdigit()):
            print('Error: depth must be integer!')
        self.depth = depth

        while (threads := input('Multithreading (yes/no):') not in ('yes', 'no')):
            print('Error')

        if threads == 'yes':
            self.threads = True
        else:
            self.threads = False

        if not os.path.exists(self.path):
            os.mkdir(self.path)

        self.queue = [self.firstPage]
    def database(self):
        """Save to database"""

        con = sqlite3.connect(os.path.join(self.path, f'{self.path}.db'))
        cur = con.cursor()
        cur.execute('''Create TABLE IF NOT EXISTS relations
            (Parent text,
            Child text
        )''')

        for relation in self.relations:
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


    def walk(self, spider, depth: int, queen=False):
        for current in range(depth):
            spider.live(self.queue.pop(0), self.queue, self.relations)
            if queen:
                self.progressBar(current, depth)

if __name__ == '__main__':
    app = App()
    app.main()

