#!/bin/bash
git checkout master
git pull
git checkout deploy
git pull
# merge to master
git checkout master
git merge dev
git push
# merge to deploy
git checkout deploy
git merge master
git push
git checkout dev
