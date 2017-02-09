"""Table view of the MSUI.

********************************************************************************

   Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
   Copyright 2011-2014 Marc Rautenhaus

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

********************************************************************************

This file is part of the Mission Support System User Interface (MSUI).

See the reference documentation, Supplement, for details on the
implementation.

To better understand of the code, look at the 'ships' example from
chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
Definitive Guide to PyQt Programming' (Mark Summerfield).

AUTHORS:
========

* Marc Rautenhaus (mr)

"""

# standard library imports
import functools
import logging
import random
import string
import pyproj
from mslib.mss_util import config_loader
from mslib.msui import MissionSupportSystemDefaultConfig as mss_default
from mslib.msui import hexagon_dockwidget as hex
# related third party imports
from mslib.msui.mss_qt import QtGui, QtCore, QtWidgets, QString

# local application imports
from mslib.msui.mss_qt import ui_tableview_window as ui
from mslib.msui import flighttrack as ft
from mslib.msui.viewwindows import MSSViewWindow
from mslib.msui.performance_settings import MSS_PerformanceSettingsDialog

#
# USER INTERFACE CLASS FlightPlanTableView
#


class MSSTableViewWindow(MSSViewWindow, ui.Ui_TableViewWindow):
    """Implements the table view of the flight plan. Data comes from a
       flight track data model.
    """

    name = "Table View"

    def __init__(self, parent=None, model=None):
        """
        """
        super(MSSTableViewWindow, self).__init__(parent)
        self.setupUi(self)

        self.setFlightTrackModel(model)
        self.tableWayPoints.setItemDelegate(ft.WaypointDelegate(self))

        toolitems = ["(select to open control)", "Hexagon Control"]
        self.cbTools.clear()
        self.cbTools.addItems(toolitems)

        # Dock windows [Hexagon].
        self.docks = [None]

        # Connect slots and signals.
        self.btAddWayPointToFlightTrack.clicked.connect(self.addWayPoint)
        self.btDeleteWayPoint.clicked.connect(self.removeWayPoint)
        self.btInvertDirection.clicked.connect(self.invertDirection)
        self.btViewPerformance.clicked.connect(self.settingsDlg)
        # Tool opener.
        self.cbTools.currentIndexChanged.connect(self.openTool)

        self.resizeColumns()

    def settingsDlg(self):
        dlg = MSS_PerformanceSettingsDialog(parent=self, settings_dict=self.waypoints_model.performance_settings)
        dlg.setModal(True)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.waypoints_model.performance_settings = dlg.get_settings()
            self.waypoints_model.update_distances(0)
            self.waypoints_model.saveSettings()
            self.waypoints_model.dataChanged.emit(
                self.waypoints_model.index(0, 0), self.waypoints_model.index(0, 0))
            self.resizeColumns()
        dlg.destroy()

    def openTool(self, index):
        """Slot that handles requests to open tool windows.
        """
        index = self.controlToBeCreated(index)
        if index >= 0:
            if index == 0:
                title = "Hexagon Control"
                widget = hex.HexagonControlWidget(view=self)
            else:
                raise IndexError("invalid control index (%i)" % index)
            self.createDockWidget(index, title, widget)

    def invertDirection(self):
        self.waypoints_model.invertDirection()

    def addWayPoint(self):
        """Handler for button <btAddWayPointToFlightTrack>. Adds a new waypoint
           behind the currently selected waypoint.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        lonlat = 0, 0
        if not index.isValid():
            row = 0
            flightlevel = 0
        else:
            row = index.row() + 1
            flightlevel = self.waypoints_model.waypointData(row - 1).flightlevel
            if row <  len(self.waypoints_model.allWaypointData()):
                wp_prev = self.waypoints_model.waypointData(row - 1)
                wp_next = self.waypoints_model.waypointData(row)
                gc = pyproj.Geod(ellps="WGS84")  # a=40e6, b=40e6)
                lonlat = gc.npts(wp_prev.lon, wp_prev.lat, wp_next.lon, wp_next.lat, 3)[1]

        self.waypoints_model.insertRows(
            row, waypoints=[ft.Waypoint(lat=round(lonlat[1], 2), lon=round(lonlat[0], 2), flightlevel=flightlevel)])

        index = self.waypoints_model.index(row, 0)
        tableView = self.tableWayPoints
        tableView.setFocus()
        tableView.setCurrentIndex(index)
        # tableView.edit(index)
        tableView.resizeRowsToContents()

    def confirm_delete_waypoint(self, row):
        """Open a QMessageBox and ask the user if he really wants to
           delete the waypoint at index <row>.

        Returns TRUE if the user confirms the deletion.

        If the flight track consists of only two points deleting a waypoint
        is not possible. In this case the user is informed correspondingly.
        """
        wps = self.waypoints_model.allWaypointData()
        if len(wps) < 3:
            QtWidgets.QtMessageBox.warning(
                None, "Remove waypoint",
                "Cannot remove waypoint, the flight track needs to consist of at least two points.")
            return False
        else:
            waypoint = wps[row]
            return QtWidgets.QtMessageBox.question(
                None, "Remove waypoint",
                "Remove waypoint at %.2f/%.2f, flightlevel %.2f?" % (waypoint.lat, waypoint.lon, waypoint.flightlevel),
                QtWidgets.QtMessageBox.Yes | QtWidgets.QtMessageBox.No) == QtWidgets.QtMessageBox.Yes

    def removeWayPoint(self):
        """Handler for button <btDeleteWayPoint>. Deletes the currently selected
           waypoint.
        """
        tableView = self.tableWayPoints
        index = tableView.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        # Let the user confirm the deletion.
        if self.confirm_delete_waypoint(row):
            self.waypoints_model.removeRows(row)

    def resizeColumns(self):
        for column in range(self.waypoints_model.columnCount()):
            self.tableWayPoints.resizeColumnToContents(column)

    def setFlightTrackModel(self, model):
        """Set the QAbstractItemModel instance that the table displays.
        """
        super(MSSTableViewWindow, self).setFlightTrackModel(model)
        self.tableWayPoints.setModel(self.waypoints_model)

    def viewPerformance(self):
        """Slot to toggle the view mode of the table between 'USER' and
           'PERFORMANCE'.
        """
        # Restore the original button face colour (as inherited from this window's palette).
        self.btViewPerformance.setPalette(self.palette())
        self.tableWayPoints.setPalette(self.palette())
        self.btAddWayPointToFlightTrack.setEnabled(True)
        self.btDeleteWayPoint.setEnabled(True)
        self.resizeColumns()


def _main():
    # Log everything, and send it to stderr.
    # See http://docs.python.org/library/logging.html for more information
    # on the Python logging module.
    # NOTE: http://docs.python.org/library/logging.html#formatter-objects
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s (%(module)s.%(funcName)s): %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    import sys

    # Create an initital flight track.
    initial_waypoints = [ft.Waypoint(flightlevel=0, location="EDMO", comments="take off OP"),
                         ft.Waypoint(48.10, 10.27, 200),
                         ft.Waypoint(52.32, 09.21, 200),
                         ft.Waypoint(52.55, 09.99, 200),
                         ft.Waypoint(flightlevel=0, location="Hamburg", comments="landing HH")]

    waypoints_model = ft.WaypointsTableModel(QString(""))
    waypoints_model.insertRows(0, rows=len(initial_waypoints),
                               waypoints=initial_waypoints)

    application = QtWidgets.QApplication(sys.argv)
    window = MSSTableViewWindow(model=waypoints_model)
    window.show()

    sys.exit(application.exec_())

if __name__ == "__main__":
    _main()
