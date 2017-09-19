#v.0.1.0
# -*- coding: utf-8 -*-

import os, time
from datetime import datetime
import _strptime # have to do to use strptime due to python bug
from ..common.fileops import readFile, checkPath
from ..common.xlogger import Logger


class objectConfig():
    def __init__( self, addon ):
        preamble     = '[Weather Station-SenseHAT]'
        logdebug     = addon.getSetting( "logging" )
        self.LW = Logger( preamble=preamble, logdebug=logdebug )
        self.P_RAPID = int( addon.getSetting( "rapid_pressure" ) )
        self.P_REGULAR = int( addon.getSetting( "regular_pressure" ) )
        self.P_DELTATIME = int( addon.getSetting( "p_deltatime" ) )
        self.ADJUSTTEMP = addon.getSetting( "adjust_senseHAT" )
        self.LOGDATEFORMAT = "%Y-%m-%d %H:%M:%S,%f"

        
    def getSensorData( self, sensorfolder='', tempscale='°C' ):
        loglines = []
        sensordata = []
        f_loglines, alldata = readFile( os.path.join( sensorfolder, 'sensordata.log' ) )
        self.LW.log( f_loglines )
        data_array = alldata.splitlines()
        try:
            last = data_array[-1]
        except IndexError:
            last = ''
        if last:
            all_values = last.split('\t')
            all_values.pop(0) #removes the unneeded date field from the sensor file
            for one_value in all_values:
                s_info = one_value.split(':')
                if s_info[0].endswith('Temp'):
                    sensordata.append( [s_info[0], self._convert_temp( s_info[1], tempscale )] )
                elif s_info[0].endswith('Humidity'):
                    sensordata.append( [s_info[0], s_info[1] + '%'] )
                elif s_info[0].endswith('Pressure'):
                    sensordata.append( [s_info[0], self._convert_pressure( s_info[1], tempscale )] )
                else:
                    sensordata.append( [s_info[0], s_info[1]] )
            sensordata.append( ['PressureTrend', self._get_pressure_trend( data_array )] )
            self.LW.log( ['returning sensor data'] )
            self.LW.log( sensordata )
        return sensordata

        
    def _convert_pressure( self, pressure, tempscale ):
        if tempscale == '°F':
            return '%.2f' % (float( pressure ) * 0.0295301) + ' inHg'
        else:
            return pressure + ' mbar'
    
    
    def _convert_temp( self, temperature, tempscale ):
        if tempscale == '°C':
            return temperature
        elif tempscale == '°F':
            return str( int( (float( temperature ) * 9/5) + 32 ) )
        elif tempscale == 'K':
            return str( int( float( temperature ) + 273.15 ) )
        elif tempscale == '°Ré':
            return str( int( float( temperature ) * 4/5 ) )
        elif tempscale == '°Ra':
            return str( int( (float( temperature ) * 273.15) * 9/5 ) )
        elif tempscale == '°Rø':
            return str( int( (float( temperature ) * 21/40) + 7.5 ) )
        elif tempscale == '°De':
            return str( int( (100 - float( temperature )) * 3/2 ) )
        elif tempscale == '°N':
            return str( int( (float( temperature ) * 0.33) ) )
        else:
            return temperature


    def _get_pressure_compare_lines( self, data_array ):
        try:
            last = data_array[-1]
            n_last = data_array[-2]
        except IndexError:
            last = ''
            n_last = ''
        if not (last and n_last):
            return '', ''
        last_values = last.split('\t')
        n_last_values = n_last.split('\t')
        # doing the date conversions this way due to bug in the version of python in Kodi
        # the shorter method worked fine in an external script
        try:
            last_time = datetime.strptime(last_values[0].rstrip(), self.LOGDATEFORMAT)
        except TypeError:
            last_time = datetime(*(time.strptime(last_values[0].rstrip(), self.LOGDATEFORMAT)[0:6]))
        try:
            n_last_time = datetime.strptime(n_last_values[0].rstrip(), self.LOGDATEFORMAT)
        except TypeError:
            n_last_time = datetime(*(time.strptime(n_last_values[0].rstrip(), self.LOGDATEFORMAT)[0:6]))
        tdelta = last_time - n_last_time
        target_seconds = self.P_DELTATIME * 60
        try:
            target = data_array[-int( target_seconds/tdelta.total_seconds() )]
        except IndexError:
            target = data_array[0]
        return last, target        


    def _get_pressure_trend( self, data_array ):
        current, previous = self._get_pressure_compare_lines( data_array )
        self.LW.log( ['current is ' + current] )
        self.LW.log( ['previous is ' + previous] )
        try:
            current_pressure = int( current.split('\t')[3].split(':')[1] )
            previous_pressure = int( previous.split('\t')[3].split(':')[1] )
        except IndexError:
            current_pressure = 0
            previous_pressure = 0
        diff = current_pressure - previous_pressure
        if diff < 0:
            direction = 'falling'
        else:
            direction = 'rising'
        if abs( diff ) >= self.P_RAPID:
            return 'rapidly ' + direction
        elif abs( diff ) >= self.P_REGULAR:
            return direction
        return 'steady'
