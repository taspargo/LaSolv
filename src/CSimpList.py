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
Created on Sep 29, 2019

@author: Thomas
'''
import Support

class Relation(object):
    '''
    Holds a < or > relationship that used to simplify the 
    solution equation
    '''
    
    def __init__(self, first, relation, second):
        # Always put simpList entries in the order [smaller, bigger]
        if relation in ['<', '<<']:
            self.small = first
            self.big = second
        elif relation in ['>', '>>']:
            self.small = second
            self.big = first
        else:
            print(Support.myName(), \
                  ': Simplify command with unknown operator:', relation)
            Support.myExit(29)
    
    def getRelation(self):
        return [self.small, self.big]
    
    def getSmaller(self):
        return self.small
    
    def getBigger(self):
        return self.big
    
    def printRelation(self):
        print( self.getSmaller()+" << "+self.getBigger())
        #print('printRelation: smaller=', self.getSmaller(), '  bigger=', self.getBigger())
        #print(' {0:s} << {1:s}'.format( self.getSmaller, self.getBigger))

class SimpList(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.simpList = []
    
    def getSimpList(self):
        return self.simpList
    
    def appendRelation(self, rel):
        self.simpList.append(rel)
        
    def appendRelationSB(self, smaller, bigger):
        rel = Relation(smaller, bigger)
        self.simpList.append(rel)
        
    def size(self):
        return len(self.simpList)
        
    def printSimpList(self):
        for it in self.simpList:
            it.printRelation()
        
        
