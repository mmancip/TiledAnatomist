#!/usr/bin/env python

from __future__ import print_function

import zmq
import traceback
import cPickle as pickle
import threading
import sys
import argparse
import time
import weakref

if sys.version_info[0] >= 3:
    unicode = str

SUB_FILTER = u'ana_all'


def run_gui(args):

    # import GUI things only in this situation
    import anatomist.direct.api as ana
    a = ana.Anatomist()
    from soma.qt_gui.qt_backend import Qt
    from soma.qt_gui import qtThread
    import re
    import six
    from functools import partial
    from soma import uuid
    from soma import aims
    import os
    import selection


    class AnaDispatcherGui(Qt.QWidget):
        def __init__(self, dispatcher, parent=None):
            super(AnaDispatcherGui, self).__init__(parent)
            self.dispatcher = dispatcher
            self.dispatcher.gui = weakref.ref(self)

            self_dir = os.path.dirname(sys.argv[0])
            icons_dir = os.path.join(self_dir, 'icons')
            icon_size = Qt.QSize(32, 32)
            sync_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'sync.png'))) # .scaled(icon_size))
            pick_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'pick.png')))
            paster_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'pasteR.png')))
            pastel_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'pasteL.png')))
            save_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'save.png')))
            saveall_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'save_all.png')))
            block_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'block_pick.png')))
            tools_icn = Qt.QIcon(Qt.QPixmap(os.path.join(
                icons_dir, 'tools.png')))
            #icons = [sync_icn, pick_icn, paster_icn, pastel_icn, save_icn, saveall_icn]
            #for icon in icons:
                #print(icon.actualSize(icon.availableSizes()[0]))

            layout = Qt.QVBoxLayout()
            layout.setContentsMargins(2, 2, 2, 2)
            self.setLayout(layout)
            #sync = Qt.QPushButton(sync_icn, '') #, 'sync views')
            ##sync.setFixedSize(icon_size)
            #sync.setIconSize(icon_size)
            #sync.setToolTip('sync views')
            #layout.addWidget(sync)
            #pick_left = Qt.QPushButton(pick_icn, '') #, 'pick label')
            ##pick_left.setFixedSize(icon_size)
            #pick_left.setIconSize(icon_size)
            #pick_left.setToolTip('pick selected label')
            #layout.addWidget(pick_left)
            #paste_right = Qt.QPushButton(paster_icn, '') #, 'paste label (R)')
            ##paste_right.setFixedSize(icon_size)
            #paste_right.setIconSize(icon_size)
            #paste_right.setToolTip('paste on right hemisphere')
            #layout.addWidget(paste_right)
            #paste_left = Qt.QPushButton(pastel_icn, '') #, 'paste label (L)')
            ##paste_left.setFixedSize(icon_size)
            #paste_left.setIconSize(icon_size)
            #paste_left.setToolTip('paste on left hemisphere')
            #layout.addWidget(paste_left)
            #save = Qt.QPushButton(save_icn, '') #, 'save')
            ##save.setFixedSize(icon_size)
            #save.setIconSize(icon_size)
            #save.setToolTip('save graphs in current view')
            #layout.addWidget(save)
            #save_all = Qt.QPushButton(saveall_icn, '') #, 'save all')
            ##save_all.setFixedSize(icon_size)
            #save_all.setIconSize(icon_size)
            #save_all.setToolTip('save graphs from all instances')
            #layout.addWidget(save_all)
            #block = Qt.QPushButton(block_icn, '') #, 'save all')
            ##block.setFixedSize(icon_size)
            #block.setIconSize(icon_size)
            #block.setToolTip('block copy/paste through instances')
            #layout.addWidget(block)
            #block.setCheckable(True)
            #sync.clicked.connect(self.dispatcher.dispatch_sync)
            #pick_left.clicked.connect(self.dispatcher.pick_label)
            #paste_left.clicked.connect(self.dispatcher.paste_label_left)
            #paste_right.clicked.connect(self.dispatcher.paste_label_right)
            #save.clicked.connect(self.dispatcher.save_sulci_graphs)
            #save_all.clicked.connect(
                #self.dispatcher.dispatch_save_sulci_graphs)
            #self.block_btn = block
            #block.toggled.connect(self.dispatcher.dispatch_block_copy)
            #self.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Preferred)

            #w = Qt.QWidget()
            #self.setCentralWidget(w)
            #w.resize(0, 0)

            tb = Qt.QToolBar()
            #self.addToolBar(Qt.Qt.LeftToolBarArea, tb)
            tb.setOrientation(Qt.Qt.Vertical)
            layout.addWidget(tb)
            tb.setIconSize(icon_size)
            sync = tb.addAction(sync_icn, 'sync views',
                                self.dispatcher.dispatch_sync)
            pick = tb.addAction(pick_icn, 'pick label',
                                self.dispatcher.pick_label)
            paste_right = tb.addAction(paster_icn,
                                       'paste on right hemisphere',
                                       self.dispatcher.paste_label_right)
            paste_left = tb.addAction(pastel_icn, 'paste on left hemisphere',
                                      self.dispatcher.paste_label_left)
            save = tb.addAction(save_icn, 'save graphs in current view',
                                self.dispatcher.save_sulci_graphs)
            save_all = tb.addAction(saveall_icn,
                                    'save graphs from all instances',
                                    self.dispatcher.dispatch_save_sulci_graphs)
            block = tb.addAction(block_icn,
                                 'block copy/paste through instances',
                                 self.dispatcher.dispatch_block_copy)
            block.setCheckable(True)
            show_tools = tb.addAction(tools_icn, 'show/hide tools',
                                      self.dispatcher.show_tools)
            show_tools.setCheckable(True)
            self.show_tools = show_tools
            self.block_action = block
            self.block_btn = block.associatedWidgets()[0]
            self.save_action = save
            self.save_all_action = save_all


    class AnaDispatcher(object):
        def __init__(self, url='localhost', port=57025, parent=None):
            self.url = url
            self.port = port
            self.context = zmq.Context()
            self.ana = ana.Anatomist()
            self.socket = self.context.socket(zmq.PUSH)
            self.socket.connect("tcp://%s:%d" % (url, port))
            self.windows = []
            self.parent = parent
            self.block = None
            self.windows_in_groups = True
            self.groups = {}
            self.copy_blocked = False
            self.gui = None
            self.id = 'no_id'

            a = self.ana
            iconpath = os.path.join(str(a.anatomistSharedPath()), 'icons')
            pix = Qt.QPixmap(os.path.join(iconpath, 'simple3Dcontrol.png'))
            ana.cpp.IconDictionary.instance().addIcon('Left3DControl', pix)
            ana.cpp.IconDictionary.instance().addIcon('Left3DControl2', pix)
            ad = ana.cpp.ActionDictionary.instance()
            ad.addAction('SelectAndRotateAction', SelectAndRotateAction)
            ad.addAction('SyncLinkAndRotateAction', SyncLinkAndRotateAction)
            cd = ana.cpp.ControlDictionary.instance()
            cd.addControl('Left3DControl', Left3DControl, 25)
            cd.addControl('Left3DControl2', Left3DControl2, 26)
            cm = ana.cpp.ControlManager.instance()
            cm.addControl('QAGLWidget3D', '', 'Left3DControl' )
            cm.addControl('QAGLWidget3D', '', 'Left3DControl2' )
            # click on background: unselect all
            a.config()['unselect_on_background'] = 1
            #a.onCursorNotifier.add(self.dispatch_linked_cursor)
            a.dispatcher = self # allow to access me

        def dispatch_message(self, message):
            print('dispatch_message:', message)
            #self.socket.send_string(pickle.dumps(message))
            self.socket.send_string(message)

        def dispatch_method(self, method, args, kwargs):
            pargs = ', '.join([repr(arg) for arg in args])
            pkwargs = ', '.join(['%s=%s' % (k, repr(v))
                                 for k, v in six.iteritems(kwargs)])
            message = '%s(%s%s)' % (method, pargs, pkwargs)
            self.dispatch_message(message)

        def get_ana_group_id(self, group):
            agroup =  self.groups.get(group, None)
            if agroup is None:
                return 0
            return agroup.getInternalRep()

        def get_ext_group_id(self, group):
            '''
            Get internal interface group id from its internal (anatomist) one
            '''
            for n, agroup in six.iteritems(self.groups):
                if agroup.getInternalRep() == group:
                    return n
            return 0

        def dispatch_new_view(self, wintype, group=None):
            print('dispatch_%s' % wintype)
            self.dispatch_message('self.main.createWindow("%s", group=%s)'
                                  % (wintype, repr(group)))

        def dispatch_sync(self):
            group = None
            print('dispatch_sync', group)
            done_groups = set()
            for window in self.windows:
                wgroup = window.Group()
                if wgroup in done_groups \
                        or (group is not None and group != wgroup):
                    continue
                done_groups.add(wgroup)
                vinfo = window.getInfo()
                view_quat = vinfo['view_quaternion']
                slice_quat = vinfo['slice_quaternion']
                position = vinfo['position']
                obs_position = vinfo['observer_position']
                #bbmin = vinfo['boundingbox_min']
                zoom = vinfo['zoom']
                print('sync group', wgroup, ':', self.get_ext_group_id(wgroup))
                self.dispatch_message(
                    'self.main.camera(view_quaternion=%s, '
                    'slice_quaternion=%s, zoom=%f, cursor_position=%s, '
                    'observer_position=%s, group=%d)'
                    % (repr(view_quat), repr(slice_quat), zoom, repr(position),
                      repr(obs_position), self.get_ext_group_id(wgroup)))
                if group is not None:
                    break # only one group to do, and we've just done it

        def dispatch_copy_label(self):
            print('dispatch copy label')
            if [int(x) for x in self.ana.getVersion().split('.')] < [4, 6, 1]:
                print('set_picked_label cannot work in version',
                      self.ana.getVersion(),
                      ', it needs anatomist version >= 4.6.1')
                return
            done_groups = set()
            for window in self.windows:
                wgroup = window.Group()
                if wgroup in done_groups:
                    continue
                done_groups.add(wgroup)
                action = window.view().controlSwitch().getAction(
                    'LabelEditAction')
                label = action.label()
                msg = 'self.main.set_picked_label(group=%d, label="%s")' \
                    % (self.get_ext_group_id(wgroup), label)
                if self.copy_blocked:
                    # limit to self
                    msg = '<%s> %s' % (self.id, msg)
                self.dispatch_message(msg)

        def pick_label(self):
            done_groups = set()
            for window in self.windows:
                wgroup = window.Group()
                if wgroup in done_groups:
                    continue
                done_groups.add(wgroup)
                action = window.view().controlSwitch().getAction(
                    'LabelEditAction')
                action.pick()
            self.dispatch_copy_label()

        def paste_label_left(self):
            if len(self.windows) < 2:
                return
            window = self.windows[1]
            action = window.view().controlSwitch().getAction(
                'LabelEditAction')
            action.edit()

        def paste_label_right(self):
            if len(self.windows) < 1:
                return
            window = self.windows[0]
            action = window.view().controlSwitch().getAction(
                'LabelEditAction')
            action.edit()

        def createWindow(self, wtype, show_toolbars=False, *args, **kwargs):
            new_block = False
            if self.block is None:
                self.block = self.ana.createWindowsBlock()
                self.block.setWidget(self.parent)
                layout = Qt.QGridLayout()
                self.parent.layout().addLayout(layout)
                self.block.layout = layout
                new_block = True
            group = 0
            if 'group' in kwargs:
                group = kwargs['group']
                kwargs = dict(kwargs)
                del kwargs['group']
            elif self.windows_in_groups:
                group = len(self.windows)
            if group != 0:
                wgroup = self.groups.get(group)
                if wgroup is None:
                    wgroup = self.ana.AWindowsGroup(self.ana)
                    self.groups[group] = wgroup
                    group = wgroup.getInternalRep()
                else:
                    wgroup = wgroup[0]
            self.windows.append(self.ana.createWindow(wtype, block=self.block,
                                                      *args, **kwargs))

            if wtype in ('Axial', 'Sagittal', 'Coronal'):
                self.windows[-1].setControl('Left3DControl2')
            else:
                self.windows[-1].setControl('Left3DControl')
            if not show_toolbars:
                sel_label = self.windows[-1].findChild(Qt.QLabel,
                                                       'selectionLabel')
                if sel_label is not None:
                    gv = self.windows[-1].findChild(Qt.QGraphicsView)
                    if gv is not None:
                        sel_label.parent().layout().removeWidget(sel_label)
                        scene = gv.scene()
                        if scene is None:
                            scene = Qt.QGraphicsScene(gv)
                            gv.setScene(scene)
                        sel_label.setParent(None)
                        lproxy = gv.scene().addWidget(sel_label)
                        sel_label.show()
                        tr = lproxy.transform()
                        tr.translate(3, 3)
                        lproxy.setTransform(tr)
                        lproxy.show()
                #if sel_label is not None:
                    #lay = self.windows[-1].window().findChild(Qt.QHBoxLayout,
                                                              #'sel_layout')
                    #if lay is not None:
                        #lay.addWidget(sel_label)
                self.windows[-1].showToolBars(0)
            orientations = [[0.5, -0.5, -0.5, 0.5], [0.5, 0.5, 0.5, 0.5]]
            if len(self.windows) <= len(orientations) \
                    and wtype == '3D':
                self.windows[-1].camera(
                    view_quaternion=orientations[len(self.windows) - 1])

            if group != 0:
                self.ana.linkWindows([self.windows[-1]], group=wgroup)

            # insert window in layout
            nw = len(self.windows) - 1
            r = nw // self.block.nbCols
            c = nw % self.block.nbCols
            self.block.layout.addWidget(self.windows[-1].getInternalRep(),
                                        r, c)

            # if new_block:
                ##self.block.internalWidget.widget.setParent(self.parent)
                #self.block.internalWidget.widget.setParent(None)
                #self.parent.layout().addWidget(
                    #self.block.internalWidget.widget)
                #self.block.internalWidget.widget.menuBar().hide()
                #print('draw:', self.windows[-1].view())
                #print('d parent:', self.windows[-1].view().parent())
                #print('win wid:', self.windows[-1].centralWidget())
                ##self.windows[-1].view().parent().setParent(self.windows[-1].centralWidget())

        def load_nomenclature(self):
            self.nomeclature = self.ana.loadObject(
                os.path.join(aims.carto.Paths.findResourceFile(
                    os.path.join('nomenclature', 'hierarchy',
                                 'sulcal_root_colors.hie'))))

        def load_sulci_graph(self, filename=None, open_window=False,
                             label=None, win_num=None):
            if not hasattr(self, 'graphs'):
                self.graphs = []
            if filename is None:
                if win_num is not None \
                        and win_num < len(self.graphs) \
                        and win_num >= -len(self.graphs):
                    filename = self.graphs[win_num].filename
                else:
                    print('load_sulci_graph should be provided a filename',
                          file=sys.stderr)
                    return
            graph = self.ana.loadObject(filename)
            graph.applyBuiltinReferential()
            if win_num is not None and win_num < len(self.graphs) \
                    and win_num >= -len(self.graphs):
                self.graphs[win_num] = graph
                n = win_num
            else:
                n = len(self.graphs)
                self.graphs.append(graph)
            if hasattr(self, 'wm_meshes') and len(self.wm_meshes) > n:
                self.wm_meshes[n].setReferential(graph.referential)

            if label is not None:
                self.ana.execute('GraphDisplayProperties',
                                  objects=[graph],
                                  nomenclature_property=label)
            if win_num is None and open_window:
                self.createWindow('3D', show_toolbars=False)
                win_num = -1
            if win_num is not None and win_num < len(self.windows) \
                    and win_num >= -len(self.windows):
                self.windows[win_num].addObjects(graph)
                self.windows[win_num].setReferential(
                    self.ana.centralReferential())

        def load_wm_mesh(self, filename, open_window=False, win_num=None):
            if not hasattr(self, 'wm_meshes'):
                self.wm_meshes = []
            if filename is None:
                if win_num is not None \
                        and win_num < len(self.wm_meshes) \
                        and win_num >= -len(self.wm_meshes):
                    filename = self.wm_meshes[win_num].filename
                else:
                    print('load_wm_mesh should be provided a filename',
                          file=sys.stderr)
                    return
            wm_mesh = self.ana.loadObject(filename)
            wm_mesh.setMaterial(
                diffuse=[1, 0.85, 0.5, 0.8],
                selectable_mode='selectable_when_not_totally_transparent')
            if win_num is not None and win_num < len(self.wm_meshes) \
                    and win_num >= -len(self.wm_meshes):
                self.wm_meshes[win_num] = wm_mesh
                n = win_num
            else:
                n = len(self.wm_meshes)
                self.wm_meshes.append(wm_mesh)
            if hasattr(self, 'graphs') and len(self.graphs) > n:
                wm_mesh.setReferential(self.graphs[n].referential)
            if win_num is None and open_window:
                self.createWindow('3D', show_toolbars=False)
                self.windows[-1].camera(
                    view_quaternion=aims.Point4df([1, 0, 0, 1]).normalize())
                win_num = -1
            if win_num is not None and win_num < len(self.windows) \
                    and win_num >= -len(self.windows):
                self.windows[win_num].addObjects(wm_mesh)
                self.windows[win_num].setReferential(
                    self.ana.centralReferential())

        def load_mri(self, filename, open_window=False, win_num=None,
                     **kwargs):
            if not hasattr(self, 'mri'):
                self.mri = []
            if filename is None:
                if win_num is not None \
                        and win_num < len(self.wm_meshes) \
                        and win_num >= -len(self.wm_meshes):
                    filename = self.mri[win_num].filename
                else:
                    print('load_mri should be provided a filename',
                          file=sys.stderr)
                    return
            mri = self.ana.loadObject(filename)
            #mri.setPalette(...)
            if win_num is not None and win_num < len(self.wm_meshes) \
                    and win_num >= -len(self.wm_meshes):
                self.mri[win_num] = mri
                n = win_num
            else:
                n = len(self.mri)
                self.mri.append(mri)
            if hasattr(self, 'graphs') and len(self.graphs) > n:
                mri.setReferential(self.graphs[n].referential)
            if win_num is None and open_window:
                wtype = 'Axial'
                if open_window != True:
                    # assume open_window is a type
                    wtype = open_window
                print('wtype:', wtype)
                self.createWindow(wtype, show_toolbars=False, **kwargs)
                win_num = -1
            if win_num is not None and win_num < len(self.windows) \
                    and win_num >= -len(self.windows):
                self.windows[win_num].addObjects(mri)
                self.windows[win_num].setReferential(
                    self.ana.centralReferential())


        def load_model(self, side='', open_window=False, win_num=None):
            if side == '':
                self.load_model('R', open_window)
                self.load_model('L', open_window)
                return

            full_side = 'left'
            if side == 'R':
                full_side = 'right'

            objects_files = [
                'models/models_2008/descriptive_models/segments/global_registered_spam_%(full_side)s/meshes/%(side)sspam_model_meshes_1.arg',
                'models/models_2008/descriptive_models/segments/global_registered_spam_%(full_side)s/meshes/%(side)swhite_spam.gii',
            ]

            attribs = {
                'side': side,
                'full_side': full_side,
            }

            a = self.ana
            objects = [a.loadObject(aims.carto.Paths.findResourceFile(
                           obj_file % attribs))
                       for obj_file in objects_files]

            mesh = objects[1]
            ref = a.createReferential()
            mesh.assignReferential(ref)
            trans = aims.carto.Paths.findResourceFile(
                'models/models_2008/descriptive_models/segments/global_registered_spam_left/meshes/Lwhite_TO_global_spam.trm')
            a.loadTransformation(trans, ref, a.centralReferential())

            print('win_num, open_window:', win_num, open_window)
            if win_num is None and open_window:
                self.createWindow('3D', show_toolbars=False)
                win_num = -1
            if win_num is not None and win_num < len(self.windows) \
                    and win_num >= -len(self.windows):
                self.windows[win_num].addObjects(objects)

            if not hasattr(self, 'graphs'):
                self.graphs = []
            if win_num < 0 or win_num >= len(self.graphs):
                self.graphs.append(objects[0])
            else:
                self.graphs[win_num] = objects[0]

            if not hasattr(self, 'wm_meshes'):
                self.wm_meshes = []
            if win_num < 0 or win_num >= len(self.wm_meshes):
                self.wm_meshes.append(objects[1])
            else:
                self.wm_meshes[win_num] = mesh

        def save_sulci_graphs(self):
            if not hasattr(self, 'graphs'):
                return
            Qt.qApp.setOverrideCursor(Qt.Qt.WaitCursor)
            self.parent.setEnabled(False)
            Qt.qApp.processEvents()
            for graph in self.graphs:
                graph.save()
            self.parent.setEnabled(True)
            Qt.qApp.restoreOverrideCursor()

        def dispatch_save_sulci_graphs(self):
            print('dispatch_save_sulci_graphs')
            self.dispatch_message('self.main.save_sulci_graphs()')

        def camera(self, group=0, **kwargs):
            print('set camera group', group)
            group = self.get_ana_group_id(group)
            print('ana group:', group)
            for window in self.windows:
                if window.Group() == group:
                    window.camera(**kwargs)

        #def dispatch_linked_cursor(self, event_name, params):
            #print('dispatch_linked_cursor')
            #pos = params['position'][:3]
            #win = params['window']
        def dispatch_linked_cursor(self, group, pos):
            self.dispatch_message('self.main.move_linked_cursor(%d, %s)'
                                  % (group, repr(list(pos))))

        def move_linked_cursor(self, group, position):
            for win in self.windows:
                if win.Group() == group:
                    self.sent_pos = False
                    win.moveLinkedCursor(position)

        def set_picked_label(self, group, label):
            if [int(x) for x in self.ana.getVersion().split('.')] < [4, 6, 1]:
                print('set_picked_label cannot work in version',
                      self.ana.getVersion(),
                      ', it needs anatomist version >= 4.6.1')
                return
            group = self.get_ana_group_id(group)
            print('set_picked_label for group', group)
            for window in self.windows:
                if window.Group() == group:
                    action = window.view().controlSwitch().getAction(
                        'LabelEditAction')
                    if hasattr(self, 'graphs') and len(self.graphs) != 0:
                        graph = self.graphs[0]
                    else:
                        graph = None
                    action.setLabel(label, graph)

        def dispatch_block_copy(self, do_block=None):
            if do_block is None:
                do_block = self.gui().block_action.isChecked()
            self.dispatch_message('self.main.block_copy(%s)'
                                  % str(bool(do_block)))

        def block_copy(self, do_block=None):
            self.copy_blocked = do_block
            if self.gui is not None:
                gui = self.gui()
            if gui is not None:
                gui.block_btn.blockSignals(True)
                gui.block_btn.setChecked(do_block)
                gui.block_btn.blockSignals(False)

        def show_tools(self):
            state = True
            if self.gui:
                state = self.gui().show_tools.isChecked()
            print('state:', state)
            for window in self.windows:
                print(window)
                window.showToolBars(state)


    class SelectAndRotateAction(ana.cpp.ContinuousTrackball):
        def name(self):
            return 'SelectAndRotateAction'

        def beginTrackball(self, x, y, gx, gy):
            super(SelectAndRotateAction, self).beginTrackball(x, y, gx, gy)
            self.startx = x
            self.starty = y
            self.start_time = time.time()

        def endTrackball(self, x, y, gx, gy):
            super(SelectAndRotateAction, self).endTrackball(x, y, gx, gy)
            if time.time() - self.start_time < 0.5:
                action = self.view().controlSwitch().getAction(
                    'SelectAction')
                if action is not None:
                    action.execSelect(x, y, gx, gy)


    class SyncLinkAndRotateAction(ana.cpp.ContinuousTrackball):
        def name(self):
            return 'SyncLinkAndRotateAction'

        def beginTrackball(self, x, y, gx, gy):
            super(SyncLinkAndRotateAction, self).beginTrackball(x, y, gx, gy)
            self.startx = x
            self.starty = y
            self.start_time = time.time()

        def endTrackball(self, x, y, gx, gy):
            super(SyncLinkAndRotateAction, self).endTrackball(x, y, gx, gy)
            if time.time() - self.start_time < 0.5:
                action = self.view().controlSwitch().getAction(
                    'LinkAction')
                if action is not None:
                    action.execLink(x, y, gx, gy)
                    win = self.view().aWindow()
                    ana.Anatomist().dispatcher.dispatch_linked_cursor(
                        win.Group(), win.getPosition()[:3])



    # define another control where rotation is with the left mouse button
    # (useful for touch devices)
    class Left3DControl(selection.SelectionControl):

        def __init__(self, name='Left3DControl'):
            super(Left3DControl, self).__init__(name)

        def eventAutoSubscription(self, pool):
            key = Qt.Qt
            NoModifier = key.NoModifier
            ShiftModifier = key.ShiftModifier
            ControlModifier = key.ControlModifier
            super(Left3DControl, self).eventAutoSubscription(pool)
            self.mousePressButtonEventUnsubscribe(key.LeftButton, NoModifier)
            self.mousePressButtonEventUnsubscribe(key.RightButton, NoModifier)
            self.mouseDoubleClickEventUnsubscribe(key.LeftButton, NoModifier)
            self.mouseLongEventUnsubscribe(key.MiddleButton, NoModifier)
            self.mouseLongEventSubscribe(
                key.LeftButton, NoModifier,
                pool.action('SelectAndRotateAction').beginTrackball,
                pool.action('SelectAndRotateAction').moveTrackball,
                pool.action('SelectAndRotateAction').endTrackball, True )
            self.keyPressEventSubscribe(key.Key_Space, ControlModifier,
                pool.action("SelectAndRotateAction").startOrStop)
            #self.mousePressButtonEventSubscribe(key.MiddleButton, NoModifier,
                #pool.action('LinkAction').execLink)
            self.mousePressButtonEventSubscribe(key.MiddleButton, NoModifier,
                pool.action('SelectAction').execSelect)
            self.mouseDoubleClickEventSubscribe(
                key.LeftButton, NoModifier,
                pool.action('SelectAction').execSelect)
            self.mousePressButtonEventSubscribe(
                key.RightButton, NoModifier,
                pool.action('SelectAction').execSelectToggling)
            self.keyPressEventSubscribe(key.Key_Return, NoModifier,
                pool.action('LabelEditAction').edit)


    # define another control where rotation is with the left mouse button
    # (useful for touch devices)
    class Left3DControl2(selection.SelectionControl):

        def __init__(self, name='Left3DControl2'):
            super(Left3DControl2, self).__init__(name)

        def eventAutoSubscription(self, pool):
            key = Qt.Qt
            NoModifier = key.NoModifier
            ShiftModifier = key.ShiftModifier
            ControlModifier = key.ControlModifier
            super(Left3DControl2, self).eventAutoSubscription(pool)
            self.mousePressButtonEventUnsubscribe(key.LeftButton, NoModifier)
            self.mousePressButtonEventUnsubscribe(key.RightButton, NoModifier)
            self.mouseDoubleClickEventUnsubscribe(key.LeftButton, NoModifier)
            self.mouseLongEventUnsubscribe(key.MiddleButton, NoModifier)
            self.mouseLongEventSubscribe(
                key.LeftButton, NoModifier,
                pool.action('SyncLinkAndRotateAction').beginTrackball,
                pool.action('SyncLinkAndRotateAction').moveTrackball,
                pool.action('SyncLinkAndRotateAction').endTrackball, True )
            self.keyPressEventSubscribe(key.Key_Space, ControlModifier,
                pool.action("SyncLinkAndRotateAction").startOrStop)
            #self.mousePressButtonEventSubscribe(key.MiddleButton, NoModifier,
                #pool.action('LinkAction').execLink)
            self.mousePressButtonEventSubscribe(key.MiddleButton, NoModifier,
                pool.action('SelectAction').execSelect)
            self.mouseDoubleClickEventSubscribe(
                key.LeftButton, NoModifier,
                pool.action('SelectAction').execSelect)
            self.mousePressButtonEventSubscribe(
                key.RightButton, NoModifier,
                pool.action('SelectAction').execSelectToggling)
            self.keyPressEventSubscribe(key.Key_Return, NoModifier,
                pool.action('LabelEditAction').edit)


    class AnaServer(threading.Thread):
        def __init__(self, url='localhost', port=57026, main=None, id=None):
            super(AnaServer, self).__init__()
            self.ana = ana.Anatomist()
            self.main = main
            self.id = id
            self.main.id = id
            if id is None:
                self.id = unicode(uuid.Uuid())
            else:
                self.id = unicode(self.id)
            self.objects = {'ana': self.ana, 'self': self, 'main': self.main}
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.SUB)
            print('listen:', "tcp://%s:%d" % (url, port))
            self.socket.connect("tcp://%s:%d" % (url, port))
            self.sub_filter = SUB_FILTER
            # Python 2 - ascii bytes to unicode str
            #if isinstance(sub_filter, bytes):
                #sub_filter = sub_filter.decode('ascii')
            self.socket.setsockopt_string(zmq.SUBSCRIBE, self.sub_filter)
            if self.id is not None:
                self.socket.setsockopt_string(zmq.SUBSCRIBE, self.id)
            self.thread_call = qtThread.QtThreadCall()
            self.stopped = False
            self.lock = threading.RLock()
            #self.var_re = re.compile('\$([a-zA-Z_][a-zA-Z0-9_]*)')

        #def parse_args(args, kwargs):
            #new_args = None
            #new_kwargs = None
            #for arg in args:
                #m = self.var_re.match(arg, re.M)
                #if m:
                    #for g in m.groups()
                    #var = g.

        def run(self):
            while True:
                with self.lock:
                    if self.stopped:
                        break
                Qt.qApp.processEvents()
                #  Wait for next request from client
                poll = self.socket.poll(2000)
                if poll != 0:
                    print('something happens.')
                    message = self.socket.recv_string()
                    if message.startswith(self.sub_filter + ' '):
                        message = message[len(self.sub_filter) + 1:]
                    elif message.startswith(self.id + ' '):
                        print('(just for me)')
                        message = message[len(self.id) + 1:]
                    try:
                        if type(message) is not str:
                            message = message.encode()
                        print('message:', message)
                        #object, args, kwargs = pickle.loads(message)
                        #print('received message:', object, args, kwargs)
                        try:
                            #obj = object.split('.')
                            #main_obj = self.objects.get(main_obj, self)
                            #for o in obj[1:]:
                                #func = getattr(main_obj, o)
                            #result = self.thread_call.call(func, *args,
                                                           #**kwargs)
                            result = self.thread_call.call(
                                eval, message, globals(), locals())
                            result = qtThread.MainThreadLife(result)
                            #self.socket.send('OK')
                        except Exception as e:
                            result = e
                            raise
                    except:
                        print()
                        traceback.print_exc()

        def stop(self):
            with self.lock:
                self.stopped = True


    def run_main(args):
        dispatch_port = args.port
        listen_port = args.dispatch
        url = args.url
        ana_id = args.id

        print('listening to local port:', listen_port)
        print('dispatching to:', url, dispatch_port)

        #widget = Qt.QSplitter()
        widget = Qt.QWidget()
        lay = Qt.QHBoxLayout()
        lay.setContentsMargins(3, 3, 3, 3)
        widget.setLayout(lay)
        dispatcher = AnaDispatcher(url, dispatch_port, parent=widget)
        gui = AnaDispatcherGui(dispatcher)
        #gui.setParent(widget)
        lay.addWidget(gui)
        print(gui.sizeHint().width(), gui.sizeHint().height())
        gui.resize(gui.sizeHint())
        server = AnaServer(url, listen_port, id=ana_id, main=dispatcher)
        server.start()

        widget.show()

        print('ana_dispatcher ready.')
        sys.stdout.flush()
        Qt.qApp.exec_()

        server.stop()
        server.join()
        del server
        del dispatcher

    # do things
    if args is not None:
        run_main(args)
    # else import only


