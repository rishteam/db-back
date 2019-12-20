#!/bin/bash
git checkout master
git pull
git checkout deploy
git pull
# merge to master
git checkout master
git merge dev
# merge to deploy
git checkout deploy
git merge master
git push --all
