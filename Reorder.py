"""  
Copyright 2020 Thomas Spargo

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
Created on Mar 15, 2020

@author: thomas
'''

from sympy import pprint, zeros, Matrix
from itertools import permutations
import Support

def pp(m):
    pprint(m) 
    
def pp_num(m):
    sz = m.shape[0]
    m_1 = m.row_insert(0, Matrix([list(range(sz))]))
    m_2 = m_1.col_insert(0, Matrix(list(range(-1,sz))))
    pprint(m_2)

def get_mat_ij(i, j, mat, inx_list):
    #print("get_mat_ij: i={0:d} j={1:d}".format(i, j))
    if i > len(inx_list)-1 or j > len(inx_list)-1:
        print("get_mat_ij: sz(mat)=", mat.shape, "  inx_list=", inx_list, \
              "  i=", i, "  j=", j)
    x = inx_list[i]
    y = inx_list[j]
    #print("get_mat_ij:                x={0:d} y={1:d}".format(x, y))
    return mat[x, y]

def set_mat_ij(i, j, value, mat, inx_list):
    if i > len(inx_list)-1 or j > len(inx_list)-1:
        print("set_mat_ij: sz(mat)=", mat.shape, "  inx_list=", inx_list, \
              "  i=", i, "  j=", j)
    x = inx_list[i]
    y = inx_list[j]
    if x > len(inx_list)-1 or y > len(inx_list)-1:
        print("set_mat_ij: sz(mat)=", mat.shape, "  inx_list=", inx_list, \
              "  x=", x, "  y=", y)
    mat[x, y] = value
    
def find_pins(mat, inx_list):
    ''' Search rows & columns for ones that have only one non-zero element.'''
    sz = len(inx_list)
    dict_h = dict()
    dict_v = dict()
    for i in range(sz):  # count down
        hz_count = 0
        non_hz = -1
        vz_count = 0
        non_vz = -1
        if Support.gVerbose > 2:
            print()
            print("findSingles: Checking ", i)
        for j in range(sz):  # going across
            if get_mat_ij(i, j, mat, inx_list) == 0:
                hz_count = hz_count + 1
            else:
                non_hz = j

            if get_mat_ij(j, i, mat, inx_list) == 0:
                vz_count = vz_count + 1
            else:
                non_vz = j
                
        if Support.gVerbose > 3: print("   Row {0:d}, z_count={1:d}, non_z={2:d}".format(i, hz_count, non_hz))
        # If the count is one less than the size, we're found a row/col with just one none-zero
        # element. Save it in a dictionary, key is the row it's in, the value is which row 
        # it needs to be in.
        if hz_count == sz-1:
            if Support.gVerbose > 2: print("        Match, adding to row list")
            dict_h[i] = non_hz
            
        if Support.gVerbose > 3: print("Column {0:d}, z_count={1:d}, non_z={2:d}".format(i, vz_count, non_vz))
        if vz_count == sz-1:
            if Support.gVerbose > 2: print("        Match, adding to column list")
            dict_v[non_vz] = i
    
    if Support.gVerbose > 1: 
        print("findSingles: dict_h=", dict_h)
        print("findSingles: dict_v=", dict_v)
    for k in dict_v:
        dict_h[k] = dict_v[k]
    if Support.gVerbose > 3: print("findSingles: Merged=", dict_h)
    # dict_h is in the inx_list map, convert that back into the plain matrix indexes.
    new_dict = dict()
    for k, v in dict_h.items():
        new_dict[inx_list[k]] = inx_list[v]
    if Support.gVerbose > 1:
        print("find_pins: mapped pin list:", dict_h)
        print("find_pins:  unmapped  list:", new_dict)
    return new_dict

# From a swap array 1..sz, make a swap matrix sz x sz
def makeSwapMatrix(swp_ary):
    
    sz = len(swp_ary)
    swp_mat = zeros(sz, sz)

    for i in range(sz):
        swp_mat[i, swp_ary[i]] = 1.0
    return swp_mat

def find_inx_value(inx_list, v):
    for i in range(len(inx_list)-1):
        if inx_list[i] == v:
            return i
    return -1

# Update the index list based on the rows that are now pinned
# Delete the index that has inx_list[n]=v for each v. 
# Must do the largest numbered rows first.
def apply_pins_inx_list(pins, inx_list):
    for value in sorted(pins.values(), reverse=True):
        if Support.gVerbose > 2: print("app_pins_inx_list: deleting index ", value)
        inx = find_inx_value(inx_list, value)
        inx_list.pop(inx)
        #inx_list.pop(value)
    if Support.gVerbose > 3: print("app_pins_inx_dict: new inx_list = ", inx_list)
    return inx_list

# Update the reorder array based on the pinned rows.
# For each pin, swap the from/to rows in the reorder array
def apply_pins_r_array(pins, swp_ary):
    db = 0
    if Support.gVerbose > 1: print("app_pins_r_ary: swap=", swp_ary)
    if Support.gVerbose > 1: print("app_pins_r_ary: pins=", pins)
    for k, v in pins.items():
        if db: print("    app_pins_r_ary: swap[{0:d}] = {1:d}, swap[{2:d}]={3:d}".format(v, k, k, v) )
        # This can be done with 'a, b = b, a' but I don't know for sure if it's 
        # always implemented the same way, and in this case the order matters.
        # b, a = a, b would give a different answer.
        if swp_ary[v] != k:
            save = swp_ary[v]
            swp_ary[v] = swp_ary[k]
            swp_ary[k] = save
            if db: print("    app_pins_r_ary: swp=", swp_ary)

    if Support.gVerbose > 1: print("app_pins_r_ary: now swp=", swp_ary)
    return swp_ary
    
def print_pin_list(plist):
    print("ppl: Pin list")
    if len(plist) != 0:
        for k, v in plist.items():
            print("ppl:  Row {0:d} moves to row {1:d}".format(k, v))
    else:
        print("    is empty!")

# For debugging, not needed.
def blank_pinned_rc(pins, m, inx_list):
    if Support.gVerbose > 0: print("shape=", m.shape, "  inx_list=", inx_list)
    for v in pins.values():
        for i in range(len(inx_list)):
            j = inx_list[i]
            if Support.gVerbose > 2: print("blanking:  {2:d} [{0:d}, {1:d}] and [{1:d}, {0:d}]".format(j, v, i))
            m[j, v] = 99
            m[v, j] = 99
    print('after blanking:')
    pp_num(m)
    return m

def diagonalNonzero(mat, perm, inx_list):
    """Returns True if the diagonal mapped using 'useRow' is non-zero"""
    nonZero = True
    for num in range(len(perm)):
        if mat[inx_list[num], inx_list[perm[num]]] == 0.0:
            nonZero = False
            break
    return nonZero

# Look through the matrix column by column and row by row looking for
#     rows/columns that have only one non-zero element. These are called
#     'pins' since they must be in a certain row for the matrix to be solvable.
# The pinned col/rows are 'removed' from the matrix and it's checked again 
#     for rows/cols with pins. Repeat until no pins are found or the size
#     of the remaining array is 1x1.
#
# The pinned r/c aren't really removed, an 'index list' is used to map from
#     consecutive integers to valid matrix row/col indices.

# While there are pins and size(remaining array) > 1x1:
#    Find pinned rows/columns
#    Update index list
#    Update reorder (swap) array
#    Repeat

# A counter is also used to limit the while loop just in case it doesn't
#    terminate normally. The max loops allowed is the size of the original matrix.
# 
def reorderEquations(mat, column):
    sz = mat.shape[0]
    swp_ary = [i for i in range(sz)]
    inx_list = [i for i in range(sz)]
    if Support.gVerbose > 1: print("reorder: Initial swap array:", swp_ary)
    if Support.gVerbose > 1: print("reorder: Initial inx dictionary:", inx_list)

    working_mat = mat.copy()
    count = sz
    done = False
    itr = 1
    while not done:
        if Support.gVerbose > 0: 
            print()
            print("---------------------------------------------------")
            print(Support.myName(), ": Pin search #", itr, "  count=", count, "  inx_list=", inx_list, \
                  "  swp_ary=", swp_ary)
            pp_num(working_mat)
        # Returns a dict of (row it's in, row it needs to be in) pairs
        pins = find_pins(working_mat, inx_list)
        if Support.gVerbose > 0: print_pin_list(pins) # 2
        if len(pins) != 0:
            if Support.gVerbose > 0: 
                working_mat = blank_pinned_rc(pins, working_mat, inx_list)
            inx_list = apply_pins_inx_list(pins, inx_list)
            swp_ary = apply_pins_r_array(pins, swp_ary)
            if Support.gVerbose > 0:
                print("reorder: count=", count, "  Applied pins, now swp_ary=", swp_ary)
            swp_mat = makeSwapMatrix(swp_ary)
            working_mat =  swp_mat * mat

            sz = len(inx_list)-1
            count = count - 1
            done = sz <= 1 or count <= 0
            itr = itr + 1
        else:
            done = True
    
    if done:
        if Support.gVerbose > 0: 
            print("Matrix after applying pins")
            pp(mat)
            print("iColumn after applying pins")
            pp(column)

        # Check if the matrix is fine with just the swaps we have now.
        perm = [i for i in range(mat.shape[0])]
        swp_mat = makeSwapMatrix(swp_ary)
        new_mat =  swp_mat * mat
        if not diagonalNonzero(new_mat, perm, swp_ary):
            # Now find a permutation of the remaining rows/cols with no zeros on the diagonal.
            found = False
            if Support.gVerbose > 1: print(Support.myName(), ": Moving on to permutation search")
            for perm in permutations( list(range(len(inx_list)) ) ):
                if Support.gVerbose > 1: 
                    print(Support.myName(), 'reorderEqn: perm=', perm)
                found = diagonalNonzero(working_mat, perm, inx_list)
                if found:
                    break
            if found:
                if Support.gVerbose > 1: print(Support.myName(), ': reorderEqn: Good permutation found:', perm)
            else:
                if Support.gVerbose > 1: print(Support.myName(), ': reorderEqn: Good permutation not found!')
                return -1, -1

            # Incorporate the permutation list into the swap list
            swp_copy = swp_ary.copy()
            for n, p in enumerate(perm):
                swp_ary[inx_list[p]] = swp_copy[inx_list[n]]
                if Support.gVerbose > 1:
                    a = inx_list[p]
                    c = inx_list[n]
                    print(Support.myName(), ": swp_ary[{0:d}=inx_list[{1:d}=perm[{2:d}]]] = "+ \
                          "swp_ary[{3:d}=inx_list[{2:d}]]".format(a, p, n, c))
                    print(swp_ary)
                # swp[inx_list[perm[0]=1]=2] = swp[inx_list[0]=1]    swp(2) = swp(1)
                # swp[inx_list[perm[1]=0]=1] = swp[inx_list[1]=2]    swp(1) = swp(2)
                # swp[inx_list[perm[2]=2]=3] = swp[inx_list[2]=3]    swp(3) = swp(3)
            swp_mat = makeSwapMatrix(swp_ary)
            new_mat =  swp_mat * mat
        new_col = swp_mat * column
        if Support.gVerbose > 1:
            print()
            print("reorder: swp_ary=", swp_ary)
            print("\nreorder: swap_matrix=")
            pp(swp_mat)
            print("\nreorder: Reordered matrix:")
            pp(new_mat)
            print("\nreorder: Reordered iColumn:")
            pp(new_col)
        return new_mat, new_col
    else:
        return -1, -1
