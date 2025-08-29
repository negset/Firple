#!/bin/bash

cat /etc/lsb-release | sed -nr 's/^DISTRIB_DESCRIPTION="(.*)"$/\1/p'
python3 --version
fontforge -version 2>&1 | sed -nr '/^fontforge .*$/p'
fonttools help 2>&1 | head -1
ttfautohint --version | head -1
