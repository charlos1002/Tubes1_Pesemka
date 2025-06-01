#!/bin/bash

python main.py --logic Random --email=test@email.com --name=stima --password=123456 --team etimo &
python main.py --logic MyBot --email=test1@email.com --name=test --password=123456 --team etimo &
python main.py --logic Random --email=test2@email.com --name=stima2 --password=123456 --team etimo &
python main.py --logic MyBot --email=test3@email.com --name=test --password=123456 --team etimo &