from string import *

z26Log = open( 'd:/emulator/atari 2600/z26.log', 'r' )
pytLog = open( 'debug.log', 'r' )
outLog = open( 'merged.log', 'w' )

for x in range(6):
    pytLog.readline()

while 1:
    z26Line = z26Log.readline()
    if len(z26Line) < 41:
        continue
    z26Line = z26Line[40:]
    pytLine = pytLog.readline()[:-1]
    if len(pytLine) < 20:
        pytLine = pytLog.readline()[:-1]
    if len(pytLine) == 0:
        break

    pytPC   = pytLine[:4]
    z26PC   = z26Line[21:25]
    pytA    = pytLine[12:14]
    z26A    = upper(z26Line[8:10])
    pytX    = pytLine[18:20]
    z26X    = upper(z26Line[11:13])
    pytY    = pytLine[24:26]
    z26Y    = upper(z26Line[14:16])
    pytS    = pytLine[30:32]
    z26S    = upper(z26Line[17:19])
    pytP    = pytLine[36:44]
    z26P    = z26Line[0:8]
    pytINS  = pytLine[47:]
    z26INS  = upper(z26Line[36:])

    while len(pytINS) < 16:
        pytINS += '  '

    output  = pytPC + ' ' + z26PC + ': A '
    if pytA != z26A:
        output += '* '
    else:
        output += '  '
    output += pytA + ' ' + z26A + ' X '
    if pytX != z26X:
        output += '* '
    else:
        output += '  '
    output += pytX + ' ' + z26X + ' Y '
    if pytY != z26Y:
        output += '* '
    else:
        output += '  '
    output += pytY + ' ' + z26Y + ' S '
    if pytS != z26S:
        output += '* '
    else:
        output += '  '
    output += pytS + ' ' + z26S + ' '
    output += pytP + ' ' + z26P + ' ' + pytINS + z26INS

    outLog.write( output )

z26Log.close()
pytLog.close()
outLog.close()
