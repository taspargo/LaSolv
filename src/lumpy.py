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
    if dtype is 'f':
        return [0.0]*length
    elif dtype is 'c':
        return [complex(0.0, 0.0)]*length

