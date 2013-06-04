#
#   Controller Emulation
#
#   This is the controller handlers, they latch events from the main
#   loop and convert them into a 7 pin emulation of the origional
#   atari controllers
#
#   The controllers themselves handle the pot timings (TIA reads)
#
#   The format is as follows:
#
#       transitions( obj )      sets up D7 (right P0) edge detection
#       fetch()                 gather RIOT info
#       throw()                 write RIOT info
#       pot1()                  The first POT
#       pot2()                  The second POT
#       fire()                  The latch key
#       toggle( ID, value )     called when a button state changes
#       ground( bool )          Grounds pots
#       latch( bool )           Determines if FIRE is to be latched
#

AnalogAxis = 'AX'
DigitalAxis = 'DX'
DigitalButton = 'B'
DeadZone = 0.3333

class Dummy:
    def __init__(self):
        self.clocks = 0        
    def transitions( self, object = None ):
        pass
    def fetch( self ):
        return 0xF
    def ground( self, state ):
        pass
    def latch( self, state ):
        pass
    def throw( self, value ):
        pass
    def pot1( self ):
        return 0
    def pot2( self ):
        return 0
    def fire( self ):
        return 0

class Joystick:
    'Joystick'
    
    def __init__(self):
        self.clocks = 0
        self.AxisY = 0
        self.AxisX = 0
        self.Fire = 0
        self.RIOT = 0
        self.latch = 0
    def ground( self, value ):
        pass
    def latch( self, value ):
        self.latch = value
    def pot1( self ):
        return 0
    def pot2( self ):
        return 0
    def fire():
        if self.Fire:
            return 0
        else:
            return 0x80
    def fetch( self ):
        return self.RIOT ^ 0xF
    def throw( self, value ):
        pass
    def Fire( self, value ):
        if not value and self.latch:
            return
        self.Fire = value
    def UpDown( self, value ):
        if value < -DeadZone:
            self.RIOT = self.RIOT & 0xC | 0x1   ## DOWN: 0  UP: 1
        elif value > DeadZone:
            self.RIOT = self.RIOT & 0xC | 0x2   ## DOWN: 1  UP: 0
        else:
            self.RIOT = self.RIOT & 0xC         ## DOWN: 0  UP: 0
    def LeftRight( self, value ):
        if value < -DeadZone:
            if self.RIOT & 0x8:
                self.WriteIRQ( 0 )
            self.RIOT = self.RIOT & 0x3 | 0x4   ## LEFT: 1  RIGHT: 0
        elif value > DeadZone:
            if self.RIOT & 0x8:
                self.WriteIRQ( 1 )
            self.RIOT = self.RIOT & 0x3 | 0x8   ## LEFT: 0  RIGHT: 1
        else:
            if self.RIOT & 0x8:
                self.WriteIRQ( 0 )
            self.RIOT = self.RIOT & 0x3         ## LEFT: 0  RIGHT: 0
    def transisitons( self, callback = None ):
        if callback == None:
            self.Callback = callback
            self.WriteIRQ = self.DoWrite
        else:
            self.WriteIRQ = self.NoWrite
    def DoWrite( self, value ):
        self.Callback( value )
    def NoWrite( self, value ):
        pass

    geometry = [
        ( 'Up / Down',      DigitalAxis,    UpDown ),
        ( 'Left / Right',   DigitalAxis,    LeftRight ),
        ( 'Fire',           DigitalButton,  Fire )
        ]


Controllers = {
    Joystick.__doc__:Joystick
    }
