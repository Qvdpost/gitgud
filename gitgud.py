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
    print("Gitting Gud")
    repo = git.Repo(os.getcwd())
    assert not repo.bare

    if repo.remotes.origin:
        origin = repo.remotes.origin
    else:
        print("Setting up remote.")
        origin = repo.create_remote('origin', repo.remotes.origin.url)
        assert origin.exists()
        assert origin == repo.remotes.origin == repo.remotes['origin']

    print("Fetching and pulling.")
    origin.fetch()
    origin.pull()

    diffs = repo.index.diff(None)
    if not diffs and len(repo.untracked_files) == 0:
        exit("No changes to add... git gud man.")

    if len(diffs) > 0:
        print("Changed files:")
        for diff_added in diffs:
            print(f'\t{diff_added.a_path}')
            if diff_added.b_mode:
                repo.index.add([diff_added.a_path])
            else:
                repo.index.remove([diff_added.a_path])

    if len(repo.untracked_files) > 0:
        print("New files:")
        for file in repo.untracked_files:
            print(f'\t{file}')
            repo.index.add([file])

    print("Committing")
    quotes = construct_quotes()
    commit_message = f'{quotes[0][0]} - {quotes[0][1]}'
    repo.index.commit(commit_message)

    print("Pushing")
    origin.push()

    print("Gotten Gud")

if __name__ == '__main__':
    main()
