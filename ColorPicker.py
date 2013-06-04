#
#   The Color Picker window, used for selecting a color for GUI elements
#

import pygame, numpy, os
from pygame.locals import *
from math import *

pickerWheel = 'pytari.wheel.bmp'
pickerWheelAlpha = 'pytari.wheelalpha.bmp'

circleSize = 127    # Resulting image is Size * 2 + 1
circleAlias = 1     # Antialiasing grid size, Larger grid is more accurate

def ColorHSV( hue, sat, value ):	
    while hue >= 360.0:
        hue -= 360.0
    while hue < 0.0:
        hue += 360.0
    hue = hue / 60.0
    i = int( hue )
    f = hue - i
    p = value * (1.0 - sat)
    q = value * (1.0 - sat * f)
    t = value * (1.0 - sat * (1.0 - f))
    
    if i == 0:  
            return [value,t,p]
    elif i == 1:
            return [q,value,p]
    elif i == 2:
            return [p,value,t]
    elif i == 3:
            return [p,q,value]
    elif i == 4:
            return [t,p,value]
    elif i == 5:
            return [value,p,q]
    return [0,0,0]

dimRange = range(-circleSize,circleSize+1)
aliasRange = range(circleAlias)

if not pickerWheel in os.listdir( os.getcwd() ):
    print 'MESSAGE\tGenerating color picker wheel'
    colorWheel = pygame.Surface((circleSize*2+1,circleSize*2+1),SRCALPHA,32)
    alphaWheel = pygame.Surface((circleSize*2+1,circleSize*2+1),0,8)
    array = pygame.surfarray.pixels3d(colorWheel)
    alpha = pygame.surfarray.pixels_alpha(colorWheel)
    for xx in dimRange:
        for yy in dimRange:
            color = numpy.zeros((3)).astype('l')
            alphaAliased = 0
            for xs in aliasRange:
                for ys in aliasRange:
                    x = xx + xs / (circleAlias + 1.0)
                    y = yy + ys / (circleAlias + 1.0)
                    saturation = sqrt( x ** 2 + y ** 2 ) / (circleSize - 2.0)
                    if saturation <= 1.0:
                        if y != 0:
                            hue = atan( x * 1.0 / y ) * 180 / 3.14159 + ( y > 0 ) * 180.0
                        elif x >= 0:
                            hue = 270
                        elif x <= 0:
                            hue = 90
                        color += numpy.array(ColorHSV( hue, saturation, 255 )).astype('b')
                        alphaAliased += 255
                    elif saturation <= 1.02:
                        alphaAliased += 255
            array[xx+circleSize][yy+circleSize][:] = (color / (circleAlias**2)).astype('b')
            alpha[xx+circleSize][yy+circleSize] = alphaAliased / (circleAlias**2)

    pygame.surfarray.pixels2d(alphaWheel)[:] = alpha

    del array
    del alpha
    pygame.image.save(colorWheel,pickerWheel)
    pygame.image.save(alphaWheel,pickerWheelAlpha)
else:
    colorWheel = pygame.image.load(pickerWheel)
