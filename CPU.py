#
#   6507 CPU core, atari glue 
#
#   The purpose of this script is to 'glue' the component classes
#   encapsulating the various devices that line through out the atari
#
#   They are: CART, RIOT (ram mapped as seperate component), TIA
#
#   Joysticks are handled by the RIOT chip.
#
#   Until the CPU class recieves an insert call with a cart class,
#   it will return nothing but zeros (BRK), causing the atari to do
#   nothing but reset
#
#   Generally speaking, the API for addressing is:
#   fetch access(address, throw)    -   Used for CART bus, read/write at
#                                       the same time
#   value fetch(address)            -   reads a value from the RIOT or TIA
#   throw(address,value)            -   writes a value to the RIOT or TIA
#
#
#   MEMORY MAPPING:
#   
#    F E D C B A 9 8 7 6 5 4 3 2 1 0
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#   |-|-|-|A|-|-|B|-|C|-|-|-|-|-|-|-| Addressing Lines
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
#   On A                NONE (Use Cart)
#   On A' and C'        TIA
#   On A' and B and C   RIOT
#   On A' and B' and C  RAM
#
#   Carts are pretty stupid about their place in the world, they
#   recieve addressing calls for reads and even when they are not
#   being accessed.   A lot of banking schemes use this to their
#   advantage.
#

import numpy
import TIA, RIOT, CPUops, Cart, Control

class Registers:
    S, A, X, Y, P, PC, PRE = 0xFF, 0xCD, 0xCD, 0xCD, 0x20, 0xCDCD, 0xCD

#    cyclesPerFrame = 59736
cyclesPerFrame = 5974

