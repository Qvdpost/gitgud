#! /usr/bin/env python3

from requests_futures.sessions import FuturesSession
from html.parser import HTMLParser
import re
import json
import sys
import git
import os


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def get_quotes(num=10):
    futures = []
    url = "http://www.quotedb.com/quote/quote.php?action=random_quote"
    session = FuturesSession()
    for i in range(1, num+1):
        futures.append(session.get(url))
    results = []
    for f in futures:
        res = f.result()
        results.append(res.content)
    return results


def extract_quote(text):
    text = text.decode(errors='ignore')
    matches = re.findall(r'document.write\(\'(.*)\'\)', str(text))
    if not matches or len(matches) != 2:
        print("Error: matches = ", matches)
        return None
    quote = strip_tags(matches[0])
    author = re.search(r'More quotes from (.*)', strip_tags(matches[1]))
    if author:
        author = author.group(1)
    return (quote, author)


def write_to_json_file(tups, filename="quotes.json"):
    data = []
    for quote, author in tups:
        data.append({'quote': quote, 'author': author})
    json_str = json.dumps(data)
    with open(filename, 'w') as f:
        f.write(json_str)
    return filename

def construct_quotes():
    if len(sys.argv) == 2:
        num = int(sys.argv[1])
    else:
        num = 1
    results = get_quotes(num=num)
    tups = []
    for r in results:
        tup = extract_quote(r)
        if tup is not None:
            try:
                q = str(tup[0])
                a = str(tup[1])
                tups.append(tup)
            except Exception as e:
                pass
    return tups

def main():
    repo = git.Repo(os.getcwd())
    assert not repo.bare
    assert not repo.is_dirty()
    print(f'Adding: {repo.untracked_files}')
    for file in repo.untracked_files:
        repo.index.add([file])
    exit(1)
    quotes = construct_quotes()
    commit_message = f'{quotes[0][0]} - {quotes[0][1]}'
    repo.index.commit(commit_message)

if __name__ == '__main__':
    main()
