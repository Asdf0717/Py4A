#! /usr/bin/env python3

import os.path
import glob
import sqlite3
import json

def main():
    styles_glob = os.path.expanduser('~/.mozilla/firefox/*.default/stylish.sqlite')
    styles_path = glob.glob(styles_glob)[0]

    conn = sqlite3.connect(styles_path)
    c = conn.cursor()
    styles = []
    for row in c.execute('SELECT * FROM styles'):
        _id, url, updUrl, md5Url, name, code, enabled, origCode, idUrl, bg, origMd5 = row
        styles.append({
            'method': 'saveStyle',
            'name': name,
            'enabled': bool(enabled),
            'sections': [{
                'code': code,
            }],
            'updateUrl': updUrl or None,
            'md5Url': md5Url or None,
            'url': url or None,
            'originalMd5': origMd5 or None,
            'id': _id,
        })
    conn.close()

    with open('stylus.json', 'w') as stylus:
        json.dump(styles, stylus)

if __name__ == '__main__':
    main()
