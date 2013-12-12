# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Thu Dec 12 13:29:46 2013
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(877, 721)
        MainWindow.setUnifiedTitleAndToolBarOnMac(True)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName(_fromUtf8("centralWidget"))
        self.seismicityTitleLabel = QtGui.QLabel(self.centralWidget)
        self.seismicityTitleLabel.setGeometry(QtCore.QRect(10, 10, 141, 20))
        self.seismicityTitleLabel.setObjectName(_fromUtf8("seismicityTitleLabel"))
        self.seismic_data_frame = QtGui.QFrame(self.centralWidget)
        self.seismic_data_frame.setGeometry(QtCore.QRect(10, 30, 851, 151))
        self.seismic_data_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.seismic_data_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.seismic_data_frame.setObjectName(_fromUtf8("seismic_data_frame"))
        self.seismic_data_plot = SeismicityPlotWidget(self.seismic_data_frame)
        self.seismic_data_plot.setGeometry(QtCore.QRect(-1, 0, 851, 151))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.seismic_data_plot.sizePolicy().hasHeightForWidth())
        self.seismic_data_plot.setSizePolicy(sizePolicy)
        self.seismic_data_plot.setObjectName(_fromUtf8("seismic_data_plot"))
        self.controlsBox = QtGui.QGroupBox(self.centralWidget)
        self.controlsBox.setEnabled(True)
        self.controlsBox.setGeometry(QtCore.QRect(10, 370, 351, 111))
        self.controlsBox.setObjectName(_fromUtf8("controlsBox"))
        self.simulationCheckBox = QtGui.QCheckBox(self.controlsBox)
        self.simulationCheckBox.setGeometry(QtCore.QRect(100, 80, 90, 20))
        self.simulationCheckBox.setChecked(True)
        self.simulationCheckBox.setObjectName(_fromUtf8("simulationCheckBox"))
        self.startButton = QtGui.QPushButton(self.controlsBox)
        self.startButton.setGeometry(QtCore.QRect(10, 30, 111, 32))
        self.startButton.setObjectName(_fromUtf8("startButton"))
        self.pauseButton = QtGui.QPushButton(self.controlsBox)
        self.pauseButton.setGeometry(QtCore.QRect(120, 30, 111, 32))
        self.pauseButton.setObjectName(_fromUtf8("pauseButton"))
        self.stopButton = QtGui.QPushButton(self.controlsBox)
        self.stopButton.setGeometry(QtCore.QRect(230, 30, 111, 32))
        self.stopButton.setObjectName(_fromUtf8("stopButton"))
        self.speedBox = QtGui.QSpinBox(self.controlsBox)
        self.speedBox.setGeometry(QtCore.QRect(260, 77, 71, 25))
        self.speedBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.speedBox.setMinimum(1)
        self.speedBox.setMaximum(10000)
        self.speedBox.setProperty("value", 1000)
        self.speedBox.setObjectName(_fromUtf8("speedBox"))
        self.speedLabel = QtGui.QLabel(self.controlsBox)
        self.speedLabel.setGeometry(QtCore.QRect(204, 80, 51, 20))
        self.speedLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.speedLabel.setObjectName(_fromUtf8("speedLabel"))
        self.statusBox = QtGui.QGroupBox(self.centralWidget)
        self.statusBox.setGeometry(QtCore.QRect(10, 490, 351, 121))
        self.statusBox.setObjectName(_fromUtf8("statusBox"))
        self.coreStatusLabel = QtGui.QLabel(self.statusBox)
        self.coreStatusLabel.setGeometry(QtCore.QRect(10, 30, 271, 16))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.coreStatusLabel.setFont(font)
        self.coreStatusLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.coreStatusLabel.setObjectName(_fromUtf8("coreStatusLabel"))
        self.projectTimeTitleLabel = QtGui.QLabel(self.statusBox)
        self.projectTimeTitleLabel.setGeometry(QtCore.QRect(10, 50, 91, 16))
        self.projectTimeTitleLabel.setObjectName(_fromUtf8("projectTimeTitleLabel"))
        self.lastEventTitleLabel = QtGui.QLabel(self.statusBox)
        self.lastEventTitleLabel.setGeometry(QtCore.QRect(10, 70, 71, 16))
        self.lastEventTitleLabel.setObjectName(_fromUtf8("lastEventTitleLabel"))
        self.nextForeCastTitleLabel = QtGui.QLabel(self.statusBox)
        self.nextForeCastTitleLabel.setGeometry(QtCore.QRect(10, 90, 101, 16))
        self.nextForeCastTitleLabel.setObjectName(_fromUtf8("nextForeCastTitleLabel"))
        self.projectTimeLabel = QtGui.QLabel(self.statusBox)
        self.projectTimeLabel.setGeometry(QtCore.QRect(110, 50, 221, 20))
        self.projectTimeLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.projectTimeLabel.setObjectName(_fromUtf8("projectTimeLabel"))
        self.lastEventLabel = QtGui.QLabel(self.statusBox)
        self.lastEventLabel.setGeometry(QtCore.QRect(110, 70, 221, 20))
        self.lastEventLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lastEventLabel.setObjectName(_fromUtf8("lastEventLabel"))
        self.nextForecastLabel = QtGui.QLabel(self.statusBox)
        self.nextForecastLabel.setGeometry(QtCore.QRect(110, 90, 221, 20))
        self.nextForecastLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.nextForecastLabel.setObjectName(_fromUtf8("nextForecastLabel"))
        self.hydraulic_data_frame = QtGui.QFrame(self.centralWidget)
        self.hydraulic_data_frame.setGeometry(QtCore.QRect(10, 210, 851, 151))
        self.hydraulic_data_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.hydraulic_data_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.hydraulic_data_frame.setObjectName(_fromUtf8("hydraulic_data_frame"))
        self.hydraulic_data_plot = HydraulicsPlotWidget(self.hydraulic_data_frame)
        self.hydraulic_data_plot.setGeometry(QtCore.QRect(-1, -1, 851, 151))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hydraulic_data_plot.sizePolicy().hasHeightForWidth())
        self.hydraulic_data_plot.setSizePolicy(sizePolicy)
        self.hydraulic_data_plot.setObjectName(_fromUtf8("hydraulic_data_plot"))
        self.hydraulicsTitleLabel = QtGui.QLabel(self.centralWidget)
        self.hydraulicsTitleLabel.setGeometry(QtCore.QRect(10, 190, 141, 20))
        self.hydraulicsTitleLabel.setObjectName(_fromUtf8("hydraulicsTitleLabel"))
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 877, 22))
        self.menuBar.setObjectName(_fromUtf8("menuBar"))
        self.menu_Project = QtGui.QMenu(self.menuBar)
        self.menu_Project.setObjectName(_fromUtf8("menu_Project"))
        self.menuSimulation = QtGui.QMenu(self.menuBar)
        self.menuSimulation.setObjectName(_fromUtf8("menuSimulation"))
        self.menuWindow = QtGui.QMenu(self.menuBar)
        self.menuWindow.setObjectName(_fromUtf8("menuWindow"))
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtGui.QToolBar(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mainToolBar.sizePolicy().hasHeightForWidth())
        self.mainToolBar.setSizePolicy(sizePolicy)
        self.mainToolBar.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.mainToolBar.setFloatable(False)
        self.mainToolBar.setObjectName(_fromUtf8("mainToolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        MainWindow.setStatusBar(self.statusBar)
        self.actionImport_Seismic_Data = QtGui.QAction(MainWindow)
        self.actionImport_Seismic_Data.setObjectName(_fromUtf8("actionImport_Seismic_Data"))
        self.actionView_Data = QtGui.QAction(MainWindow)
        self.actionView_Data.setObjectName(_fromUtf8("actionView_Data"))
        self.actionStart_Simulation = QtGui.QAction(MainWindow)
        self.actionStart_Simulation.setObjectName(_fromUtf8("actionStart_Simulation"))
        self.actionPause_Simulation = QtGui.QAction(MainWindow)
        self.actionPause_Simulation.setObjectName(_fromUtf8("actionPause_Simulation"))
        self.actionStop_Simulation = QtGui.QAction(MainWindow)
        self.actionStop_Simulation.setObjectName(_fromUtf8("actionStop_Simulation"))
        self.actionShow_GR = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/toolbar-buttons/images/view-gr-toolbar-button.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionShow_GR.setIcon(icon)
        self.actionShow_GR.setObjectName(_fromUtf8("actionShow_GR"))
        self.actionImport_Hydraulic_Data = QtGui.QAction(MainWindow)
        self.actionImport_Hydraulic_Data.setObjectName(_fromUtf8("actionImport_Hydraulic_Data"))
        self.actionOpen_Project = QtGui.QAction(MainWindow)
        self.actionOpen_Project.setObjectName(_fromUtf8("actionOpen_Project"))
        self.actionNew_Project = QtGui.QAction(MainWindow)
        self.actionNew_Project.setObjectName(_fromUtf8("actionNew_Project"))
        self.actionForecasts = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/toolbar-buttons/images/forecast-window-toolbar-button.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionForecasts.setIcon(icon1)
        self.actionForecasts.setObjectName(_fromUtf8("actionForecasts"))
        self.menu_Project.addAction(self.actionNew_Project)
        self.menu_Project.addAction(self.actionOpen_Project)
        self.menu_Project.addSeparator()
        self.menu_Project.addAction(self.actionImport_Seismic_Data)
        self.menu_Project.addAction(self.actionImport_Hydraulic_Data)
        self.menu_Project.addSeparator()
        self.menu_Project.addAction(self.actionView_Data)
        self.menuSimulation.addAction(self.actionStart_Simulation)
        self.menuSimulation.addAction(self.actionPause_Simulation)
        self.menuSimulation.addAction(self.actionStop_Simulation)
        self.menuWindow.addAction(self.actionShow_GR)
        self.menuWindow.addAction(self.actionForecasts)
        self.menuBar.addAction(self.menu_Project.menuAction())
        self.menuBar.addAction(self.menuSimulation.menuAction())
        self.menuBar.addAction(self.menuWindow.menuAction())
        self.mainToolBar.addAction(self.actionShow_GR)
        self.mainToolBar.addAction(self.actionForecasts)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "ATLAS i.s.", None))
        self.seismicityTitleLabel.setText(_translate("MainWindow", "Seismicity", None))
        self.controlsBox.setTitle(_translate("MainWindow", "Controls", None))
        self.simulationCheckBox.setText(_translate("MainWindow", "Simulation", None))
        self.startButton.setText(_translate("MainWindow", "Start", None))
        self.pauseButton.setText(_translate("MainWindow", "Pause", None))
        self.stopButton.setText(_translate("MainWindow", "Stop", None))
        self.speedBox.setSuffix(_translate("MainWindow", "x", None))
        self.speedLabel.setText(_translate("MainWindow", "Speed", None))
        self.statusBox.setTitle(_translate("MainWindow", "Status", None))
        self.coreStatusLabel.setText(_translate("MainWindow", "Idle", None))
        self.projectTimeTitleLabel.setText(_translate("MainWindow", "Project Time:", None))
        self.lastEventTitleLabel.setText(_translate("MainWindow", "Last Event:", None))
        self.nextForeCastTitleLabel.setText(_translate("MainWindow", "Next Forecast:", None))
        self.projectTimeLabel.setText(_translate("MainWindow", "-", None))
        self.lastEventLabel.setText(_translate("MainWindow", "-", None))
        self.nextForecastLabel.setText(_translate("MainWindow", "-", None))
        self.hydraulicsTitleLabel.setText(_translate("MainWindow", "Hydraulics", None))
        self.menu_Project.setTitle(_translate("MainWindow", "&Project", None))
        self.menuSimulation.setTitle(_translate("MainWindow", "Simulation", None))
        self.menuWindow.setTitle(_translate("MainWindow", "Window", None))
        self.actionImport_Seismic_Data.setText(_translate("MainWindow", "&Import Seismic Data...", None))
        self.actionView_Data.setText(_translate("MainWindow", "View Data", None))
        self.actionStart_Simulation.setText(_translate("MainWindow", "Start Simulation", None))
        self.actionPause_Simulation.setText(_translate("MainWindow", "Pause Simulation", None))
        self.actionStop_Simulation.setText(_translate("MainWindow", "Stop Simulation", None))
        self.actionShow_GR.setText(_translate("MainWindow", "Catalog Statistics", None))
        self.actionImport_Hydraulic_Data.setText(_translate("MainWindow", "Import Hydraulic Data...", None))
        self.actionOpen_Project.setText(_translate("MainWindow", "&Open Project...", None))
        self.actionNew_Project.setText(_translate("MainWindow", "New Project...", None))
        self.actionForecasts.setText(_translate("MainWindow", "Forecasts", None))

from plots import SeismicityPlotWidget, HydraulicsPlotWidget
import images_rc