class AnaBroker(object):
    ''' ZMQ PULL from any individual anatomist, then output PUB
    '''
    def __init__(self, listen_port, dispatch_port):
        self.listen_port = listen_port
        self.dispatch_port = dispatch_port
        self.context = zmq.Context()
        self.dispatch_socket = self.context.socket(zmq.PUB)
        self.dispatch_socket.bind('tcp://*:%d' % dispatch_port)
        self.listen_socket = self.context.socket(zmq.PULL)
        self.listen_socket.bind('tcp://*:%d' % listen_port)

        # Python 2 - ascii bytes to unicode str
        self.sub_filter = SUB_FILTER
        #if isinstance(SUB_FILTER, bytes):
            #self.sub_filter = sub_filter.decode('ascii')

    def serve_forever(self):
        print('ana_dispatcher ready.')
        sys.stdout.flush()
        while True:
            message = self.listen_socket.recv_string()
            dest = self.sub_filter
            if message.startswith('<'):
                i = message.find('>')
                if i < 0:
                    print('message not understood:', message)
                dest = message[1:i]
                print('message for:', dest)
                message = message[i+2:]
            print('transmit message:', message)
            self.dispatch_socket.send_string('%s %s'
                                             % (dest, message))


def send_message(args):
    url = args.url
    port = args.port
    messages = args.message
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://%s:%d" % (url, port))
    for message in messages:
        socket.send_string(message)



