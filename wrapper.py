#!/usr/bin/env python3

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
from scipy import interpolate
import pandas as pd
import subprocess
from io import StringIO

import holoviews as hv
from bokeh.models import HoverTool


class WrapperTool:
    def __init__(self):
        super(WrapperTool, self).__init__()
        hv.extension('bokeh', 'matplotlib')

    def sdds_to_pandas(self, *colnames, file='results/beamline.mag'):
        try:
            cmd_str = self.names_parser(colnames)
            out = subprocess.Popen(['sdds2stream', file, cmd_str, '-pipe=out'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = out.communicate()
            output = stdout.decode('utf-8').splitlines()
            data = StringIO("\n".join(output))
            data_frame = pd.read_csv(data, names=colnames, delim_whitespace=True)

            return data_frame
        except Exception as exp:
            print(exp)
            return None

    def sdds_par(self, file='results/twiss.twi', par='nux'):
        out = subprocess.Popen(['sdds2stream', file, '-par=' + par],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        return float(stdout)

    def acc_view(self, *colnames, file='results/xyz.sdds'):
        try:
            df_xyz = self.sdds_to_pandas(*colnames, file=file)
            theta = interpolate.interp1d(df_xyz.s.values, df_xyz.theta.values, fill_value=(0, 0), bounds_error=False)
            x0 = interpolate.interp1d(df_xyz.s.values, df_xyz.X.values, fill_value=(0, 0), bounds_error=False)
            z0 = interpolate.interp1d(df_xyz.s.values, df_xyz.Z.values, fill_value=(0, 0), bounds_error=False)

            data_frame = self.sdds_to_pandas('ElementName', 's', 'Profile')
            s = data_frame.s.values
            nx = np.cos(theta(s))
            nz = -np.sin(theta(s))
            element_width = 0.5  # m
            data_frame['X'] = x0(s) + element_width * data_frame['Profile'] * nx
            data_frame['Z'] = z0(s) + element_width * data_frame['Profile'] * nz

            dim_x = hv.Dimension('X', label='X', unit='m')
            dim_z = hv.Dimension('Z', label='Z', unit='m', range=(-32, +32))
            curve = hv.Curve((data_frame.Z, data_frame.X), kdims=dim_z, vdims=dim_x)
            curve.opts(width=700, height=400, show_frame=False, show_title=False, xaxis=None, yaxis=None,
                       show_grid=True, tools=['box_zoom', 'pan', 'wheel_zoom', 'reset'], color='blue', alpha=0.3)
            return curve
        except Exception as exp:
            print(exp)
            return None

    @staticmethod
    def names_parser(names):
        cmd_str = '-col='
        for elem in names:
            cmd_str = cmd_str + elem + ','
        return cmd_str[:-1]

    @staticmethod
    def plot_structure(data_frame):
        dim_s = hv.Dimension('s', unit='m', label="s")
        hover = HoverTool(tooltips="@ElementName")
        mag = hv.Curve(data_frame, kdims=dim_s, vdims=['Profile', 'ElementName'], group='mag')
        mag.opts(width=700, height=70, show_frame=False, show_title=False, xaxis=None, yaxis=None, show_grid=True,
                 tools=['box_zoom', 'pan', 'wheel_zoom', 'reset', hover], color='black', alpha=0.3)
        return mag

    @staticmethod
    def plot_function(data_frame, func='betax', color='red', label='βx'):
        dim_s = hv.Dimension('s', unit='m', label="s")
        data = getattr(data_frame, func)
        dim_y = hv.Dimension(func, unit='m', label=label, range=(0, 1.1 * max(data)))
        curve = hv.Curve((data_frame.s, data), label=label, kdims=dim_s, vdims=dim_y)
        curve.opts(color=color, alpha=0.7, line_width=3, width=700, height=300, show_grid=True,
                   tools=['box_zoom', 'pan', 'wheel_zoom', 'reset'])
        return curve


if __name__ == "__main__":
    app = QApplication(['Twiss'])
    w = WrapperTool()
    sys.exit(app.exec_())
