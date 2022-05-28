'''
Created on May 5, 2019

@author: Thomas
'''

import sympy
from sympy import factor
from sympy import Symbol

if 1:

    if 0:
        # rf1 >> rs1
        rf1, rs1, s = sympy.symbols('rf1 rs1 s')
        efn = sympy.sympify('cpi*rf1*rp1*s+cpi*rp1*rs1*s+gm*rf1*rp1+rf1+rp1+rs1')
        print('efn=', efn)
        coll = sympy.collect(efn, s, evaluate=False)
        print('collected by s:', coll)
        print('size of coll:', len(coll))
        print(coll.keys())
        print(coll.values())
        collf = sympy.collect(efn, s, factor, evaluate=False)
        print('collected by s then factor:', collf)
        s_part = collf[s]
        print('s-part=', s_part)
        fixd = s_part.subs(rf1+rs1, rf1)
        print('Apply rf1 >> rs1')
        print('fixd=:', fixd)
        o_part = coll[1]
        fixdo = o_part.subs(rf1+rs1, rf1)
        print('1-part=', o_part)
        print('fixdo=', fixdo)
        final = s*fixd+fixdo
        print('final=', final)

    if 1:
        # from cascode gain stage denom
        # Re << Rs
        # Rl < Ro2
        eq1 = sympy.sympify('Gm2*Ro2*Rp2*Cp1*s + Rl + Ro2 + Rp2')
        eq2 = sympy.sympify('Cp1*Re*Rp1*s + Cp1*Rp1*Rs*s + Gm1*Re*Rp1 + Re + Rp1 + Rs')
        efn = sympy.expand(eq1*eq2)
        efnf = efn.factor()
        print(' efn=', efn)
        print('efnf=', efnf)
        Re, Rs, s = sympy.symbols('Re Rs s')
        coll = sympy.collect(efn, s, evaluate=False)
        print('collected by s:', coll)
        print('size of coll:', len(coll))
        dct = {'1':0, 's':1, 's**2':2, 's**3':3, 's**4':4, 's**5':5, 's**6':6}
        kys = coll.keys()
        for ky in kys:
            print('str(ky)=', str(ky), '  order=', dct[str(ky)])
        print('keys:', kys)
        
        print('values:', coll.values())
        collf = sympy.collect(efn, s, factor, evaluate=False)
        print('collected by s then factor:', collf)
        s_part = collf[s]
        print('s-part=', s_part)
        fixd = s_part.subs(Re+Rs, Rs)
        print('Apply Re << Rs')
        print('  fixd=', fixd)
        o_part = coll[1].factor()
        fixdo = o_part.subs(Re+Rs, Rs)
        print('1-part=', o_part)
        print(' fixdo=', fixdo.factor())
        final = s*fixd+fixdo
        print(' final=', final)

    #coll2 = sympy.collect(efn, [rf1, rs1], evaluate=False)
    #print('collected by rf1, rs1:', coll2)
    
    if 0:
        ef_zout = sympy.sympify('(cpi*r1*rpi*s+r1+rpi)/(cpi*rpi*s+gm*rpi+1)')
        #print('ef_zout:', ef_zout)
        
        gm, rpi, beta = sympy.symbols('gm rpi beta')
        n,d = sympy.fraction(ef_zout)
        # gm*rpi >> 1
        ef_zout2 = sympy.expand(d/(gm*rpi))
        print('d of ef_zout:', d)
        print('ef_zout2:', ef_zout2)
        
        smp=ef_zout2.subs(1/(gm*rpi), 0)
        print('smp:', smp)
"""
; Gain of a cascode (CE then CB) stage
; Vout / Vin
Vin 1 0
Rs 1 2
Rp1 2 3
Cp1 2 3
Re 3 0
Gm1 4 3 2 3

Rp2 0 4
Cp2 0 4
Gm2 5 4 0 4
Ro2 5 4
Rl 5 0
"""
# Ro2 >> Rp2
# Ro2 >> Rl
# Re << Rp1

if 0:
    xfer = sympy.sympify('-Gm1*Rl*Rp1*Rp2*(Gm2*Ro2 + 1)/((Cp1*Re*Rp1*s + Cp1*Rp1*Rs*s + Gm1*Re*Rp1 + Re + Rp1 + Rs)*(Cp2*Rl*Rp2*s + Cp2*Ro2*Rp2*s + Gm2*Ro2*Rp2 + Rl + Ro2 + Rp2))')
    print()
    #print('xfer:', xfer)
    
    Gm, rp1, beta, Ro2, Re, Rp2, Rl = sympy.symbols('Gm rp1 beta Ro2 Re Rp2 Rl')
    
    xfern, xferd = sympy.fraction(xfer)
    xferlst=sympy.factor_list(xferd)
    #print()
    #print('factor list=', xferlst)
    print()
    print('denom=', xferd)
    xfere = sympy.expand(xferd)
    #print('expanded:', xfere)
    #coll = sympy.collect(xfere, s, evaluate=False)
    #print('collected by s:', coll)

    #print('expand/=', xfere)
    f1= xferlst[1][1][0]
    print('eqn=', f1)
    # Ro2 >> Rp2
    f1d_ro2 = sympy.expand(f1/Ro2)
    print('eqn/Ro2=', f1d_ro2)
    f1d_ro2_sub = f1d_ro2.subs(Rp2/Ro2, 0)
    print('Rp2/Ro2=0 sub=', f1d_ro2_sub)
    
    # Ro2 >> Rl
    f1d_ro2_rl_sub = f1d_ro2_sub.subs(Rl/Ro2, 0)
    print('factor1/Rl subs=', f1d_ro2_rl_sub)
    #print(symp.subs(gm*rpi, beta))
    # Rl << Ro2
    # eqn/Ro2=s*Cp2*Rp2*(Rl/Ro2+1) + Gm2*Rp2 + Rl/Ro2+1+Rp2/Ro2
if __name__ == '__main__':
    pass