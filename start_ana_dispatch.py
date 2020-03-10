#!/usr/bin/env python
from __future__ import print_function

import sys
import distutils.spawn
import subprocess
import argparse
import time
import os

sides = ['R', 'L']
reco_session = "session1_manual"
meshbrain = "white"
center = 't1-1mm-1'
acquisition = 'default_acquisition'
analysis = 'default_analysis'
graph_version = '3.1'

parser = argparse.ArgumentParser(
    description='Load objects in several anatomist containers')
parser.add_argument('-n', '--nbrain', help='number of containers', type=int,
                    default=0)
parser.add_argument('-d', '--data_path', help='database base path')
parser.add_argument('-s', '--subject', action='append', default=[],
                    help='subjects names (default: 001, 002, ...)')
parser.add_argument('-a', '--anadispatch',
                    help='ana_dispatcher.py program full path '
                    '(default: search in the PATH)')
parser.add_argument('-c', '--config', help='data config file (json)')

args = parser.parse_args(sys.argv[1:])

nbrain = args.nbrain
# remove 2 because one is the master (current container)
# and one is the model
data_path = args.data_path
subjects = args.subject
#if len(subjects) == 0 and nbrain != 0:
    #nbrain -= 2
    #subjects = ['%03d' % (i + 1) for i in range(nbrain)]

ana_dispatcher = args.anadispatch
if ana_dispatcher is None:
    ana_dispatcher = distutils.spawn.find_executable('ana_dispatcher.py')
    if ana_dispatcher is None:
        ana = distutils.spawn.find_executable('anatomist')
        bindir = os.path.dirname(ana)
        if bindir.endswith('real-bin'):
            bindir = os.path.dirname(ana)
        maindir = os.path.dirname(bindir)
        ana_dispatcher = os.path.join(maindir, 'ana_dispatcher.py')

print('ana_dispatcher:', ana_dispatcher)

data_config_file = args.config
if data_config_file:
    import json
    data_config = json.load(open(data_config_file))
    common_attributes = data_config['common_attributes']
    data_list = data_config['data_list']
    if 'sides' not in common_attributes:
        common_attributes['sides'] = ['R', 'L']
    if nbrain != 0:
        # truncate list to nbrain first items
        data_list = data_list[:nbrain]
else:
    common_attributes = {
        'database': data_path,
        'center': center,
        'acquisition': acquisition,
        'analysis': analysis,
        'graph_version': graph_version,
        'reco_session': reco_session,
        'meshtype': meshbrain,
        'sides': sides
    }
    data_list = [{'subject': s} for s in subjects]

if data_path:
    # if data_path is specified on the commandline, overload any config
    # settings
    common_attributes['database'] = data_path

subprocess.call([sys.executable, ana_dispatcher, '-m',
                 'self.main.load_nomenclature()'])

print('load data:', data_list)
print('common_attributes:', common_attributes)

for i, data in enumerate(data_list):
    if subjects and data['subject'] not in subjects:
        # skip non-selected subjects, still counting containers
        continue

    attribs = dict(common_attributes)
    attribs.update(data)
    sides = attribs.get('sides', ['R', 'L'])
    print('tile %d data:' %i, data)
    sys.stdout.flush()
    for sn, side in enumerate(sides):
        attribs['side'] = side

        graph_file = '%(database)s/%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/folds/%(graph_version)s/%(reco_session)s/%(side)s%(subject)s_%(reco_session)s.arg' \
            % attribs
        mesh_exts = ['.gii', '.mesh']
        for ext in mesh_exts:
            wm_mesh_file = ('%(database)s/%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/segmentation/mesh/%(subject)s_%(side)s%(meshtype)s' + ext) \
                % attribs
            print('look for:', wm_mesh_file, ":", os.path.exists(wm_mesh_file))
            if os.path.exists(wm_mesh_file):
                break
        subprocess.call([sys.executable, ana_dispatcher, '-m',
                         '<anatomist-%03d> '
                         'self.main.load_sulci_graph("%s", open_window=True, '
                         'label="name")' % (i + 2, graph_file)])
        subprocess.call([sys.executable, ana_dispatcher, '-m',
                         '<anatomist-%03d> '
                         'self.main.load_wm_mesh("%s", '
                         'win_num=%d)' % (i + 2, wm_mesh_file, sn)])

    # set subject name as window title so that we know who is who
    subprocess.call([sys.executable, ana_dispatcher, '-m',
                      '<anatomist-%03d> '
                      'self.main.block.internalWidget.widget.window()'
                      '.setWindowTitle("subject: %s")'
                      % (i + 2, attribs['subject'])])


subprocess.call([sys.executable, ana_dispatcher, '-m',
                 '<anatomist-atlas> self.main.load_model("", True)'])

subprocess.call([sys.executable, ana_dispatcher, '-m',
                 'self.main.block.internalWidget.widget.window().'
                 'showMaximized()'])
# set subnject name as window title so that we know who is who
subprocess.call([sys.executable, ana_dispatcher, '-m',
                  '<anatomist-atlas> '
                  'self.main.block.internalWidget.widget.window()'
                  '.setWindowTitle("atlas")'])

print('dispatcher done.')