def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Anatomist commands dispatcher')
    parser.add_argument('-b', '--broker', action='store_true',
                        help='broker mode, receives and dispatches messages')
    parser.add_argument('-m', '--message', action='append',
                        help='message mode: send the given message via the '
                        'broker (using its listen port, see -p). Messages can '
                        'be addressed to a single Anatomist instance given '
                        'its ID, if the message starts with "<ID> ". '
                        'Several messages can be sent using several -m '
                        'options')
    parser.add_argument('-p', '--port', type=int, default=57025,
                        help='broker listen port; default: 57025')
    parser.add_argument('-d', '--dispatch', type=int, default=57026,
                        help='broker dispatch port; default: 57026')
    parser.add_argument('-u', '--url', default='localhost',
                        help='connect to broker on this url '
                        '(default: localhost)')
    parser.add_argument('-i', '--id',
                        help='ID assigned to an Anatomist instance. Messages '
                        'can be sent to it via the broker using this ID. If '
                        'not specified, a unique id (uuid) will be generated '
                        'and print on the standard output at startup.')

    args = parser.parse_args(argv[1:])
    return args


if __name__ == '__main__':
    args = parse_args(sys.argv)

    if args.broker:

        broker = AnaBroker(args.port, args.dispatch)
        broker.serve_forever()

    elif args.message:

        send_message(args)

    else:

        run_gui(args)

