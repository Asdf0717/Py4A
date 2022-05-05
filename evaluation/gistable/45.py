#!/usr/bin/python

import os, sys, re, argparse

parser = argparse.ArgumentParser(description='Fix PHP file endings')
parser.add_argument('directory', metavar='d', help='The path to the PHP sources')

args = parser.parse_args()

path = args.directory
php_dir = os.listdir(path)

regex = re.compile("\?>",re.MULTILINE)

for root, dirs, files in os.walk(path):
    for name in files:
        file_name = os.path.join(root, name)
        file_content = ""
        with open(file_name, "r") as f:
            file_content = f.read()

        occurrences = regex.findall(file_content)
        if len(occurrences) is 1:
            file_content = file_content.replace("?>", "", 1).rstrip() + "\n"

            with open(file_name, "w") as f:
                file_content = f.write(file_content)

            print("Fixed file: " + file_name)
