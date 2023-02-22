
Windows version: LaSolv 1.0.0
Mac OSX version: LaSolv_1.0.0

	Finally got pyinstaller to create a stand-alone app for both Windows and Mac.
Linux people can download the source code and run it with Python. You'll need Python 3
to run it, as well as these packages (libraries):

wxPython
sympy
engineering_notation
matplotlib

	Install the packages in the usual Python way (Homebrew, pip, etc.). Make sure that the help file, help.htm, is in the same directory as the source, or one or two levels up. Then start LaSolv using:

python3 gui_wx.py

	The GUI should open with two empty sub-windows in it. The left one is
where you type or edit a file. The right one is where the solution will
be shown.
	Once you have a file loaded or have entered a circuit, click 'Solve'
and if the circuit is solvable, the requested solution should show
up on the right side of the window.
	You can also plot the solution. Clicking 'Plot' will solve the equations and then plot the magnitude and phase. If there aren't any capacitors or inductors in the circuit, it's really not worth plotting! If a frequency range isn't supplied, LaSolv will estimate an appropriate range for you. If both a start and stop frequency is supplied, those will be used as the limits.

	There's an option on the bottom for 'Test mode' (which doesn't work). 
I've used this to verify the results that LaSolv gets. It takes a list of
circuit files, solves them if possible, and then outputs how many were solved,
and how many got the correct answer (which is at the bottom of the circuit
file in plain text). I'll probably disable this in future executuables since
a user wouldn't need it, only someone developing LaSolv would find this useful.

-tom spargo

