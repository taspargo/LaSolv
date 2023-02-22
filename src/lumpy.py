"""
Copyright 2019 Thomas Spargo

This file is part of LaSolv.

    LaSolv is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    LaSolv is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with LaSolv.  If not, see <https://www.gnu.org/licenses/>.
"""
'''
Created on Feb 16, 2019

@author: Thomas
'''

from math import log10
import Support

def arange(start, stop, step):
    if start < stop and step < 0:
        print(Support.myName(), "'step' needs to be > 0 when start > stop:", step ) 
    if start > stop and step > 0:
        print(Support.myName(), "'step' needs to be < 0 when start < stop:", step ) 
    
    length = int((stop-start)/step+1)
    ans = [0.0]*length
    num = start
    for x in range(length):
        ans[x] = num 
        num += step
    return ans
    
def geomSpace(start, stop, length):
    if start < 0:
        print(Support.myName(), "'Start' should be > 0:", start ) 
    if stop < 0:
        print(Support.myName(), "'Stop' should be > 0:", stop ) 
    
    if length < 0:
        print(Support.myName(), "'Length' should be > 0:", length ) 

    if start > stop:
        print(Support.myName(), "'Start' should be < 'Stop':" )
        print(Support.myName(), "    Start=", start)
        print(Support.myName(), "     Stop=", stop)

    ratio = 10**(log10(stop/start)/(length-1))
    ans = [0.0]*length
    ans[0] = float(start)
    for x in range(length-1):
        ans[x+1] = ans[x]*ratio
    return ans

def zeros(length, dtype):
    if dtype == 'f':
        return [0.0]*length
    elif dtype == 'c':
        return [complex(0.0, 0.0)]*length

