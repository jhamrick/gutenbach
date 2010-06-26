#!/bin/bash
CURRENT=virtualenv-1.3.2
wget "http://pypi.python.org/packages/source/v/virtualenv/$CURRENT.tar.gz"
tar xzf "$CURRENT.tar.gz"
python "$CURRENT/virtualenv.py" --no-site-packages tg2env
rm "$CURRENT.tar.gz"
rm -rf "$CURRENT"
source tg2env/bin/activate
source virtualenv-create
