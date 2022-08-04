#!/bin/bash

# version=$(<VERSION)
version=1.2.6
datapath=$(readlink --canonicalize /home/schaubnj/polus-data/polus/images/Eastman2021Infectivity/)
echo ${datapath}

# Inputs
inpDir=/data/standard/intensity
filePattern="p001_x{x+}_y{y+}_wx{r+}_wy{z+}_c{c}.ome.tif"
darkfield=true
photobleach=false
groupBy="xyrz"

# Output paths
outDir=/data/basic

docker run --mount type=bind,source=${datapath},target=/data/ \
            --gpus=all \
            --user $(id -u):$(id -g) \
            labshare/polus-basic-flatfield-correction-plugin:${version} \
            --inpDir ${inpDir} \
            --filePattern ${filePattern} \
            --darkfield ${darkfield} \
            --photobleach ${photobleach} \
            --groupBy ${groupBy} \
            --outDir ${outDir}
