'''
Created on Oct 21, 2015

@author: qurban.ali
'''
try:
    from uiContainer import uic
except:
    from PyQt4 import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, QTreeWidgetItem, qApp
import os.path as osp
import iutil
import cui
import _missingCache as mc
reload(mc)
reload(cui)
reload(iutil)
from pprint import pprint
import appUsageApp

rootPath = iutil.dirname(__file__, 2)
uiPath = osp.join(rootPath, 'ui')

Form3, Base3 = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class UI(Form3, Base3):
    def __init__(self, parent=None):
        super(UI, self).__init__(parent)
        self.setupUi(self)
        self.server = None
        self.title = 'MCache'
        self.lastPath = ''
        self.login()
        self.progressBar.hide()
        
        self.findButton.clicked.connect(self.find)
        self.browseButton.clicked.connect(self.setEpPath)
        self.closeButton.clicked.connect(self.close)
        self.projectBox.activated.connect(self.setProject)
        
        appUsageApp.updateDatabase('missingCache')
        
    def setStatus(self, status):
        self.statusLabel.setText(status)
        
    def processEvents(self):
        qApp.processEvents()
        
    def getProject(self):
        text = self.projectBox.currentText()
        if text == '--Select Project--': text = ''
        return text
        
    def setProject(self):
        project = self.getProject()
        if project:
            mc.setProject(project)
        
    def showMessage(self, **kwargs):
        return cui.showMessage(self, title=self.title, **kwargs)
    
    def getEpPath(self):
        path = self.epPathBox.text()
        if not osp.exists(path):
            self.showMessage(msg='The system could not find the path specified',
                             icon=QMessageBox.Warning)
            path = ''
        return path
    
    def setEpPath(self):
        path = QFileDialog.getExistingDirectory(self, self.title, self.lastPath, QFileDialog.DontUseNativeDialog)
        if path:
            self.epPathBox.setText(path)
            self.lastPath = path
        
    def find(self):
        self.treeWidget.clear()
        self.treeWidget2.clear()
#         try:
        if not self.server:
            self.showMessage(msg='Could not connect to TACTIC, please close and reopen the window',
                            icon=QMessageBox.Warning)
            return
        if not self.getProject():
            self.showMessage(msg='Select a project and then try to find missing cache files',
                            icon=QMessageBox.Information)
            return
        if not self.server: return
        epPath = self.getEpPath()
        if not epPath: return
        missing, extra, errors = mc.get(epPath=epPath)
        if missing:
            for seq, shots in missing.items():
                seqItem = QTreeWidgetItem(self.treeWidget)
                seqItem.setText(0, seq)
                for shot, assets in shots.items():
                    shotItem = QTreeWidgetItem(seqItem)
                    shotItem.setText(0, shot)
                    for asset in assets:
                        assetItem = QTreeWidgetItem(shotItem)
                        assetItem.setText(0, asset)
            self.treeWidget.expandAll()
        if extra:
            for seq, shots in extra.items():
                seqItem = QTreeWidgetItem(self.treeWidget2)
                seqItem.setText(0, seq)
                for shot, assets in shots.items():
                    shotItem = QTreeWidgetItem(seqItem)
                    shotItem.setText(0, shot)
                    for asset in assets:
                        assetItem = QTreeWidgetItem(shotItem)
                        assetItem.setText(0, asset)
            self.treeWidget2.expandAll()
        if errors:
            self.showMessage(msg='Some errors occurred while finding missing cache files',
                             details=iutil.dictionaryToDetails(errors),
                             icon=QMessageBox.Critical)
#         except Exception as ex:
#             self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
#         finally:
#             self.progressBar.hide()
#             self.progressBar.setMaximum(0)
#             self.progressBar.setValue(0)
#             self.setStatus('')
    
    def login(self):
        self.server, er = mc.setServer()
        projs, err = mc.getProjects()
        er.update(err)
        if er:
            self.showMessage(msg='Error occurred while connecting to TACTIC',
                             icon=QMessageBox.Critical,
                             details=iutil.dictionaryToDetails(er))
            return
        self.projectBox.addItems(projs)
        mc.setParent(self)