#!/usr/bin/env python

'''
PySQM plotting program
____________________________

Copyright (c) Mireia Nievas <mnievas[at]ucm[dot]es>

This file is part of PySQM.

PySQM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PySQM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PySQM.  If not, see <http://www.gnu.org/licenses/>.
____________________________
'''

import os,sys
import ephem
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime,timedelta

# Read configuration

if __name__ != '__main__':
    import pysqm.settings as settings
    config = settings.GlobalConfig.config

    for directory in [\
        config.monthly_data_directory,\
        config.daily_graph_directory,\
        config.current_graph_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)


class Ephemerids(object):
    def __init__(self):
        from pysqm.common import define_ephem_observatory
        self.Observatory = define_ephem_observatory()

    def ephem_date_to_datetime(self,ephem_date):
        # Convert ephem dates to datetime
        date_,time_ = str(ephem_date).split(' ')
        date_ = date_.split('/')
        time_ = time_.split(':')

        return(datetime(\
            int(date_[0]),int(date_[1]),int(date_[2]),\
            int(time_[0]),int(time_[1]),int(time_[2])))

    def end_of_the_day(self,thedate):
        newdate = thedate+timedelta(days=1)
        newdatetime = datetime(\
            newdate.year,\
            newdate.month,\
            newdate.day,0,0,0)
        newdatetime = newdatetime-timedelta(hours=config._local_timezone)
        return(newdatetime)


    def calculate_moon_ephems(self,thedate):
        # Moon ephemerids
        self.Observatory.horizon = '0'
        self.Observatory.date = str(self.end_of_the_day(thedate))

        # Moon phase
        Moon = ephem.Moon()
        Moon.compute(self.Observatory)
        self.moon_phase = Moon.phase
        self.moon_maxelev = Moon.transit_alt # TODO: transit_alt deprecated, needs to be converted.

        try:
            float(self.moon_maxelev)
        except:
            # The moon has no culmination time for 1 day
            # per month, so there is no max altitude.
            # As a workaround, we use the previous day culmination.
            # The error should be small.

            # Set the previous day date
            thedate2 = thedate - timedelta(days=1)
            self.Observatory.date = str(self.end_of_the_day(thedate2))
            Moon2 = ephem.Moon()
            Moon2.compute(self.Observatory)
            self.moon_maxelev = Moon2.transit_alt

            # Recover the real date
            self.Observatory.date = str(self.end_of_the_day(thedate))

        # Moon rise and set
        self.moon_prev_rise = \
         self.ephem_date_to_datetime(self.Observatory.previous_rising(ephem.Moon()))
        self.moon_prev_set  = \
         self.ephem_date_to_datetime(self.Observatory.previous_setting(ephem.Moon()))
        self.moon_next_rise = \
         self.ephem_date_to_datetime(self.Observatory.next_rising(ephem.Moon()))
        self.moon_next_set  = \
         self.ephem_date_to_datetime(self.Observatory.next_setting(ephem.Moon()))

    def calculate_twilight(self,thedate,twilight=-18):
        '''
        Changing the horizon forces ephem to
        calculate different types of twilights:
        -6: civil,
        -12: nautical,
        -18: astronomical,
        '''
        self.Observatory.horizon = str(twilight)
        self.Observatory.date = str(self.end_of_the_day(thedate))

        try:
            ## Plotting only uses twilight_prev_set and twilight_next_rise
            # self.twilight_prev_rise = self.ephem_date_to_datetime(\
            # self.Observatory.previous_rising(ephem.Sun(),use_center=True)) 
            self.twilight_prev_set = self.ephem_date_to_datetime(\
            self.Observatory.previous_setting(ephem.Sun(),use_center=True))
            self.twilight_next_rise = self.ephem_date_to_datetime(\
            self.Observatory.next_rising(ephem.Sun(),use_center=True))
            # self.twilight_next_set = self.ephem_date_to_datetime(\
            # self.Observatory.next_setting(ephem.Sun(),use_center=True))
        # If you're north or south enough, night, day or the twilights might not exist. 
        # Here we are catching the root class of the exception hierarchy 
        # to catch NeverUpError or AlwaysUpError
        except ephem.CircumpolarError:
            # self.twilight_prev_rise = None
            self.twilight_prev_set = None
            self.twilight_next_rise = None
            # self.twilight_next_set = None 
            



