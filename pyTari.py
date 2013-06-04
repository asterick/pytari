#! /usr/bin/env python
#
#   pyTari - Written by Bryon Vandiver, released under the GNU
#   public licence.  This is an open source atari emulator
#   built entirely by public domain documentation provided by
#   various sources, big thanks to Dan Boris and Kevin Horton
#
#   This is the main execution loop.  It does little more than
#   handle syncronization and import all the component classes
#   into a main body. It also creates the interface between the
#   SDL and Audio modules.  Psyco might be added later, if
#   performance is a big issue.
#

print "\t--- PyTari Bootup ---"

import os, pygame, numpy, pickle, zlib, thread
import CPU, Chemistry, RomTools, Cart, Debugger, ColorPicker
from pygame.locals import *
from types import *
#import psyco; psyco.jit()

version = "build 12-21-2002 (Squirrel)"

if not pygame or not numpy or not zlib:
    print """
ERROR\tYou do not have the required libraries, this could be either
\t\tpygame, zlib, or numpy.  Please note that both of these are
\t\trequired, although sound emulation is optional.  Feel free to
\t\tdownload these modules and try again.
    """
    exit()

print "MESSAGE\tLoading configuration"

files = os.listdir(os.getcwd())

if "pytari.config" in files:
    configFile = open('pytari.config','rb')
    configuration = pickle.loads(zlib.decompress(configFile.read()))
    configFile.close()
else:
    print "MESSAGE\tNo configuration found, using defaults"
    configuration = {
        'settings':{
            'sound':1,
            'fullscreen':0,
            'screenSize':(800,600),
            'depth':32,
            'roms':'roms'
            },
        'desktop':{
            'image':'pytari.desktop.png',
            'alignment':'centered',
            'color':(151,149,128)},
        'colors':{
            'title.focus':(255,231,0),
            'body.focus':(0,150,255),
            'focused':(255,210,57),
            'title.unfocus':(255,210,57),
            'body.unfocus':(0,102,155),
            'widget.fore':(0,0,0),
            'widget.back':(255,255,255),
            'message':(255,255,255),
            'highlight':(200,200,255),
            'text':(0,0,0)
        },
        'profiles':{}
        }

pygame.mixer.pre_init(31440,8,0)
pygame.init()
pygame.mixer.set_num_channels(3)
pygame.mixer.set_reserved(2)
pygame.event.set_blocked( [ACTIVEEVENT,VIDEORESIZE,VIDEOEXPOSE] )

print "MESSAGE\tInitializing all available joysticks"
for id in range(pygame.joystick.get_count()):
    pygame.joystick.Joystick(id).init()

icon = pygame.image.load('pytari.icon.png')
logo = pygame.image.load('pytari.logo.png')
alerts = pygame.image.load('pytari.alerts.png')
font = pygame.font.Font(None,20)
FixedFont = pygame.font.Font('courbd.ttf',16)

if configuration['settings']['fullscreen'] == 1:
    television = pygame.display.set_mode(configuration['settings']['screenSize'],FULLSCREEN,configuration['settings']['depth'])
else:
    television = pygame.display.set_mode(configuration['settings']['screenSize'])
    pygame.display.set_icon(icon)
    pygame.display.set_caption('pyTari ' + version)

atari = CPU.CPU()
gui = Chemistry.Compound( television, configuration, font, alerts )

aboutCaption = "pyTari: " + version + """

Bryon Vandiver (asterick@buxx.com): Code
Kevin Horton: Public Domain Information
Dan Boris: Public Domain Information
Steve Wright: Stella Programmer's Guide"""

AboutPytari = {
    'size':(32,32,480,240),
    'icon':None,
    'title':'About pyTari',
    'tray':['iconify', 'close'],
    'atoms':[
            Chemistry.AtomImage(logo,(0,0)),
            Chemistry.AtomLable((140,0),aboutCaption, color = (255,255,255), alignment = 'center'),
        ]
    }

gui.register(AboutPytari,visible = Chemistry.False)

class debugholder:
    def __init__( self ):
        self.disasm = None
        self.ramview = None
        self.tiareg = None

debug = debugholder()

def ShowAbout():
    gui.hide( Chemistry.False,AboutPytari )

def QuitPytari():
    pygame.event.post( pygame.event.Event(QUIT,{}) )

def ShowDissassembler():
    if debug.disasm == None and atari.cart != None:
        debug.disasm = Debugger.Disassembler( gui, atari, FixedFont )
    elif debug.disasm != None:
        debug.disasm.Show()

def ShowTIARegisters():
    if debug.tiareg == None and atari.cart != None:
        debug.tiareg = Debugger.TIARegisters( gui, atari.tia, FixedFont )
    elif debug.tiareg != None:
        debug.tiareg.Show()

def ShowRam():
    if debug.ramview == None and atari.cart != None:
        debug.ramview = Debugger.RamViewer( gui, [('RIOT',atari.ram)] + atari.cart.getRam() + [('Cartridge',atari.cart.getRom())], FixedFont, atari.reg )
    elif debug.ramview != None:
        debug.ramview.Show()

def UnloadRom():
    if debug.ramview != None:
        debug.ramview.Unload()
        debug.ramview = None
    if debug.disasm != None:
        debug.disasm.Unload()
        debug.disasm = None
    if debug.tiareg != None:
        debug.tiareg.Unload()
        debug.tiareg = None

    atari.cart = None

