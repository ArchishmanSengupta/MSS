# -*- coding: utf-8 -*-
"""

    mslib.msui._tests.test_mss_pyui
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to tests msui.mss_pyui

    This file is part of mss.

    :copyright: Copyright 2017 Joern Ungermann
    :copyright: Copyright 2017-2021 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""


import sys
import mock
import os
from urllib.request import urlopen
from PyQt5 import QtWidgets, QtTest
from mslib import __version__
from mslib._tests.constants import ROOT_DIR
import mslib.msui.mss_pyui as mss_pyui
from mslib._tests.utils import ExceptionMock
from mslib.plugins.io.text import load_from_txt, save_to_txt
from mslib.plugins.io.flitestar import load_from_flitestar


class Test_MSS_AboutDialog():
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.window = mss_pyui.MSS_AboutDialog()

    def test_milestone_url(self):
        with urlopen(self.window.milestone_url) as f:
            text = f.read()
        pattern = f'value="is:closed milestone:{__version__[:-1]}"'
        assert pattern in text.decode('utf-8')

    def teardown(self):
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()


class Test_MSS_ShortcutDialog():
    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)
        self.main_window = mss_pyui.MSSMainWindow()
        self.main_window.show()
        self.shortcuts = mss_pyui.MSS_ShortcutsDialog()

    def teardown(self):
        self.shortcuts.hide()
        self.main_window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_shortcuts_present(self):
        assert self.shortcuts.treeWidget.topLevelItemCount() == 1


class Test_MSSSideViewWindow(object):
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "samples", "flight-tracks")
    save_csv = os.path.join(ROOT_DIR, "example.csv")
    save_ftml = os.path.join(ROOT_DIR, "example.ftml")
    save_ftml = save_ftml.replace('\\', '/')
    save_txt = os.path.join(ROOT_DIR, "example.txt")

    def setup(self):
        self.application = QtWidgets.QApplication(sys.argv)

        self.window = mss_pyui.MSSMainWindow()
        self.window.create_new_flight_track()
        self.window.show()
        QtWidgets.QApplication.processEvents()
        QtTest.QTest.qWaitForWindowExposed(self.window)
        QtWidgets.QApplication.processEvents()

    def teardown(self):
        for i in range(self.window.listViews.count()):
            self.window.listViews.item(i).window.hide()
        self.window.hide()
        QtWidgets.QApplication.processEvents()
        self.application.quit()
        QtWidgets.QApplication.processEvents()

    def test_no_updater(self):
        assert not hasattr(self.window, "updater")

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_app_start(self, mockbox):
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_new_flightrack(self, mockbox):
        assert self.window.listFlightTracks.count() == 1
        self.window.actionNewFlightTrack.trigger()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_topview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTopView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_sideview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionSideView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_tableview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionTableView.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0
        assert self.window.listViews.count() == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_linearview(self, mockbox):
        assert self.window.listViews.count() == 0
        self.window.actionLinearView.trigger()
        self.window.listViews.itemActivated.emit(self.window.listViews.item(0))
        QtWidgets.QApplication.processEvents()
        assert self.window.listViews.count() == 1
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_about(self, mockbox):
        self.window.actionAboutMSUI.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_config(self, mockbox):
        self.window.actionConfigurationEditor.trigger()
        QtWidgets.QApplication.processEvents()
        self.window.config_editor.close()
        assert mockbox.critical.call_count == 0

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    def test_open_shotcut(self, mockbox):
        self.window.actionShortcuts.trigger()
        QtWidgets.QApplication.processEvents()
        assert mockbox.critical.call_count == 0

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_ftml)
    def test_plugin_ftml_saveas(self, mocksave):
        assert self.window.listFlightTracks.count() == 1
        assert mocksave.call_count == 0
        self.window.last_save_directory = ROOT_DIR
        self.window.actionSaveActiveFlightTrackAs.trigger()
        QtWidgets.QApplication.processEvents()
        assert mocksave.call_count == 1
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=os.path.join(sample_path, u"example.csv"))
    def test_plugin_csv_read(self, mockopen):
        assert self.window.listFlightTracks.count() == 1
        assert mockopen.call_count == 0
        self.window.last_save_directory = self.sample_path
        self.window.actionImportFlightTrackCSV()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_csv)
    def test_plugin_csv_write(self, mocksave):
        assert self.window.listFlightTracks.count() == 1
        assert mocksave.call_count == 0
        self.window.last_save_directory = ROOT_DIR
        self.window.actionExportFlightTrackCSV()
        assert mocksave.call_count == 1
        assert os.path.exists(self.save_csv)
        os.remove(self.save_csv)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=os.path.join(sample_path, u"example.txt"))
    def test_plugin_txt_read(self, mockopen):
        self.window.add_import_filter("_TXT", "txt", load_from_txt)
        assert self.window.listFlightTracks.count() == 1
        assert mockopen.call_count == 0
        self.window.last_save_directory = self.sample_path
        self.window.actionImportFlightTrack_TXT()
        assert mockopen.call_count == 1
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2

    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_txt)
    def test_plugin_txt_write(self, mocksave):
        self.window.add_export_filter("_TXT", "txt", save_to_txt)
        self.window.last_save_directory = ROOT_DIR
        self.window.actionExportFlightTrack_TXT()
        assert mocksave.call_count == 1
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 1
        assert os.path.exists(self.save_txt)
        os.remove(self.save_txt)

    @mock.patch("mslib.msui.mss_pyui.get_open_filename",
                return_value=os.path.join(sample_path, u"flitestar.txt"))
    def test_plugin_flitestar(self, mockopen):
        self.window.last_save_directory = self.sample_path
        self.window.add_import_filter("_FliteStar", "txt", load_from_flitestar)
        assert self.window.listFlightTracks.count() == 1
        self.window.actionImportFlightTrack_FliteStar()
        QtWidgets.QApplication.processEvents()
        assert self.window.listFlightTracks.count() == 2
        assert mockopen.call_count == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox")
    @mock.patch("mslib.msui.mss_pyui.config_loader",
                return_value={"Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]})
    def test_add_plugins(self, mockopen, mockbox):
        assert len(self.window.menuImport_Flight_Track.actions()) == 1
        assert len(self.window.menuExport_Active_Flight_Track.actions()) == 1
        assert len(self.window._imported_plugins) == 0
        assert len(self.window._exported_plugins) == 0
        self.window.add_plugins()
        assert len(self.window._imported_plugins) == 1
        assert len(self.window._exported_plugins) == 1
        assert len(self.window.menuImport_Flight_Track.actions()) == 2
        assert len(self.window.menuExport_Active_Flight_Track.actions()) == 2
        assert mockbox.critical.call_count == 0

        with mock.patch("importlib.import_module", new=ExceptionMock(Exception()).raise_exc):
            self.window.add_plugins()
            assert mockbox.critical.call_count == 2
        with mock.patch("mslib.msui.mss_pyui.MSSMainWindow.add_import_filter",
                        new=ExceptionMock(Exception()).raise_exc):
            self.window.add_plugins()
            assert mockbox.critical.call_count == 4

        self.window.remove_plugins()
        assert len(self.window.menuImport_Flight_Track.actions()) == 1
        assert len(self.window.menuExport_Active_Flight_Track.actions()) == 1

    @mock.patch("PyQt5.QtWidgets.QMessageBox.critical")
    @mock.patch("PyQt5.QtWidgets.QMessageBox.warning", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.information", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("PyQt5.QtWidgets.QMessageBox.question", return_value=QtWidgets.QMessageBox.Yes)
    @mock.patch("mslib.msui.mss_pyui.get_save_filename", return_value=save_ftml)
    @mock.patch("mslib.msui.mss_pyui.get_open_filename", return_value=save_ftml)
    def test_flight_track_io(self, mockload, mocksave, mockq, mocki, mockw, mockbox):
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert mocki.call_count == 1
        self.window.actionNewFlightTrack.trigger()
        self.window.listFlightTracks.setCurrentRow(0)
        assert self.window.listFlightTracks.count() == 2
        tmp_ft = self.window.active_flight_track
        self.window.active_flight_track = self.window.listFlightTracks.currentItem().flighttrack_model
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert mocki.call_count == 2
        self.window.last_save_directory = self.sample_path
        self.window.actionSaveActiveFlightTrack.trigger()
        self.window.actionSaveActiveFlightTrack.trigger()
        self.window.active_flight_track = tmp_ft
        self.window.actionCloseSelectedFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 1
        self.window.actionOpenFlightTrack.trigger()
        assert self.window.listFlightTracks.count() == 2
        assert os.path.exists(self.save_ftml)
        os.remove(self.save_ftml)
