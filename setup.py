# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from setuptools import setup, find_packages


def get_long_description():
    long_description = open('README.md').read()
    try:
        import subprocess
        import pandoc

        process = subprocess.Popen(
            ['which pandoc'],
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True)

        pandoc_path = process.communicate()[0]
        pandoc_path = pandoc_path.strip('\n')

        pandoc.core.PANDOC_PATH = pandoc_path

        doc = pandoc.Document()
        doc.markdown = long_description
        long_description = doc.rst
    except:
        print("Could not find pandoc or convert properly")
        print("  make sure you have pandoc (system) and pyandoc (python module) installed")

    return long_description

setup(
  name='epoxy',
  version='1.0',
  description='Inversion of Control Framework for Python',
  long_description=get_long_description(),
  url='https://github.com/etherios/epoxy',
  author="Paul Osborne",
  author_email="paul.osborne@etherios.com",
  packages=find_packages(),
  install_requires=open('requirements.txt').read().split(),
  classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
      "Programming Language :: Python :: 2.7",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.3",
      "Programming Language :: Python :: 3.4",
      "Topic :: Software Development :: Libraries",
      "Topic :: Software Development :: Libraries :: Application Frameworks",
      "Operating System :: OS Independent",
  ],
)
