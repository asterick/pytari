pyTari: An abuse of a language.

For licence information, read copying.txt

you must place a file 'courbd.ttf' in the working program directory for pytari to run.
I cannot provide this due to copyright reasons.  It is packaged with most new distrobutions
of windows

0 --- Todos --

	1:  RIOT / CART register viewer
	2:  Configuration editor
	3:  Input handler
	4:  Playable emulation

1 --- What is pyTari? ---

pyTari is an emulator coded in the scripting language known as python.  This project was
origionally created in hopes that I might learn the language throughly, and maybe even
use it as ammunition for any software companies out there that would like to hire me on.
The ultimate goal is to create a high compatibility, easy to read source that can be used
for creating software for the atari, and design custom mappers with minimal effort.  I
intend on creating a robust debugging environment, but not nessessarly a high speed
execution base.

So far, the 6507 and RIOT emulation seems very accurate, but the TIA leaves something to
be desired.  I'm currently learning the innerworkings of the processor on a more low level.
Tricks seem to be the driving force behind that chip.  Fortunately, the fact that the
registers are well documented and the fact that there is so little time to actually render
a frame makes it easy to figure out what a programmer was tring to do and thus easier to
work the system.

2 --- Contributers ---
	Bryon Vandiver (asterick(at)buxx.com)	Lead coder, project manager, graphics, etc
	Kevin Horton				Public Domain Information
	Dan Boris				Public Domain Information
	Steve Wright				Stella Programmer's Guide

3 --- Project Status (ballpark) ---
	CPU (DOC/UNDOC):	100% / 0%
	TIA:			95%		(no sound)
	RIOT:			95%		(No panel)
	GUI:			80%		(No configuration)
	DEBUG:			90%		(No RIOT or Cart registers)
	OTHER:			75%		(No joystick event pump)

4 --- Disclaimer ---

This software is the collective work of several people, willing or not.  All the information
I have used is public domain and freely available anywhere at several locations on the web.
I do not encourage the use of pirate roms, there are many public domain images out there
that are well suited for emulation.  This emulator should not be used in association with
pirated software.

Atari is a trademark of Hasbro (corp?  inc?  dunnknow),  Thus, the Atari logo belongs to
them.

Please do not e-mail me in reguards to compatibility.  I will have a scripted database
eventually that will be used for rom compatiblity, as well as a profile database.  If
you have a specific bug, please post it in the sourceforge bug tracker.

side note:  I know the idea of using the emulator for the purpose of playing pirate
	software is pretty silly, seeing as my computer is nearly top of the line and I can't
	pull a playable frame rate.

Release Notes (12-21-2002 SQUIRREL):
	(12-21-2002)
	It seems the life of a emulator designer is inherently complicated.  I have
	moved recently and not had much time to work on the project due to working
	in retail over the holiday season.  A number of changes have been made, 
	namely to the TIA emulation (making it more accurate) and some debugger toys.
	($##, X) addressing has been fixed.  I was making a very stupid mistake.

	(10-23-2002)
	The debugger and memory viewer are done.  Cleaned up the debugger.py module 
	significantly, Need to finish the TIA viewer asap.  That is next on my list.
	Next is a RIOT/CART register viewer, I'll put these in the same window for
	space reasons, considering that carts will only have one or two registers.
	Goals before next release:  Finish debug windows, work on getting TRON to
	display it's boot screen correctly.  I may start working on configuration
	menus also.  Input will not be finished in this release.

Release Notes (10-22-2002 AIRSMASH):
	(10-16-2002)
	This release is all about working out bugs in the emulation, not adding
	features.  I will only be adding things if it makes it easier to debug.
	I implemented player graphics, and they appear to work.  Alien's
	Revenge displays at least one frame correctly, I'm very stoked about that.

	Added Vertical delay graphics to the player

	Modified the Panel constant to simply return Beginner, Color, No reset / 
	select,	Adventures of Tron would infinately loop because it was constantly
	being reset.

	(10-17-2002)
	Ironed out several kinks, mostly stupid mistakes (forgetting parens, order of ops,
	not being logical, not bitwise, using the wrong variables, etc), also, the TIA
	runs at 3x the speed of the CPU and RIOT, I failed to remember this, which resulted
	in graphic errors on delicately timed writes (adventures of tron).  Fixed that as
	well.  I also made a function that runs the atari 59736 (I actually have that number
	memorized now) (TIA) cycles per frame, which is as real-world as it's going to get.
	I generally avoid using that because it draws WAY too much CPU time without doing
	an event dump.  The TIA also now has a back buffer, that is automatically 
	transformed into something a real projection (flipped, rotated, and scaled). This
	also occurs only once per blanking period, so it should in THEORY be a wee faster.

	There is no vertical delay on the ball currently.  This isn't too big of an issue
	seeing as I can't even get the player graphics to display properly.  I think it's
	a palette issue.... maybe not though.
	

	On a side note, the Adventures of Tron title screen displays near perfectly (No
	copyright information in the lower right corner)

	I've also geared my priorities to debugging the processor cores.  Input is silly
	to write if I can't even run software to use it in.

	I actually read up on numeric's slicing... and dang it, I didn't know you could
	actually create slices in multiple dimensions.  So, now there is only a scale
	transformation applied.	

	(10-18-2002)
	I rebuilt the palette generators, fixed some bugs, and hopefully made it a wee
	more accurate.  I know it wouldn't work on certain parts.

	(10-22-2002)
	Started work on the TIA debugger, displays some neato keen information on what it
	is currently doing.  No numerical outputs though.  I'll get to that eventually.
	I'm basicly done with the release, I want to flesh out the debugger functions a
	wee more before I make another release.  I really need to clean up the container
	atom for chemistry so it's not so horrendously slow to open the memory viewer.

Release Notes (10-15-2002 GOODFAITH):
	The emulation is infact broken, it doesn't run anything right now, this
	is the first release, given out to prove that I'm not lying about the
	projects existance.  There are a few things missing and other issues:
	
	1)	The emulator does not support any inputs to the atari, including 
		the panel, this should be resolved by the next release, as it
		is top priority

	2)	The chip register viewer is non existant, as well as functionality
		for it is pretty nonexistant (Carts don't have a bank number, etc)

	3)	There is no way to manually configure the emulator.  This should
		be resolved soon

	4)	I built the emulator around a copyritten font, courbd.ttf, which
		due to copyright reasons, I cannot post.  I'm sure a replacement
		font would be easy to find, or simply gained from a certain
		propriatary OS's fonts directory.

	5)	Sound emulation was origionally going to be included, but direct
		access to samples in a sound on loop causes weird static, and 
		pregenerating waveforms is slow.

	6)	I've not implemented player sprite graphic pattern generators, 
		because I got lazy.

	7)	The way it handles instructions per frame is stupid, and make shift

	There are various other things that are not included, but not really a
	priority.  The emulator is slow, but I never expected it to run at
	full speed.  Performance isn't an issue.  I might optomize later, but
	I'm more concerned with getting it accurate, and adding developer functions
	like breakpoints.  This has the capibility to be the most portable atari
	emulator of all time, which makes me happy.
