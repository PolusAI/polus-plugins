#!/bin/bash

version=$(<VERSION)
docker push polusai/polus-imagej-threshold-isodata-plugin:${version}