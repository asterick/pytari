#
#   RIOT (CMOS 6532) Emulation
#
#   This code emulates the RIOT chip, minus the 128 bytes
#   of ram which suprisingly enough provides all of the
#   memory in the atari, minus a few registers (most which
#   are read or write only)
#
#   Since the (r) and (iot) are sperated, only the IO and
#   Timer is implemented
#
#   The RIOT is mapped in the atari thusly:
#
#     Address
#   +-+-+-+-+-+
#   |4|3|2|1|0|     Read    Write   
#   +-+-+-+-+-+
#   
#    - - 0 S 0      Output  Output  S = Port
#    - - 0 S 1      DDR     DDR     S = Port
#    - A 1 - 0      Timer   ------  A = Enable Timer IRQ
#    - - 1 - 1      IRQ     ------
#    0 - 1 B C      ------  Edge    B = Enable PA7 IRQ      C = +/- edge
#    1 A 1 B B      ------  Timer   A = Enable Timer IRQ    B = Interval
#
#   Since the 6507 has no IRQ lines, the emulation does not handle the
#   Enable Lines.  Reading the IRQ Flag register clears the PA7 IRQ,
#   addressing the timer register causes the timer IRQ to reset
#   The edge register gains data from the addressing lines, not thrown
#   data.
#
#   How output PB is handled is a mystery to me, it very well could be
#   used to mask the port, but not actually be written to (in the case
#   of a diode farm)
#
#   JOYSTICK API:
#
#       Clocks are randomly added to the joystick, it is it's
#       responcibility to know when it has changed.
#
#       <-Transition()  - Joystick must call this when PA7 has changed
#       fetch()         - Poll for status of the fields, packed
#       throw(value)    - Forces output to the joystick ( masked )
#       buttons()       - Fetches the POTS and FIRE button, used by TIA
#

class RIOT:
    def __init__(self, ControlA, ControlB ):
        self.clocks = 0xCD                      # Riot gains a random start position
        self.DDRA   = 0x00                      # Initially, everything is a read
        self.DDRB   = 0x00                      # ONLY HOLDS DATA!  This might also mask data
        self.OUTA   = 0x00                      # Only A allows output
        self.OUTB   = 0x00                      # THIS MIGHT BE DEPRECIATED, since the port is read only
        self.timer  = 0xFF                      # Timer is reset
        self.IRQ    = 0x00                      # No events have occured, but they could later
        self.edge   = 0                         # Interrupt occurs on a negitive edge
        self.shift  = 0                         # There is no inverval shift
        self.clocks = 0                         # RIOT Timing

        self.ControlA = ControlA                # Start off with dummy controllers, these do nothing
        self.ControlB = ControlB                # but return OFF states, only player one gets an IRQ
    
    def reset( self ):
        self.timer = 0xFF                       # Timer is reset
        self.shift = 0                          # single cycle counting

    def plug( self, ControlA, ControlB ):
        ControlA.transitions( self )
        ControlB.transitions()
        self.ControlA = ControlA
        self.ControlB = ControlB
        
    def transition(self, value):                # Value of PA7 changed
        if value == self.edge:                  # Does the edge match
            self.IRQ = self.IRQ | 0x40
            
    def fetch(self, address):
        self.timer = self.timer - (self.clocks / 3)
        self.ControlA.clocks += self.clocks     # Give the controllers some time
        self.ControlB.clocks += self.clocks     
        self.clocks %= 3                        # The riot runs 1/3rd the max speed
        if (self.timer < 0):                    # Timer rollover
            self.timer = self.timer & 0xFF      # Roll over
            self.shift = 0                      # Unshifted
            self.IRQ = self.IRQ | 0x80          # Timer IRQ occured
        
        if (address & 0x4):                     # Timer and IRQ
            if (address & 0x1):                 # IRQ status
                IRQ = self.IRQ                  # Pre-clear value
                self.IRQ = self.IRQ & 0x80      # Clear PA7 flag
                return IRQ                 
            else:                               # Read Timer
                self.clocks = 0                 # Make sure to sync up with TIA
                self.IRQ = self.IRQ & 0x40      # Clear timer flag
                return self.timer >> self.shift # Return 'fixed' value
        else:                                   # Ports
            port = address & 0x02               # Port A = 0 Port B = 2
            if (address & 0x1):                 # Direction selection
                if (not port):                  # Read port A Status
                    return self.DDRA
                else:                           # Read port B Status
                    return self.DDRB                              
            else:                               # Read input ORed with the output
                if (not port):                  # Read port A Status (Controllers)
                    input = ( self.ControlA.fetch() << 4 | self.ControlB.fetch() ) & ( self.DDRA ^ 0xFF )
                    return (self.OUTA & self.DDRA) | input
                else:                           # Read port B status
                    return 0xB                  # NEED TO RETURN PANEL INFO!

    def throw(self, address, value):        
        self.timer = self.timer - (self.clocks / 3)
        self.ControlA.clocks += self.clocks     # Give the controllers some time
        self.ControlB.clocks += self.clocks     
        self.clocks %= 3
        if (self.timer < 0):                    # Timer rollover
            self.timer = self.timer & 0xFF      # Roll over
            self.shift = 0                      # Unshifted
            self.IRQ = self.IRQ | 0x80          # Timer IRQ occured
        
        if (address & 0x4):                     # Timer and Edge
            if (address & 0x10):                # Write timer
                self.IRQ = self.IRQ & 0x40      # Clear timer IRQ
                interval = address & 0x3        # Gain the interval
                if (interval == 3):
                    self.shift = 10             # shift value is usually a multiple of 3
                else:
                    self.shift = interval * 3
                self.timer = value << self.shift
                return
            else:                               # Write edge
                self.edge = address & 0x1
                return
        else:                                   # Ports
            port = address & 0x02               # Port A = 0 Port B = 2
            if (address & 0x1):                 # Direction selection
                if (not port):                  # Read port A Status
                    self.DDRA = value           # Data direction changed, give joys new data          
                    self.ControlA.throw( (value & self.OUTA) >> 4 )
                    self.ControlB.throw( value & self.OUTB & 0xF )
                    return
                else:                           # Read port B Status
                    self.DDRB = value           # Data direction changed, but co
                    return self.DDRB                              
            else:                               # Write output
                if (not port):                  # Read port A Status
                    self.OUTA = value           # Output to the controllers changed
                    self.ControlA.throw( (value & self.OUTA) >> 4 )
                    self.ControlB.throw( value & self.OUTB & 0xF )
                    return
                else:                           # Read port B Status
                    self.OUTB = value           # Output to PortB changed, this may be completely useless