class SQMData(object):
    # Split pre and after-midnight data

    class premidnight(object):
        pass

    class aftermidnight(object):
        pass

    class Statistics(object):
        pass

    def __init__(self,filename,Ephem):
        self.all_night_sb = []
        self.all_night_dt = []
        self.all_night_temp = []

        for variable in [\
         'utcdates','localdates','sun_altitudes',\
         'temperatures','tick_counts','frequencies',\
         'night_sbs','label_dates','sun_altitude']:
            setattr(self.premidnight,variable,[])
            setattr(self.aftermidnight,variable,[])

        self.load_rawdata(filename)
        self.process_rawdata(Ephem)
        self.check_number_of_nights()

    def extract_metadata(self,raw_data_and_metadata):
        from pysqm.common import format_value
        metadata_lines = [\
         line for line in raw_data_and_metadata \
         if format_value(line)[0]=='#']

        # Extract the serial number
        serial_number_line = [\
         line for line in metadata_lines \
         if 'SQM serial number:' in line][0]
        self.serial_number = format_value(serial_number_line.split(':')[-1])

    def check_validdata(self,data_line):
        from pysqm.common import format_value
        try:
            assert(format_value(data_line)[0]!='#')
            assert(format_value(data_line)[0]!='')
        except:
            return(False)
        else:
            return(True)

    def load_rawdata(self,filename):
        '''
        Open the file, read the data and close the file
        '''
        sqm_file = open(filename, 'r')
        raw_data_and_metadata = sqm_file.readlines()
        self.metadata = self.extract_metadata(raw_data_and_metadata)

        self.raw_data = [\
         line for line in raw_data_and_metadata \
         if self.check_validdata(line)==True]
        sqm_file.close()

    def process_datetimes(self,str_datetime):
        '''
        Get date and time in a str format
        Return as datetime object
        '''
        str_date,str_time = str_datetime.split('T')

        year  = int(str_date.split('-')[0])
        month = int(str_date.split('-')[1])
        day   = int(str_date.split('-')[2])

        # Time may be not complete. Workaround
        hour   = int(str_time.split(':')[0])
        try:
            minute = int(str_time.split(':')[1])
        except:
            minute = 0
            second = 0
        else:
            try:
                second = int(str_time.split(':')[2])
            except:
                second = 0

        return(datetime(year,month,day,hour,minute,second))

    def process_rawdata(self,Ephem):
        from pysqm.common import format_value_list
        '''
        Get the important information from the raw_data
        and put it in a more useful format

        Splits string read from file into columns, converts string formats into python binary formats.
        if data and timezone config disagree return 1 (and no data is processed)
        '''

        # Split rows on ";"
        self.raw_data = format_value_list(self.raw_data)

        # convert to Python data formats
        for k,line in enumerate(self.raw_data):
            # DateTime extraction
            utcdatetime = self.process_datetimes(line[0])
            localdatetime = self.process_datetimes(line[1])

            # Check that datetimes are corrent
            calc_localdatetime = utcdatetime+timedelta(hours=config._local_timezone)
            if (calc_localdatetime != localdatetime): 
                print("WARNING: Difference between localtime and utctime in data DO NOT MATCH configured timezone difference. Check config.py ")
                print("**** ABORT processing raw data ****")
                print("No data will be plotted")
                return 1

            # Set the datetime for astronomical calculations.
            Ephem.Observatory.date = ephem.date(utcdatetime)

            # Date in str format: 20130115
            label_date = str(localdatetime.date()).replace('-','')

            # Temperature
            temperature = float(line[2])
            # Counts
            tick_counts = float(line[3])
            # Frequency
            frequency   = float(line[4])
            # Night sky background
            night_sb    = float(line[5])
            try: config._plot_corrected_nsb
            except AttributeError: config._plot_corrected_data=False
            if (config._plot_corrected_data):
                night_sb += config._plot_corrected_data*config._offset_calibration
            # Define sun in pyephem
            Sun = ephem.Sun(Ephem.Observatory)

            self.premidnight.label_date=[]
            self.aftermidnight.label_dates=[]


            if localdatetime.hour > 12:
                self.premidnight.utcdates.append(utcdatetime)
                self.premidnight.localdates.append(localdatetime)
                self.premidnight.temperatures.append(temperature)
                self.premidnight.tick_counts.append(tick_counts)
                self.premidnight.frequencies.append(frequency)
                self.premidnight.night_sbs.append(night_sb)
                self.premidnight.sun_altitude.append(Sun.alt)
                if label_date not in self.premidnight.label_dates:
                    self.premidnight.label_dates.append(label_date)
            else:
                self.aftermidnight.utcdates.append(utcdatetime)
                self.aftermidnight.localdates.append(localdatetime)
                self.aftermidnight.temperatures.append(temperature)
                self.aftermidnight.tick_counts.append(tick_counts)
                self.aftermidnight.frequencies.append(frequency)
                self.aftermidnight.night_sbs.append(night_sb)
                self.aftermidnight.sun_altitude.append(Sun.alt)
                if label_date not in self.aftermidnight.label_dates:
                    self.aftermidnight.label_dates.append(label_date)

            # Data for the complete night
            self.all_night_dt.append(utcdatetime) # Must be in UTC!
            self.all_night_sb.append(night_sb)
            self.all_night_temp.append(temperature)

    def check_number_of_nights(self):
        '''
        Check that the number of nights is exactly 1 and
        extract it to a new variable self.Night.
        Needed for the statistics part of the analysis and
        to make the plot.
        '''

        if np.size(self.premidnight.localdates)>0:
            self.Night = np.unique([DT.date() \
             for DT in self.premidnight.localdates])[0]
        elif np.size(self.aftermidnight.localdates)>0:
            self.Night = np.unique([(DT-timedelta(hours=12)).date() \
             for DT in self.aftermidnight.localdates])[0]
        else:
            print('Warning, No Night detected.')
            self.Night = None

    def data_statistics(self,Ephem):
        '''
        Make statistics on the data.
        Useful to summarize night conditions.
        '''
        def select_bests(values,number):
            return(np.sort(values)[::-1][0:int(number)])

        def fourier_filter(array,nterms):
            '''
            Make a fourier filter for the first nterms terms.
            '''
            array_fft = np.fft.fft(array)
            # Filter data
            array_fft[nterms:]=0
            filtered_array = np.fft.ifft(array_fft)
            return(filtered_array)
    
        def window_smooth(x,window_len=10,window='hanning'):
            # http://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
            if x.ndim != 1: raise ValueError("smooth requires 1-d arrays")
            if x.size < window_len: raise ValueError("size(input) < window_size")
            if window_len < 3: return x
            if not window in ['flat','hanning','hamming','bartlett','blackman']:
                raise ValueError("Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
            s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
            if window == 'flat': #moving average
                w=np.ones(window_len,'d')
            else:
                w=eval('np.'+window+'(window_len)')
            y=np.convolve(w/w.sum(),s,mode='valid')
            return(y)

        if Ephem.twilight_prev_set is not None and Ephem.twiligth_next_rise is not None:
            astronomical_night_filter = (\
            (np.array(self.all_night_dt)>Ephem.twilight_prev_set)*\
            (np.array(self.all_night_dt)<Ephem.twilight_next_rise))
        else: # No astronomical twilight at current location (poor lads)
            astronomical_night_filter = (0)

        if np.sum(astronomical_night_filter)>10:
            self.astronomical_night_sb = \
                 np.array(self.all_night_sb)[astronomical_night_filter]
            self.astronomical_night_temp = \
                 np.array(self.all_night_temp)[astronomical_night_filter]
        else:
            print(\
             'Warning, < 10 points in astronomical night, '+\
             'using the whole night data instead')
            self.astronomical_night_sb = np.array(self.all_night_sb)
            self.astronomical_night_temp = np.array(self.all_night_temp)

        Stat = self.Statistics
        #with self.Statistics as Stat:
        # Complete list
        Stat.mean   = np.mean(self.astronomical_night_sb)
        Stat.median = np.median(self.astronomical_night_sb)
        Stat.std    = np.median(self.astronomical_night_sb)
        Stat.number = np.size(self.astronomical_night_sb)
        # Only the best 1/25.
        Stat.bests_number = 1+Stat.number/25
        Stat.bests_mean   = np.mean(select_bests(self.astronomical_night_sb,Stat.bests_number))
        Stat.bests_median = np.median(select_bests(self.astronomical_night_sb,Stat.bests_number))
        Stat.bests_std    = np.std(select_bests(self.astronomical_night_sb,Stat.bests_number))
        Stat.bests_err    = Stat.bests_std*1./np.sqrt(Stat.bests_number)

        Stat.model_nterm = 1+int(Stat.number/25)
        #data_smooth = fourier_filter(self.astronomical_night_sb,nterms=Stat.model_nterm)
        data_smooth = window_smooth(self.astronomical_night_sb,
                window_len=Stat.model_nterm)
        min_length = min(len(data_smooth),len(self.astronomical_night_sb))
        data_residuals = self.astronomical_night_sb[:min_length]-data_smooth[:min_length]
        Stat.data_model_abs_meandiff = np.mean(np.abs(data_residuals))
        Stat.data_model_sum_squareresiduals = np.sum(data_residuals**2)

        # Other interesting data
        Stat.min_temperature = np.min(self.astronomical_night_temp)
        Stat.max_temperature = np.max(self.astronomical_night_temp)


class Plot(object):
    def __init__(self,Data,Ephem):
        plt.clf() # plt.hold(True/False) is deprecated
        Data = self.prepare_plot(Data,Ephem)

        try: config.full_plot
        except: config.full_plot = False
        if (config.full_plot):
            self.make_figure(thegraph_altsun=True,thegraph_time=True)
            self.plot_data_sunalt(Data,Ephem)
        else:
            self.make_figure(thegraph_altsun=False,thegraph_time=True)

        self.plot_data_time(Data,Ephem)

        self.plot_moonphase(Ephem)
        self.plot_twilight(Ephem)

    def plot_moonphase(self,Ephem):
        '''
        shade the period of time for which the moon is above the horizon
        '''
        if Ephem.moon_next_rise > Ephem.moon_next_set:
            # We need to divide the plotting in two phases
            #(pre-midnight and after-midnight)
            self.thegraph_time.axvspan(\
             Ephem.moon_prev_rise+timedelta(hours=config._local_timezone),\
             Ephem.moon_next_set+timedelta(hours=config._local_timezone),\
              edgecolor='#d62728',facecolor='#d62728', alpha=0.1,clip_on=True)
        else:
            self.thegraph_time.axvspan(\
             Ephem.moon_prev_rise+timedelta(hours=config._local_timezone),\
             Ephem.moon_prev_set+timedelta(hours=config._local_timezone),\
             edgecolor='#d62728',facecolor='#d62728', alpha=0.1,clip_on=True)
            self.thegraph_time.axvspan(\
             Ephem.moon_next_rise+timedelta(hours=config._local_timezone),\
             Ephem.moon_next_set+timedelta(hours=config._local_timezone),\
             edgecolor='#d62728',facecolor='#d62728', alpha=0.1,clip_on=True)

    def plot_twilight(self,Ephem):
        '''
        Plot vertical lines on the astronomical twilights
        '''
        # If twilight is not defined, skip plotting
        if Ephem.twilight_prev_set is None or Ephem.twilight_next_rise is None: 
            return 

        self.thegraph_time.axvline(\
         Ephem.twilight_prev_set+timedelta(hours=config._local_timezone),\
         color='black', ls='dashdot', lw=1, alpha=0.75, clip_on=True)
        self.thegraph_time.axvline(\
         Ephem.twilight_next_rise+timedelta(hours=config._local_timezone),\
         color='black', ls='dashdot', lw=1, alpha=0.75, clip_on=True)

    def make_subplot_sunalt(self,twinplot=0):
        '''
        Make a subplot.
        If twinplot = 0, then this will be the only plot in the figure
        if twinplot = 1, this will be the first subplot
        if twinplot = 2, this will be the second subplot
        '''
        if twinplot == 0:
            self.thegraph_sunalt = self.thefigure.add_subplot(1,1,1)
        else:
            self.thegraph_sunalt = self.thefigure.add_subplot(2,1,twinplot)


        self.thegraph_sunalt.set_title(\
         'Sky Brightness ('+config._device_shorttype+'-'+\
         config._observatory_name+')\n',fontsize='x-large')
        self.thegraph_sunalt.set_xlabel('Solar altitude (deg)',fontsize='large')
        self.thegraph_sunalt.set_ylabel('Sky Brightness (mag/arcsec$\mathregular{^2}$)',fontsize='medium')

        # Auxiliary plot (Temperature)
        '''
        self.thegraph_sunalt_temp = self.thegraph_sunalt.twinx()
        self.thegraph_sunalt_temp.set_ylim(-10, 50)
        self.thegraph_sunalt_temp.set_ylabel('Temperature (C)',fontsize='medium')
        '''

        # format the ticks (frente a alt sol)
        tick_values = range(config.limits_sunalt[0],config.limits_sunalt[1]+5,5)
        tick_marks  = np.multiply([deg for deg in tick_values],np.pi/180.0)
        tick_labels = [str(deg) for deg in tick_values]

        self.thegraph_sunalt.set_xticks(tick_marks)
        self.thegraph_sunalt.set_xticklabels(tick_labels)
        self.thegraph_sunalt.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
        self.thegraph_sunalt.grid(True,which='major',
                alpha=0.2,color='k',ls='',lw=0.5)
        self.thegraph_sunalt.grid(True,which='minor',
                alpha=0.2,color='k',ls='solid',lw=0.5)

    def make_subplot_time(self,twinplot=0):
        '''
        Make a subplot.
        If twinplot == 0, then this will be the only plot in the figure
        if twinplot == 1, this will be the first subplot
        if twinplot == 2, this will be the second subplot
        '''
        if twinplot == 0:
            self.thegraph_time = self.thefigure.add_subplot(1,1,1)
        else:
            self.thegraph_time = self.thefigure.add_subplot(2,1,twinplot)

        if config._local_timezone<0:
            UTC_offset_label = '-'+str(abs(config._local_timezone))
        elif config._local_timezone>0:
            UTC_offset_label = '+'+str(abs(config._local_timezone))
        else: UTC_offset_label = ''

        #self.thegraph_time.set_title('Sky Brightness (SQM-'+config._observatory_name+')',\
        # fontsize='x-large')
        self.thegraph_time.set_xlabel('Time (UTC'+UTC_offset_label+')',fontsize='large')
        self.thegraph_time.set_ylabel('Sky Brightness (mag/arcsec$\mathregular{^2}$)',fontsize='medium')

        # Auxiliary plot (Temperature)
        '''
        self.thegraph_time_temp = self.thegraph_time.twinx()
        self.thegraph_time_temp.set_ylim(-10, 50)
        self.thegraph_time_temp.set_ylabel('Temperature (C)',fontsize='medium')
        '''

        # format the ticks (vs time)
        daylocator    = mdates.HourLocator(byhour=[4,20])
        hourlocator   = mdates.HourLocator()
        dayFmt        = mdates.DateFormatter('%d %b %Y')
        hourFmt       = mdates.DateFormatter('%H')

        self.thegraph_time.xaxis.set_major_locator(daylocator)
        self.thegraph_time.xaxis.set_major_formatter(dayFmt)
        self.thegraph_time.xaxis.set_minor_locator(hourlocator)
        self.thegraph_time.xaxis.set_minor_formatter(hourFmt)
        self.thegraph_time.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))

        self.thegraph_time.xaxis.set_tick_params(which='major', pad=15)
        self.thegraph_time.format_xdata = mdates.DateFormatter('%Y-%m-%d_%H:%M:%S')
        self.thegraph_time.grid(True,which='major',
                alpha=0.2,color='k',ls='',lw=0.5)
        self.thegraph_time.grid(True,which='minor',
                alpha=0.2,color='k',ls='solid',lw=0.5)

    def make_figure(self,thegraph_altsun=True,thegraph_time=True):
        # Make the figure and the graph
        if thegraph_time==False:
            self.thefigure = plt.figure(figsize=(7,3.))
            self.make_subplot_sunalt(twinplot=0)
        elif thegraph_altsun==False:
            self.thefigure = plt.figure(figsize=(7,3.))
            self.make_subplot_time(twinplot=0)
        else:
            self.thefigure = plt.figure(figsize=(7,6.))
            self.make_subplot_sunalt(twinplot=1)
            self.make_subplot_time(twinplot=2)

        # Adjust the space between plots
        plt.subplots_adjust(hspace=0.35)


    def prepare_plot(self,Data,Ephem):
        '''
        Warning! Multiple night plot implementation is pending.
        Until the support is implemented, check that no more than 1 night
        is used
        '''

        # Mean datetime
        dts       = Data.all_night_dt
        mean_dt   = dts[0]+np.sum(np.array(dts)-dts[0])/np.size(dts)
        sel_night = (mean_dt - timedelta(hours=12)).date()

        Data.premidnight.filter = np.array(\
         [Date.date()==sel_night for Date in Data.premidnight.localdates])
        Data.aftermidnight.filter = np.array(\
         [(Date-timedelta(days=1)).date()==sel_night\
           for Date in Data.aftermidnight.localdates])

        return(Data)

    def plot_data_sunalt(self,Data,Ephem):
        '''
        Plot NSB data vs Sun altitude
        '''
        # Plot the data
        TheData = Data.premidnight
        if np.size(TheData.filter)>0:
            self.thegraph_sunalt.plot(\
             np.array(TheData.sun_altitude)[TheData.filter],\
             np.array(TheData.night_sbs)[TheData.filter],color='#2ca02c')
            '''
            self.thegraph_sunalt.plot(\
             np.array(TheData.sun_altitude)[TheData.filter],\
             np.array(TheData.temperatures)[TheData.filter],color='#9467bd',alpha=0.5))
            '''
        TheData = Data.aftermidnight
        if np.size(TheData.filter)>0:
            self.thegraph_sunalt.plot(\
             np.array(TheData.sun_altitude)[TheData.filter],\
             np.array(TheData.night_sbs)[TheData.filter],color='#1f77b4')
            '''
            self.thegraph_sunalt.plot(\
             np.array(TheData.sun_altitude)[TheData.filter],\
             np.array(TheData.temperatures)[TheData.filter],color='#9467bd',alpha=0.5))
            '''

        # Make limits on data range.
        self.thegraph_sunalt.set_xlim([\
         config.limits_sunalt[0]*np.pi/180.,\
         config.limits_sunalt[1]*np.pi/180.])
        self.thegraph_sunalt.set_ylim(config.limits_nsb)

        premidnight_label = str(Data.premidnight.label_dates).replace('[','').replace(']','')
        aftermidnight_label = str(Data.aftermidnight.label_dates).replace('[','').replace(']','')

        self.thegraph_sunalt.text(0.00,1.015,\
         config._device_shorttype+'-'+config._observatory_name+' '*5+'Serial #'+str(Data.serial_number),\
         color='0.25',fontsize='small',fontname='monospace',\
         transform = self.thegraph_sunalt.transAxes)

        self.thegraph_sunalt.text(0.75,0.92,'PM: '+premidnight_label,\
         color='#2ca02c',fontsize='small',transform = self.thegraph_sunalt.transAxes)
        self.thegraph_sunalt.text(0.75,0.84,'AM: '+aftermidnight_label,\
         color='#1f77b4',fontsize='small',transform = self.thegraph_sunalt.transAxes)

        '''
        if np.size(Data.Night)==1:
            self.thegraph_sunalt.text(0.75,1.015,'Moon: %d%s (%d%s)' \
             %(Ephem.moon_phase, "%", Ephem.moon_maxelev*180./np.pi,"$^\mathbf{o}$"),\
             color='#d62728',fontsize='small',fontname='monospace',\
             transform = self.thegraph_sunalt.transAxes)
        '''

    def plot_data_time(self,Data,Ephem):
        '''
        Plot NSB data vs Sun altitude
        '''

        # Plot the data (NSB and temperature)
        TheData = Data.premidnight
        if np.size(TheData.filter)>0:
            self.thegraph_time.plot(\
             np.array(TheData.localdates)[TheData.filter],\
             np.array(TheData.night_sbs)[TheData.filter],color='#2ca02c')
            '''
            self.thegraph_time_temp.plot(\
             np.array(TheData.localdates)[TheData.filter],\
             np.array(TheData.temperatures)[TheData.filter],color='#9467bd',alpha=0.5)
            '''


        TheData = Data.aftermidnight
        if np.size(TheData.filter)>0:
            self.thegraph_time.plot(\
             np.array(TheData.localdates)[TheData.filter],\
             np.array(TheData.night_sbs)[TheData.filter],color='#1f77b4')
            '''
            self.thegraph_time_temp.plot(\
             np.array(TheData.localdates)[TheData.filter],\
             np.array(TheData.temperatures)[TheData.filter],color='#9467bd',alpha=0.5)
            '''

        # Vertical line to mark 0h
        self.thegraph_time.axvline(\
         Data.Night+timedelta(days=1),
         color='black', alpha=0.75,lw=1,ls='solid',clip_on=True)

        # Set the xlimit for the time plot.
        if np.size(Data.premidnight.filter)>0:
            begin_plot_dt = Data.premidnight.localdates[-1]
            begin_plot_dt = datetime(\
             begin_plot_dt.year,\
             begin_plot_dt.month,\
             begin_plot_dt.day,\
             config.limits_time[0],0,0)
            end_plot_dt = begin_plot_dt+timedelta(\
             hours=24+config.limits_time[1]-config.limits_time[0])
        elif np.size(Data.aftermidnight.filter)>0:
            end_plot_dt = Data.aftermidnight.localdates[-1]
            end_plot_dt = datetime(\
             end_plot_dt.year,\
             end_plot_dt.month,\
             end_plot_dt.day,\
             config.limits_time[1],0,0)
            begin_plot_dt = end_plot_dt-timedelta(\
             hours=24+config.limits_time[1]-config.limits_time[0])
        else:
            print('Warning: Cannot calculate plot limits')
            return(None)

        self.thegraph_time.set_xlim(begin_plot_dt,end_plot_dt)
        self.thegraph_time.set_ylim(config.limits_nsb)

        premidnight_label = str(Data.premidnight.label_dates).replace('[','').replace(']','')
        aftermidnight_label = str(Data.aftermidnight.label_dates).replace('[','').replace(']','')

        self.thegraph_time.text(0.00,1.015,\
         config._device_shorttype+'-'+config._observatory_name+' '*5+'Serial #'+str(Data.serial_number),\
         color='0.25',fontsize='small',fontname='monospace',\
         transform = self.thegraph_time.transAxes)

        if np.size(Data.Night)==1:
            self.thegraph_time.text(0.75,1.015,'Moon: %d%s (%d%s)' \
             %(Ephem.moon_phase, "%", Ephem.moon_maxelev*180./np.pi,"$^\mathbf{o}$"),\
             color='black',fontsize='small',fontname='monospace',\
             transform = self.thegraph_time.transAxes)

    def save_figure(self,output_filename):
        self.thefigure.savefig(output_filename, bbox_inches='tight',dpi=150)

    def show_figure(self):
        plt.show(self.thefigure)

    def close_figure(self):
        plt.close('all')


