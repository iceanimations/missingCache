'''
Created on Oct 20, 2015

@author: qurban.ali
'''
import sip
sip.setapi('QString', 2)
import sys
sys.path.insert(0, 'R:/Pipe_Repo/User/Qurban/utilities')
from PyQt4.QtGui import QApplication, QStyleFactory
from src import ui


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('plastique'))
    win = ui.UI()
    win.show()
    sys.exit(app.exec_())