def SaveScreenshot():
    # event is posted to stall the screenshot a frame
    pygame.event.post(pygame.event.Event(USEREVENT,{'code':SaveScreenshotEvent}))

def SaveScreenshotEvent():
    x = 0
    while 'snap%04x.bmp' % x in os.listdir( os.getcwd() ):
        x = x + 1
    pygame.image.save( television, 'snap%04x.bmp' % x )
    
def LoadCallBack( data, profile ):
    UnloadRom()
    cart = Cart.Mappers[profile['mapper']]( numpy.fromstring( data, numpy.uint8 ) )
    atari.insert(cart)
    print "MESSAGE\tLoaded", profile['name']

LoadDialog = RomTools.LoadDialog( gui, configuration['settings']['roms'], configuration['profiles'], LoadCallBack )
DupeCheck = RomTools.DupeCheck( gui, configuration['settings']['roms'] )
    
menu =  [(((64,32),'Game'),
            [(((96,32),'Load Rom'),LoadDialog.ShowDialog),
             ('Unload Rom',UnloadRom),
             Chemistry.Seperator,
             ('Run',atari.run),
             ('Stop',atari.stop),
             ('Reset',atari.reset),
             Chemistry.Seperator,
             ('Tools',[
                 ('Locate Duplicates',DupeCheck.LocateDupes),
                 ('Save Screenshot',SaveScreenshot)
                 ]),
             Chemistry.Seperator,
             ('Quit pyTari', QuitPytari)
            ]),
         ('Debug',[
             ('Disassembly',ShowDissassembler),
             ('TIA Registers',ShowTIARegisters),
             ('Memory Viewer',ShowRam),
             ]),
         ('About',ShowAbout)
         ]

gui.SetMenu(menu)

screenWidth, screenHeight = television.get_size()

class VirtualAxis:
    "Virtual Axis: Used to convert buttons into an analog axis"
    def __init__( self, callback, axis ):
        self.value = 0
        self.callback = callback
        self.axis = axis
    def ButtonA( self, value ):
        if value:
            self.value = self.value - 1
        else:
            self.value = self.value + 1
        self.callback( self.callback, self.axis )
    def ButtonB( self, value ):
        if value:
            self.value = self.value + 1
        else:
            self.value = self.value - 1
        self.callback( self.callback, self.axis )

joyAxisDirect = {}
joyButtonDirect = {}

def DoAxisMotion( joy, axis, value ):
    pass
def DoButton( joy, button, value ):
    pass

def EventPump( ):
    events = pygame.event.get()

    for event in events:
        if event.type is KEYDOWN:
            DoButton( -1, event.key, 1 )
            gui.DoEvent( event )
        elif event.type is KEYUP:
            DoButton( -1, event.key, 0 )
            gui.DoEvent( event )
        elif event.type is MOUSEMOTION:
            DoAxisMotion( -2, 0, (event.pos[0] * 2.0 / screenWidth) - 1.0 )
            DoAxisMotion( -2, 1, (event.pos[1] * 2.0 / screenHeight) - 1.0 )
            gui.DoEvent( event )
        elif event.type is MOUSEBUTTONDOWN:
            DoButton( -2, event.button, 1 )
            gui.DoEvent( event )
        elif event.type is MOUSEBUTTONUP:
            DoButton( -2, event.button, 0 )
            gui.DoEvent( event )
        elif event.type is JOYAXISMOTION:
            DoAxisMotion( event.joy, event.axis, event.value )
        elif event.type is JOYBUTTONDOWN:
            DoButton( event.joy, event.button, 1 )
        elif event.type is JOYBUTTONUP:
            DoButton( event.joy, event.button, 0 )
        elif event.type is QUIT:
            return 1
        elif event.type is USEREVENT:
            event.code()
    return 0

buffer = Chemistry.AtomImage(logo,(0,0))

frameViewer = {
    'size':(32,32,328+8,292),
    'icon':None,
    'title':'Television',
    'tray':['iconify'],
    'atoms':[
            buffer,
        ]
    }

gui.register(frameViewer)

televisionSize = television.get_size()

def runtime():
    static = pygame.Surface((160,264),SWSURFACE, 8)
    channel = pygame.image.load('pytari.channel.png')

    palette = numpy.zeros((256,3)).astype('b')
    for x in range(len(palette)):
        palette[x] = x
    static.set_palette(palette)

    while 1:        
        if atari.cart != None:
            telly = atari.tia.UserFrame
        else:
            staticArray = pygame.surfarray.pixels2d(static)
            staticArray[:,::2]  = numpy.random.random_integers( 0, 0xFF, (160, 132) ).astype(numpy.uint8)
            staticArray[:,1::2] = numpy.random.random_integers( 0, 0xBF, (160, 132) ).astype(numpy.uint8)
            telly = pygame.transform.scale( static, (320,264) ).convert(24)
            telly.blit( channel, (8,8) )
        buffer.set(telly)

        if gui.hidden:
            television.fill((0,0,0))            
            television.blit( pygame.transform.scale( telly.subsurface((0,0,320,200)), televisionSize), (0,0) )
        else:
            gui.DoUpdate()

        atari.execute()

        pygame.display.flip()
        if EventPump():
            return

import profile

runtime()

print "MESSAGE\tSaving configuration"

configFile = open('pytari.config','wb')
configFile.write(zlib.compress(pickle.dumps(configuration)))
configFile.close()

pygame.quit()