def save_stats_to_file(Night,NSBData,Ephem):
    from pysqm.common import set_decimals
    '''
    Save statistics to file
    '''

    Stat = NSBData.Statistics

    Header = \
     '# Summary statistics for '+str(config._device_shorttype+'_'+config._observatory_name)+'\n'+\
     '# Description of columns (CSV file):\n'+\
     '# Col 1: Date\n'+\
     '# Col 2: Total measures\n'+\
     '# Col 3: Number of Best NSB measures\n'+\
     '# Col 4: Median of best N NSBs (mag/arcsec2)\n'+\
     '# Col 5: Err in the median of best N NSBs (mag/arcsec2)\n'+\
     '# Col 6: Window size for the smoothing function\n'+\
     '# Col 7: Mean of Abs diff of NSBs data - fourier model (mag/arcsec2)\n'+\
     '# Col 8: Min Temp (C) between astronomical twilights\n'+\
     '# Col 9: Max Temp (C) between astronomical twilights\n\n'
     #'# Col 6: Number of terms of the low-freq fourier model\n'+\

    formatted_data = \
        str(Night)+';'+\
        str(Stat.number)+';'+\
        str(Stat.bests_number)+';'+\
        set_decimals(Stat.bests_median,4)+';'+\
        set_decimals(Stat.bests_err,4)+';'+\
        str(Stat.model_nterm)+';'+\
        set_decimals(Stat.data_model_abs_meandiff,4)+';'+\
        set_decimals(Stat.min_temperature,1)+';'+\
        set_decimals(Stat.max_temperature,1)+\
        '\n'

    statistics_filename = \
     config.summary_data_directory+'/Statistics_'+\
     str(config._device_shorttype+'_'+config._observatory_name)+'.dat'

    print('Writing statistics file')

    def safe_create_file(filename):
        if not os.path.exists(filename):
            open(filename, 'w').close()

    def read_file(filename):
        thefile = open(filename,'r')
        content = thefile.read()
        thefile.close()
        return(content)

    def write_file(filename,content):
        thefile = open(filename,'w')
        thefile.write(content)
        thefile.close()

    def append_file(filename,content):
        thefile = open(filename,'a')
        thefile.write(content)
        thefile.close()

    # Create file if not exists
    safe_create_file(statistics_filename)

    # Read the content
    stat_file_content = read_file(statistics_filename)

    # If the file doesnt have a proper header, add it to the beginning

    def valid_line(line):
        if '#' in line:
            return False
        elif line.replace(' ','')=='':
            return False
        else:
            return True

    if Header not in stat_file_content:
        stat_file_content = [line for line in stat_file_content.split('\n') \
         if valid_line(line)]
        stat_file_content = '\n'.join(stat_file_content)
        stat_file_content = Header+stat_file_content
        write_file(statistics_filename,stat_file_content)

    # Remove any previous statistic for the given Night in the file
    if str(Night) in stat_file_content:
        stat_file_content = [line for line in stat_file_content.split('\n') \
         if str(Night) not in line]
        stat_file_content = '\n'.join(stat_file_content)
        write_file(statistics_filename,stat_file_content)

    # Append to the end of the file
    append_file(statistics_filename,formatted_data)


