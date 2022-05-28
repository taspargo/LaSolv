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
Created on Nov 26, 2016

@author: Tom Spargo
'''

#import inspect
import wx
import sys

gVerbose = 4
        
#def myName(self):
    #return self.__class__.__name__ + '::' + inspect.stack()[1][3]

def myName():
    import traceback
    return traceback.extract_stack(None, 2)[0][2]

# 1    Not used
# 2    Maxnodes exceeded.                        CCircuit, addNode
# 3    Source node 1 doesn't exist.              CCircuit, renumberSourceNodes
# 4    Source node 2 doesn't exist in source.    CCircuit, renumberSourceNodes
# 5    Added element with 'label' not found      CCircuit, getAddedNodeElementIndex
# 6    Source with name 'label' not found        CCircuit, calculateVorIEqn
# 7    Source element type not v or i            CCircuit, calculateVorIEqn
# 8    Computer type not found                   CFileReader, init
# 9    Solve element not found                   CFileReader, init
# 10   Unknown element found                     CFileReader, init
# 11   None-numeric node name                    CFileReader, parseSolveStatement
# 12   Incorrect solve statement syntax          CFileReader, parseSolveStatement
# 13   Solve statement with unknown source, V/I  CFileReader, parseSolveStatement
# 14   Solve statement with unknown source, I/V  CFileReader, parseSolveStatement
# 15   Solve statement, unknown 1st source, I/I  CFileReader, parseSolveStatement
# 16   Solve statement, unknown 2nd source, I/I  CFileReader, parseSolveStatement
# 17   Two node element without enough nodes     CFileReader, parseElement
# 18   2-node element, non-numeric nodes         CFileReader, parseElement
# 19   4-node element, non-numeric nodes         CFileReader, parseElement
# 20   F or H element, not enough nodes          CFileReader, parseElement
# 21   F or H element, c-sense isn't an IVS      CFileReader, parseElement
# 22   F or H element, non-numeric nodes         CFileReader, parseElement
# 23   F or H element uses a non-existent source CFileReader, verifyIVSforFandHElements
# 24   Unknown element found                     CLinearEquations, fillAMatrix
# 25   Reorder equations failed                  CLinearEquations, solveEquations
# 26   Matrix cannot be solved                   eqnSolver, calling solveEquations
# 27   Could not find file/path                  CFileReader, init
# 28   Permissions error when opening file       eqnSolver, createHTMLFile
# 29   Unknown relational operator in simplify   CFileReader

err_list = [ \
"Zero",
"Not used",
"Maxnodes exceeded.",                        
"Source node 1 doesn't exist.",             
"Source node 2 doesn't exist in source.",  
"Added element with 'label' not found",   
"Source not found" ,     
"Source element type not v or i",
"Computer type not found",
"Solve element not found",
"Unknown element found",
"None-numeric node name",
"Incorrect solve statement syntax",
"Solve statement with unknown source, V/I",
"Solve statement with unknown source, I/V",
"Solve statement, unknown 1st source, I/I",
"Solve statement, unknown 2nd source, I/I",
"Two node element without enough nodes",
"2-node element, non-numeric nodes",
"4-node element, non-numeric nodes",
"F or H element, not enough nodes",
"F or H element, c-sense isn't an IVS",
"F or H element, non-numeric nodes",
"F or H element uses a non-existent source",
"Unknown element found",
"Reorder equations failed",
"Matrix cannot be solved",
"Could not find file/path",
"Permissions error when opening file",
"Unknown relational operator in simplify statement"]

def myExit(code, ):
    if code <= len(err_list):
        print('*'*(len(err_list[code])+11))
        print("Error #{0:2}: {1:}".format(code, err_list[code]))
        print('*'*(len(err_list[code])+11))
    else:
        print('?'*50)
        print('An unknown error occurred: code', code)
        print('?'*50)
        
    wx.MessageBox("Error #{0:2}: {1:}".format(code, err_list[code]), \
                  'Error', wx.OK | wx.ICON_ERROR)
    #sys.exit(code)


