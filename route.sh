#!/bin/bash

git add . && \
git add -u && \
git commit -m $'Testing In Progress\n'"Committed on: [$(date)]"$' by Arfaz' && \
git push origin HEAD