def make_plot(input_filename=None,send_emails=False,write_stats=False):
    '''
    Main function (allows to execute the program
    from within python.
     - Extracts the NSB data from a given data file
     - Performs statistics
     - Save statistics to file
     - Create the plot
    '''

    print('Plotting photometer data ...')

    if (input_filename is None):
        input_filename  = config.current_data_directory+\
         '/'+config._device_shorttype+'_'+config._observatory_name+'.dat'

    # Define the observatory in ephem
    Ephem = Ephemerids()

    # Get and process the data from input_filename
    NSBData = SQMData(input_filename,Ephem)

    # Moon and twilight ephemerids.
    Ephem.calculate_moon_ephems(thedate=NSBData.Night)
    Ephem.calculate_twilight(thedate=NSBData.Night)

    # Calculate data statistics
    NSBData.data_statistics(Ephem)

    # Write statiscs to file?
    if write_stats==True:
        save_stats_to_file(NSBData.Night,NSBData,Ephem)

    # Plot the data and save the resulting figure
    NSBPlot = Plot(NSBData,Ephem)

    output_filenames = [\
        str("%s/%s_%s.png" %(config.current_data_directory,\
            config._device_shorttype,config._observatory_name)),\
        str("%s/%s_120000_%s-%s.png" \
            %(config.daily_graph_directory, str(NSBData.Night).replace('-',''),\
              config._device_shorttype, config._observatory_name))\
    ]

    for output_filename in output_filenames:
        NSBPlot.save_figure(output_filename)

    # Close figure
    NSBPlot.close_figure()

    if send_emails == True:
        import pysqm.email
        night_label = str(datetime.date.today()-timedelta(days=1))
        pysqm.email.send_emails(night_label=night_label,Stat=NSBData.Statistics)

'''
The following code allows to execute plot.py as a standalone program.
'''
if __name__ == '__main__':
    # Exec the main program
    import pysqm.settings as settings
    InputArguments = settings.ArgParser(inputfile=True)
    configfilename = InputArguments.config
    try:
        settings.GlobalConfig.read_config_file(configfilename)
        config = settings.GlobalConfig.config
        make_plot(input_filename=InputArguments.input,\
          send_emails=False,write_stats=True)
    except:
        raise
        print("Error: The arguments you provided are invalid")
        InputArguments.print_help()














