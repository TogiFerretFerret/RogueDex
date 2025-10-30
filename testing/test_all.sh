#!/bin/bash
cd ..
python3 -m unittest discover testing/battledex_engine
python3 -m unittest discover testing/picoNet
python3 -m unittest discover testing/rotomdex
