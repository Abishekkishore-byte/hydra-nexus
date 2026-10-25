"""Opens the capsule model in the FreeCAD GUI, styles it, and saves screenshots of the main window
(3D view + model tree) and of the ShellProfile sketch in Sketcher. Run: freecad.exe screenshot_macro.py"""
import os
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.environ['HN_CAD']
OUT = os.path.join(HERE, 'screenshots'); os.makedirs(OUT, exist_ok=True)
doc = App.openDocument(os.path.join(HERE, 'HydraNexus_Capsule_v1.FCStd'))
Gui.activateWorkbench('PartDesignWorkbench')
colors = {'Shell': ((0.80, 0.84, 0.90), 70), 'TopCap': ((0.05, 0.65, 0.91), 0), 'Cartridge': ((0.93, 0.95, 0.97), 0),
          'SensingCell': ((0.23, 0.51, 0.96), 30), 'UVC_Chamber': ((0.66, 0.33, 0.97), 0), 'MicroPump': ((0.20, 0.25, 0.33), 0),
          'ValveBlock': ((0.06, 0.09, 0.16), 0), 'DrySpine': ((0.08, 0.50, 0.24), 40), 'Cell18650': ((0.11, 0.31, 0.85), 0)}
for name, (c, tr) in colors.items():
    vo = doc.getObject(name).ViewObject
    vo.ShapeAppearance = (App.Material(DiffuseColor=c),)
    vo.Transparency = tr
    body = doc.getObject(name)
    vo.Visibility = True
    for f in body.Group:
        if hasattr(f, 'ViewObject') and f.ViewObject is not None and f.TypeId != 'App::Origin':
            f.ViewObject.Visibility = (f == body.Tip)
mw = Gui.getMainWindow()
mw.showNormal(); mw.resize(1600, 980); mw.move(10, 10); mw.raise_(); mw.activateWindow()

def walk(item):
    txt = item.text(0)
    if txt.startswith('Origin') or txt in ('Params',):
        item.setExpanded(False); return
    item.setExpanded(True)
    for i in range(item.childCount()):
        walk(item.child(i))

def expand():
    for t in mw.findChildren(QtGui.QTreeWidget):
        for i in range(t.topLevelItemCount()):
            walk(t.topLevelItem(i))
        t.setColumnWidth(0, 360)
    for d in mw.findChildren(QtGui.QDockWidget):
        if d.isVisible() and d.findChildren(QtGui.QTreeWidget):
            mw.resizeDocks([d], [430], QtCore.Qt.Horizontal)
            for sp in d.findChildren(QtGui.QSplitter):
                sp.setSizes([900, 60])

def shot(path):
    scr = QtGui.QGuiApplication.primaryScreen()
    pm = scr.grabWindow(mw.winId())
    if pm.isNull() or pm.width() < 100:
        pm = mw.grab()
    pm.save(path)

def step1():
    view = Gui.ActiveDocument.ActiveView
    view.viewIsometric(); view.fitAll()
    expand()
    QtCore.QTimer.singleShot(1500, step2)

def step2():
    shot(os.path.join(OUT, 'freecad_model_tree.png'))
    Gui.ActiveDocument.ActiveView.saveImage(os.path.join(OUT, 'freecad_3dview.png'), 1600, 1200, 'White')
    Gui.ActiveDocument.setEdit(doc.getObject('ShellProfile'))
    QtCore.QTimer.singleShot(2500, step3)

def step3():
    Gui.SendMsgToActiveView('ViewFit')
    expand()
    QtCore.QTimer.singleShot(1500, step4)

def step4():
    shot(os.path.join(OUT, 'freecad_sketch_constraints.png'))
    Gui.ActiveDocument.resetEdit()
    App.closeDocument(doc.Name)
    open(os.path.join(OUT, 'done.flag'), 'w').write('ok')
    QtCore.QTimer.singleShot(500, mw.close)

QtCore.QTimer.singleShot(4000, step1)
