#!/bin/bash

cd "$(dirname "$0")";

if [ -d "fxpixiv" ] 
then
    source fxpixiv/bin/activate
else
    curl "https://bootstrap.pypa.io/get-pip.py" --output get-pip.py
    python3.9 get-pip.py
    python3.9 -m pip install -U virtualenv
    python3.9 -m virtualenv fxpixiv
    source fxpixiv/bin/activate
fi

python3.9 -m pip install -U requests flask pixivpy selenium

python3.9 main.py
