#!/bin/bash

cd "$(dirname "$0")";

if [ -d "fxpixiv" ] 
then
    source fxpixiv/bin/activate
else
    curl "https://bootstrap.pypa.io/get-pip.py" --output get-pip.py
    python3 get-pip.py
    python3 -m pip install -U virtualenv
    python3 -m virtualenv fxpixiv
    source fxpixiv/bin/activate
fi

python3 -m pip install -U requests flask pixivpy selenium gunicorn

python3 main.py
