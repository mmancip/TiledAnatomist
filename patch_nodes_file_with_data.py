#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import sys
import os

parser = argparse.ArgumentParser(
    description='patch nodes.js file to include data configuration in it')
parser.add_argument('-n', '--nodes',
                    help='nodes.json filename (default: nodes.json in the same '
                    'directory as this script)')
parser.add_argument('-d', '--data_config', help='data config file')
parser.add_argument('--dry-run', action='store_true')

args = parser.parse_args(sys.argv[1:])

nodes_js_file = args.nodes
data_config_file = args.data_config
dry_run = args.dry_run

if not nodes_js_file:
    nodes_js_file = os.path.join(os.path.dirname(sys.argv[0]), 'nodes.json')

nodes_js = open(nodes_js_file)
nodes_vars = json.load(nodes_js)

data_config = json.load(open(data_config_file))

for i, node in enumerate(nodes_vars["nodes"][1:]):
    node["title"] = node["title"].replace("ANATOMIST ","")+" "+data_config["data_list"][i]["subject"]
    node["tags"] = data_config["data_list"][i]["tags"]

if dry_run:
    ofile = sys.stdout
else:
    ofile = open(nodes_js_file, "w")

print(json.dumps(nodes_vars, indent=4), file=ofile,
      end='\n')