example = '''
ana_dispatcher.py -m 'self.main.load_nomenclature()'
#ana_dispatcher.py -m 'self.main.createWindow("3D")'
#ana_dispatcher.py -m 'self.main.createWindow("3D", group=1)'
ana_dispatcher.py -m '<anatomist-1> self.main.load_sulci_graph("/volatile/riviere/basetests-3.1.0/subjects/sujet01/t1mri/default_acquisition/default_analysis/folds/3.1/default_session_auto/Rsujet01_default_session_auto.arg", open_window=True, label="label")'
ana_dispatcher.py -m '<anatomist-1> self.main.load_sulci_graph("/volatile/riviere/basetests-3.1.0/subjects/sujet01/t1mri/default_acquisition/default_analysis/folds/3.1/default_session_auto/Lsujet01_default_session_auto.arg", open_window=True, label="label")'
ana_dispatcher.py -m '<anatomist-1> self.main.load_wm_mesh("/volatile/riviere/basetests-3.1.0/subjects/sujet01/t1mri/default_acquisition/default_analysis/segmentation/mesh/sujet01_Rwhite.gii", win_num=0)'
ana_dispatcher.py -m '<anatomist-1> self.main.load_wm_mesh("/volatile/riviere/basetests-3.1.0/subjects/sujet01/t1mri/default_acquisition/default_analysis/segmentation/mesh/sujet01_Lwhite.gii", win_num=1)'

ana_dispatcher.py -m '<anatomist-0> self.main.load_model("", True)'
'''

