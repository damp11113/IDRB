"""
This file is part of IDRB Project.

IDRB Project is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDRB Project is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDRB Project.  If not, see <https://www.gnu.org/licenses/>.
"""

import dearpygui.dearpygui as dpg

from utils import *

librarylist = ["Opencv (opencv.org)", "PyOgg (TeamPyOgg) (Forked)", "DearPyGui (hoffstadt)", "LZ4 (python-lz4)", "PyAudio (CristiFati)"]

def window(self):
    with dpg.window(label="IDRB", width=320, height=520, no_close=True):
        dpg.add_button(label="Server info", callback=lambda: dpg.configure_item("Serverinfowindow", show=True),
                       tag="serverinfobutton", show=False)
        dpg.add_button(label="disconnect", callback=self.disconnectserver, tag="disconnectbutton", show=False)
        dpg.add_text("not connect", tag="serverstatus", color=(255, 0, 0))
        dpg.add_combo([], label="Channel", tag="mediachannelselect", default_value="Main Channel", show=False,
                      callback=self.changechannel)
        dpg.add_spacer()
        dpg.add_image("station_logo", show=False, tag="station_logo_config")
        dpg.add_text("Logo not available", tag="logostatus", color=(255, 0, 0), show=False)
        dpg.add_text("", tag="RDSinfo", show=False)

        with dpg.child_window(tag="connectservergroup", label="Server", use_internal_label=True, height=130):
            dpg.add_button(label="select server", tag="selectserverbutton", callback=self.pubserverselectopen)
            dpg.add_input_text(label="server ip", tag="serverip", default_value="localhost")
            dpg.add_input_int(label="port", tag="serverport", max_value=65535, default_value=6980)
            dpg.add_combo(["TCP", "ZeroMQ", "ZeroMQ (WS)"], label="protocol", tag="serverprotocol", default_value="TCP")
            dpg.add_button(label="connect", callback=self.connecttoserver, tag="connectbutton")

        dpg.add_spacer()
        dpg.add_button(label="More RDS info", callback=lambda: dpg.configure_item("RDSwindow", show=True),
                       tag="morerdsbutton", show=False)

    with dpg.window(label="IDRB RDS Info", tag="RDSwindow", show=False, width=250):
        with dpg.tab_bar():
            with dpg.tab(label="Program"):
                with dpg.child_window(label="Basic", use_internal_label=True, height=100):
                    dpg.add_text("PS: ...", tag="RDSPS")
                    dpg.add_text("PI: ...", tag="RDSPI")
                    dpg.add_text("RT: ...", tag="RDSRT")

                dpg.add_text("Time Local: ...", tag="RDSCTlocal")
                dpg.add_text("Time UTC: ...", tag="RDSCTUTC")
            with dpg.tab(label="EPG"):
                pass
            with dpg.tab(label="Images"):
                pass
            with dpg.tab(label="AS"):
                pass
            with dpg.tab(label="EOM"):
                pass

    with dpg.window(label="IDRB Server Info", tag="Serverinfowindow", show=False):
        dpg.add_text("Server: ...", tag="ServerNamedisp")
        dpg.add_text("Description: ...", tag="ServerDescdisp")
        dpg.add_text("Listener: ...", tag="ServerListener")

        # dpg.add_spacer()
        # dpg.add_simple_plot(label="Transfer Rates", autosize=True, height=250, width=500, tag="transferateplot")

    with dpg.window(label="IDRB About", tag="aboutwindow", show=False, no_resize=True):
        dpg.add_image("app_logo")
        dpg.add_spacer()
        dpg.add_text("IDRB (Internet Digital Radio Broadcasting System) Client")
        dpg.add_spacer()
        dpg.add_text(f"IDRB Client v1.6.2 Beta")
        dpg.add_spacer()

        desc = "IDRB is a novel internet radio broadcasting alternative that uses HLS/DASH/HTTP streams, transferring over TCP/IP. This system supports images and RDS (Dynamic update) capabilities, enabling the transmission of station information. Additionally, it allows for setting station logos and images. IDRB offers multi-broadcasting functionalities and currently supports the Opus codec, with plans to incorporate PCM, MP2/3, AAC/AAC+, and more in the future, ensuring low delay. If you find this project intriguing, you can support it at damp11113.xyz/support."

        dpg.add_text(limit_string_in_line(desc, 75))

        dpg.add_spacer()
        with dpg.table(header_row=True):
            # use add_table_column to add columns to the table,
            # table columns use slot 0
            dpg.add_table_column(label="Libraries")

            # add_table_next_column will jump to the next row
            # once it reaches the end of the columns
            # table next column use slot 1
            for i in librarylist:
                with dpg.table_row():
                    dpg.add_text(i)

        dpg.add_spacer(height=20)
        dpg.add_text(f"Copyright (C) 2023-2024 ThaiSDR All rights reserved. (GPLv3)")

    with dpg.window(label="IDRB Public Server", tag="pubserverselectwindow", show=False, modal=True, popup=True, height=500, width=1200):
        dpg.add_text("N/A", tag="pubserverselectstatus")
        dpg.add_input_text(hint="search server here", tag="serversearchinput")
        dpg.add_button(label="search", callback=lambda: self.pubserverselectsearch(dpg.get_value("serversearchinput")))
        with dpg.table(header_row=True, tag="pubserverlist"):
            dpg.add_table_column(label="IP")
            dpg.add_table_column(label="Server")
            dpg.add_table_column(label="Description")
            dpg.add_table_column(label="listeners")
        dpg.add_spacer()
        dpg.add_button(label="connect", callback=self.connecttoserverwithpubselect, tag="connectbuttonpubserverselect", show=False)


    with dpg.window(label="IDRB Evaluation", tag="evaluationwindow", show=False):
        with dpg.tab_bar():
            with dpg.tab(label="Audio"):
                with dpg.plot(label="FFT Spectrum", height=250, width=500):
                    # optionally create legend
                    dpg.add_plot_legend()

                    # REQUIRED: create x and y axes
                    dpg.add_plot_axis(dpg.mvXAxis, tag="x_axis_1", no_gridlines=True, label="Frequencies")
                    dpg.add_plot_axis(dpg.mvYAxis, tag="audioL_y_axis", no_gridlines=True)
                    dpg.add_plot_axis(dpg.mvYAxis, tag="audioR_y_axis", no_gridlines=True)

                    dpg.set_axis_limits("audioL_y_axis", 0, 2500000)
                    dpg.set_axis_limits("audioR_y_axis", 0, 2500000)

                    # series belong to a y axis
                    dpg.add_line_series([], [], label="Left Channel", parent="audioL_y_axis", tag="audioinfoleftplot")
                    dpg.add_line_series([], [], label="Right Channel", parent="audioR_y_axis", tag="audioinforightplot")

            with dpg.tab(label="Network"):
                dpg.add_text("NA", tag="codecbitratestatus", show=True)
                dpg.add_text("Buffer 0/0", tag="bufferstatus", show=True)
                with dpg.plot(label="Transfer Rates", height=250, width=500):
                    # optionally create legend
                    dpg.add_plot_legend()

                    # REQUIRED: create x and y axes
                    dpg.add_plot_axis(dpg.mvXAxis, tag="x_axis", no_gridlines=True)
                    dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis1", no_gridlines=True)
                    dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis2", no_gridlines=True)
                    dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis3", no_gridlines=True)

                    # series belong to a y axis
                    dpg.add_line_series([], [], label="All Data", parent="y_axis1", tag="transferatealldataplot")
                    dpg.add_line_series([], [], label="Audio Data", parent="y_axis2",
                                        tag="transferateaudiodataoncchannelplot")
                    dpg.add_line_series([], [], label="Images Data", parent="y_axis3",
                                        tag="transferateimagesoncchannelplot")


            with dpg.window(label="Password Required", tag="requestpasswordpopup", modal=True, no_resize=True,
                            no_close=True, no_move=True, show=False):
                dpg.add_text("This channel is encrypt! Please enter password for decrypt.")
                dpg.add_spacer()
                dpg.add_input_text(label="password", tag="requestpasswordinputpopup")
                dpg.add_spacer()
                dpg.add_button(label="confirm", callback=self.submitpassworddecrypt)

            with dpg.window(label="Config", tag="configwindow", show=False, width=500):
                dpg.add_text("Please restart software when configured")
                with dpg.tab_bar():
                    with dpg.tab(label="Audio"):
                        dpg.add_combo([], label="Output Device", tag="selectaudiooutputdevicecombo", callback=self.changeaudiodevice)
                    with dpg.tab(label="Network"):
                        dpg.add_input_int(label="Buffer Size", tag="buffersizeintinput", callback=self.changebuffersize)


def menubar(self):
    with dpg.viewport_menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Exit", callback=lambda: self.exit())
        with dpg.menu(label="View"):
            dpg.add_menu_item(label="Evaluation", callback=lambda: dpg.configure_item("evaluationwindow", show=True))
        with dpg.menu(label="Settings"):
            dpg.add_menu_item(label="Config", callback=lambda: dpg.configure_item("configwindow", show=True))
            dpg.add_spacer()
            dpg.add_menu_item(label="StyleEditor", callback=dpg.show_style_editor)

        with dpg.menu(label="Help"):
            dpg.add_menu_item(label="About", callback=lambda: dpg.configure_item("aboutwindow", show=True))
