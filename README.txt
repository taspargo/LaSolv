
Windows version: LaSolv_0.3.1.zip
Mac OSX version: LaSolv_0.8.9.zip

For running on Linux systems:
	Requires Python 3. Download the source code and these libraries (packages):
		wxPython
		sympy
		engineering_notation
		matplotlib

	Install the packages in the usual Python way (Homebrew, pip, etc.). Make sure that the help file, help.htm, is
	in the same directory as the source, or one or two levels up. Then start LaSolv using:

		python3 gui_wx.py

On all systems:
	
	The GUI should open with two empty sub-windows in it. The left one is where you type or edit a file. The right one is where the solution will be shown.
	Once you have a file loaded or have entered a circuit, click 'Solve' and if the circuit is solvable, the requested solution should show up on the right side of the window.
	You can also plot the solution. Clicking 'Plot' will solve the equations and then plot the magnitude and phase. If there aren't any capacitors or inductors in the circuit, it's really not worth plotting! If a frequency range isn't supplied, LaSolv will estimate an appropriate range for you. If both a start and stop frequency is supplied, those will be used as the limits.

	There's an option on the bottom for 'Test mode'. I've used this to verify
the results that LaSolv gets. It takes a list of circuit files, solves them if 
possible, and then outputs how many were solved, and how many got the correct
answer (which is at the bottom of the circuit file in plain text). I'll probably
disable this in future executuables since a user wouldn't need it, only someone 
developing LaSolv would find this useful.

Side note...
<excuses><disclaimers>If you look through the code, even a beginning Python programmer will
see several cases where I could accomplished the same function with less code,
more speed, easier to follow, etc. The original version of LaSolv was written in 
C++ from scratch. There came a point where I realized I didn't have enough
math background to make it work in all cases (factoring large polynomials was
the specific part). So I decided to rewrite it in Python, which I did in about 3-4
evenings. I wasn't concerned with it being efficient, fast or in using features
that Python has which generic C++ doesn't, I just wanted to get it translated. So
that's I didn't use a dictionary here or there, or why a whole method could
probably be replaced by one line of code, it's because I just wanted to get the
Python code working.</disclaimers></excuses> I'll get to doing that kind of stuff time and motivation
permitting. Some code simplification would help in getting rid of bugs as well.


-tom spargo

