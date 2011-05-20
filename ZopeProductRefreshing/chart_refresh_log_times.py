#!/usr/bin/python

import sys, os, re
from pychartdir import *


def parseFile(filepath, packagename, max_cutoff=5.0):
    f = file(filepath)
    times = []
    for line in f.xreadlines():
        if line.startswith(packagename):
            time = float(line.split(':')[1])
            if time > max_cutoff:
                print "Skipping:", repr(line)
                continue
            times.append(time)
    
    return times

def chartTimes(times, packagename="Package"):
    data = times
    print max(times)

    #The labels for the line chart
    labels = []
    
    #Create a XYChart object of size 500 x 320 pixels, with a pale purpule
    #(0xffccff) background, a black border, and 1 pixel 3D border effect.
    c = XYChart(600, 420, 0xffccff, 0x0, 1)

    #Set the plotarea at (55, 45) and of size 420 x 210 pixels, with white
    #background. Turn on both horizontal and vertical grid lines with light grey
    #color (0xc0c0c0)
    c.setPlotArea(55, 55, 520, 310, 0xffffff, -1, -1, 0xc0c0c0, -1)
    
    #Add a legend box at (55, 25) (top of the chart) with horizontal layout. Use 8
    #pts Arial font. Set the background and border color to Transparent.
    #c.addLegend(55, 25, 0, "", 8).setBackground(Transparent)
    
    #Add a title box to the chart using 13 pts Times Bold Italic font. The text is
    #white (0xffffff) on a purple (0x800080) background, with a 1 pixel 3D border.
    c.addTitle("Refresh times %s"%packagename, "timesb.ttf", 13, 0xffffff
               ).setBackground(0x800080, -1, 1)

    #Add a title to the y axis
    c.yAxis().setTitle("Seconds")

    #Set the labels on the x axis. Rotate the font by 90 degrees.
    c.xAxis().setLabels(labels).setFontAngle(90)

    #Add a line layer to the chart
    lineLayer = c.addLineLayer()

    #Add the data to the line layer using light brown color (0xcc9966) with a 7
    #pixel square symbol
    lineLayer.addDataSet(data, 0xcc9966, "Server Utilization"
                   )#.setDataSymbol(SquareSymbol, 7)

    #Set the line width to 2 pixels
    lineLayer.setLineWidth(1)

    #Add a trend line layer using the same data with a dark green (0x008000) color.
    #Set the line width to 2 pixels
    c.addTrendLayer(data, 0x8000, "Trend Line").setLineWidth(2)

    #output the chart
    outto = os.path.join(os.path.curdir, "refresh_times-%s.png"%packagename)
    c.makeChart(outto)
    print outto


def _err(s):
    print >>sys.stderr, s
    
def _grr(return_value=1):
    this_file = os.path.basename(__file__)
    _err("USAGE: %s file.log Package" % this_file)
    return return_value

def averageBundleTimes(times, cutoff):
    new = []
    t = 0
    subnew = []
    for i, item in enumerate(times):
        if (i+1) % cutoff == 0:
            new.append(t / len(subnew))
            subnew = []
            t = 0
        else:
            t += item
            subnew.append(item)

    return new
        
def run():
    args = sys.argv[1:]
    
    if len(args) < 2:
        _err("Not two arguments")
        return _grr(1)
    elif not os.path.isfile(args[0]):
        _err("First argument not a file")
        return _grr(2)
    
    max_cutoff = 5.0
    if len(args)==3:
        max_cutoff = float(args[2])
    
    times = parseFile(args[0], args[1], max_cutoff=max_cutoff)
    
    if len(times) > 1000:
        times = averageBundleTimes(times, 4)
        
    if not times:
        _err("No times for package %s" % args[1])
        return _grr(3)

    chartTimes(times, args[1])
    
    return 0
    
    
if __name__=='__main__':
    sys.exit(run())