class CPU:
    def __init__(self):
        self.reg = Registers()
        self.ram = numpy.zeros((128),numpy.uint8)
        CtrlA = Control.Dummy()
        CtrlB = Control.Dummy()        
        self.tia = TIA.TIA( self.clock, CtrlA, CtrlB  )
        self.riot = RIOT.RIOT( CtrlA, CtrlB )
        self.cart = None
        self.clocks = 0
        self.execute = self.stepFrame
        self.step = self.stepNoDump

    def insert(self, cart):
        self.cart = cart
        self.reset()
        
    def plug( self, CtrlA, CtrlB ):
        self.riot.plug( CtrlA, CtrlB )
        self.tia.plug( CtrlA, CtrlB )

    def reset(self):
        self.reg.S = 0xFF        # Reset Stack
        self.reg.PC = self.fetch(0xFFFD) << 8 | self.fetch(0xFFFC)
        
    def push(self, value):
        self.throw( self.reg.S | 0x100, value )
        self.reg.S = (self.reg.S - 1) & 0xFF
    
    def pull(self):
        value = self.fetch( self.reg.S | 0x100 )
        self.reg.S = (self.reg.S + 1) & 0xFF
        return value
    
    def clock( self, clocks = 3 ):
        self.clocks += clocks
        self.tia.clocks += clocks
        self.riot.clocks += clocks
        self.riot.ControlA.clocks += clocks
        self.riot.ControlB.clocks += clocks

    def throw(self, address, value):
        self.clock()
        self.cart.access(address & 0x1FFF,value)
        if not (address & 0x1000):
            index = address & 0x7F
            if (address & 0x80):
                if (address & 0x200):
                    self.riot.throw(index,value)
                else:
                    self.ram[ index ] = value
            else:
                self.tia.throw(index, value)
    
    def fetch(self, address):
        self.clock()
        address = address & 0x1FFF
        access = self.cart.access(address,0)
        if not (address & 0x1000):
            index = address & 0x7F
            if (address & 0x80):
                if (address & 0x200):
                    return self.riot.fetch(index)
                else:
                    return self.ram[ index ]
            else:
                return self.tia.fetch(index)
        return access

    def stop(self):
        self.execute = self.stepStopped
        
    def run(self):
        self.execute = self.stepFrame

    def runTo( self, address ):
        self.breakAddress = address
        self.execute = self.stepRunTo

    def DoTrace( self, trace = 0 ):
        if trace:
            self.step = self.stepWithDump
        else:
            self.step = self.stepNoDump

    def stepWithDump(self):
        self.DumpInstruction()
        self.stepNoDump()

    def stepNoDump(self):        
        op = self.fetch( self.reg.PC )
        self.reg.PC += 1
        self.reg.PRE = self.fetch( self.reg.PC )
        CPUops.instTable[op]( self.reg, self )

    def stepStopped(self):
        pass

    def stepRunTo(self):
        while self.clocks < cyclesPerFrame and self.cart != None:
            if self.reg.PC == self.breakAddress:
                self.execute = self.stepStopped
                return
            self.step()            
        if self.clocks >= cyclesPerFrame:
            self.clocks -= cyclesPerFrame

    def stepFrame(self):
        while self.clocks < cyclesPerFrame and self.cart != None:
            self.step()
        if self.clocks >= cyclesPerFrame:
            self.clocks -= cyclesPerFrame

    def DumpInstruction( self ):
        flags = 'CZIDB1VS'
        P = ''
        for index in range(8):
            if self.reg.P & 1<<index:
                P = P + flags[index]
            else:
                P = P + '-'

        print '%04X' % (self.reg.PC), ': (',
        print 'A:', '%02X' % (self.reg.A),
        print 'X:', '%02X' % (self.reg.X),
        print 'Y:', '%02X' % (self.reg.Y),
        print 'S:', '%02X' % (self.reg.S),
        print 'P:', P,
        print ')', self.instruction( self.reg.PC )[1]

    def read( self, address ):
        if address & 0x1000:
            return self.cart.getRom()[address & 0xFFF]
        elif not address & 0x200 and address & 0x80:
            return self.ram[address & 0x7F]
        else:
            return 0

    instSize = {
        CPUops.Accumulator:1,
        CPUops.Implied:1,
        CPUops.Relative:2,
        CPUops.Immediate:2,
        CPUops.ZeroPage:2,
        CPUops.ZeroPageIndexedX:2,
        CPUops.ZeroPageIndexedY:2,
        CPUops.Absolute:3,
        CPUops.IndexedX:3,
        CPUops.IndexedY:3,
        CPUops.Indirect:3,
        CPUops.PreIndexedX:2,
        CPUops.PostIndexedY:2
        }

    instFormat = {
        CPUops.Accumulator:     ' A',
        CPUops.Implied:         '',
        CPUops.Relative:        ' $%(relative)04X',
        CPUops.Immediate:       ' #$%(short)02X',
        CPUops.ZeroPage:        ' $%(short)02X',
        CPUops.ZeroPageIndexedX:' $%(short)02X, X',
        CPUops.ZeroPageIndexedY:' $%(short)02X, Y',
        CPUops.Absolute:        ' $%(long)04X',
        CPUops.IndexedX:        ' $%(long)04X, X',
        CPUops.IndexedY:        ' $%(long)04X, Y',
        CPUops.Indirect:        ' ($%(long)04X)',
        CPUops.PreIndexedX:     ' ($%(short)02X, X)',
        CPUops.PostIndexedY:    ' ($%(short)02X), Y'
        }

    def instruction(self,address):
        opcode, mode = CPUops.instDefs[ self.read( address ) ]
        size = self.instSize[mode]

        data = ""
        for index in range(size):
            data = data + ' ' + '%02X' % (self.read(address + index))
        imm = self.read( address + 1 ) | (self.read( address + 2 ) << 8)

        if imm & 0x80:
            relative = (address - (imm & 0x7F ^ 0x7F) + 1) & 0xFFFF
        else:
            relative = (address + imm + 2) & 0xFFFF

        return size, opcode + self.instFormat[mode] % {'relative':relative,'long':imm,'short':imm&0xFF}, data

        instFormat = {
            }


print "MESSAGE\tCPU Imported"
