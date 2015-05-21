""" Sanitize fixtures

    Removes environment variables from fixtures and replaces them with constants...

"""
import os
import fileinput
import re

TEST_IP = "127.0.0.1"
TEST_USER = "admin"
TEST_PASS = "adminadmin"

dir = os.path.dirname(__file__)
fixtures_dir = os.path.join(dir, '../fixtures')

for root, dirnames, filenames, in os.walk(fixtures_dir):
    for filename in filenames:
        file_path = os.path.join(root,filename)

        with open(file_path, "r") as sources:
            lines = sources.readlines()
        with open(file_path, "w") as sources:
            for line in lines:
                sanitized_line = line

                if os.environ['PYBSN_HOST']:
                    sanitized_line = re.sub(os.environ['PYBSN_HOST'], TEST_IP, sanitized_line)
                if os.environ['PYBSN_USER']: 
                    sanitized_line = re.sub(os.environ['PYBSN_USER'], TEST_USER, sanitized_line)
                if os.environ['PYBSN_PASS']:
                    sanitized_line = re.sub(os.environ['PYBSN_PASS'], TEST_PASS, sanitized_line)

                sources.write(sanitized_line)