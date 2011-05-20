##
## RememberYourFriends
## (c) Fry-IT, www.fry-it.com
## <mail@peterbe.com>
##

# python
import os, re, sys

from pychartdir import *


# Product
from Tables import Reminders
from I18N import _
from Constants import *
from Utils import debug


class StatsBase(Reminders):
    
    def getMostRemindersSentStats(self, howmany=None):
        """ return who's sent most reminders ever """
        if howmany is not None:
            howmany = int(howmany)
        return self._getMostRemindersSentStats(limit=howmany)
    
    def ChartRemindersSent(self, width=445, height=250, cumulative=False,
                           REQUEST=None):
        """ return the imagedata of a single line chart """
        
        counts = []
        counts_cum = []
        labels = []
        first_reminder = self._getFirstReminderSent()
        last_reminder = self._getLastReminderSent()
        days_difference = int(last_reminder.add_date - first_reminder.add_date)
        #weeks = days_difference / 7
        months = days_difference / 30
        
        sql_count = self.SQLCountSentRemindersBetweenDates
        #for i in range(weeks):
        for i in range(int(months)):
            start = i * 7
            end = i * 30 + 30
            start_date = first_reminder.add_date + start
            end_date = first_reminder.add_date + end
            count = sql_count(start_date=start_date, end_date=end_date)[0].count
            counts.append(count)
            try:
                counts_cum.append(counts_cum[-1]+count)
            except IndexError:
                counts_cum.append(count)
            labels.append(str(end/30))
            
        #Create a XYChart object of size 500 x 300 pixels, with a pale yellow (0xffff80)
        #background, a black border, and 1 pixel 3D border effect
        c = XYChart(width, height, 0xffffff, 0xffffff, 0)

        #Set the plotarea at (55, 45) and of size 420 x 210 pixels, with white
        #background. Turn on both horizontal and vertical grid lines with light grey
        #color (0xc0c0c0)
        c.setPlotArea(55, 25, width-80, height-65, 0xffffff, -1, -1, 0xc0c0c0, -1)

        #Add a legend box at (55, 25) (top of the chart) with horizontal layout. Use 8
        #pts Arial font. Set the background and border color to Transparent.
        #c.addLegend(55, 25, 0, "", 8).setBackground(Transparent)

        #Add a title box to the chart using 11 pts Arial Bold Italic font. The text is
        #white (0xffffff) on a dark red (0x800000) background, with a 1 pixel 3D border.
        #title = "Number of reminders sent"
        #if cumulative:
        #    title = "Cumulative number of reminders sent"
        #c.addTitle(title, "arialbd.ttf", 10, 0x0
        # ) #.setBackground(0x800000, -1, 1)
   
        #Add a title to the y axis
        c.yAxis().setTitle("# sent reminders")

        #Set the labels on the x axis.
        c.xAxis().setLabels(labels)
        
        #Add a title to the x axis
        #c.xAxis().setTitle("weeks")
        c.xAxis().setTitle("months")

        #Add a line layer to the chart
        layer = c.addLineLayer2()
        
        #Set the default line width to 2 pixels
        layer.setLineWidth(2)

        if cumulative:
            layer.addDataSet(counts_cum, -1, "Total")
        else:
            layer.addDataSet(counts, -1, "Total")
        
        #print counts_cum
        
        if REQUEST:
            REQUEST.RESPONSE.setHeader('Content-Type', 'image/png')
        
        return c.makeChart2(PNG)
        
            
            
        
        
    
        
        

        
