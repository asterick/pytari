#
#   Cartridge Mappers, Interfaces a UInt8 numpy array
#
#   This creates a glue from a numpy array to the atari
#   bus, with a dictionary containing the mappers.
#
#   The Cart API is very simple, consisting of only one call,
#   access, which does read and write at the same time, over
#   all of the atari's addressing space
#
#   It can be assumed that only the first 13 bits of the address
#   will be passed
#

import numpy

class TwoK:
    "2K Mirrored"
    def __init__(self, array):
        self.rom = numpy.repeat(numpy.array(array,numpy.uint8),2)
    def access(self, address,value):
        return self.rom[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.rom

#
#   4096 bytes unmapped
#

class FourK:
    "4K Standard"
    def __init__(self, array):
        self.rom = array
    def access(self, address,value):
        return self.rom[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.rom

class Standard:
    "Atari Standard"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = self.rom[0:0x1000]
        self.ram = numpy.zeros((128),numpy.uint8)
        self.banks = len(self.rom) / 0x1000
        if self.banks == 2:
            self.access = self.accessF8
        elif self.banks == 4:
            self.access = self.accessF6
        elif self.banks == 8:
            self.access = self.accessF4
    def accessF8(self, address,value):
        if address == 0x1FF8 or address == 0x1FF9:
            bank = address & 0x1 << 12
            self.romSlice = self.rom[ bank : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def accessF6(self, address,value):
        if address >= 0x1FF6 and address <= 0x1FF9:
            bank = address - 0x1FF6 << 12
            self.romSlice = self.rom[ bank : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def accessF4(self, address,value):
        if address >= 0x1FF4 and address <= 0x1FFB:
            bank = address - 0x1FF4 << 12
            self.romSlice = self.rom[ bank : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.romSlice

class SuperChip:
    "Atari Super-Chip"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = self.rom[:0x1000]
        self.banks = len(self.rom) / 0x1000
        if self.banks == 2:
            self.access = self.accessF8
        elif self.banks == 4:
            self.access = self.accessF6
        elif self.banks == 8:
            self.access = self.accessF4
    def accessF8(self, address,value):
        if address >= 0x1000 and address < 0x1080:
            self.romSlice[address & 0x7F] = value
        elif address >= 0x1080 and address < 0x1100:
            return self.romSlice[address & 0x7F]            
        elif address == 0x1FF8 or address == 0x1FF9:
            bank = address & 0x1 << 12
            self.romSlice[0x80:0x1000]  = self.rom[ bank + 0x80 : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def accessF6(self, address,value):
        if address >= 0x1000 and address < 0x1080:
            self.romSlice[address & 0x7F] = value
        elif address >= 0x1080 and address < 0x1100:
            return self.romSlice[address & 0x7F]            
        elif address >= 0x1FF6 and address <= 0x1FF9:
            bank = address - 0x1FF6 << 12
            self.romSlice[0x80:0x1000]  = self.rom[ bank + 0x80 : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def accessF4(self, address,value):
        if address >= 0x1000 and address < 0x1080:
            self.romSlice[address & 0x7F] = value
        elif address >= 0x1080 and address < 0x1100:
            return self.romSlice[address & 0x7F]            
        elif address >= 0x1FF4 and address <= 0x1FFB:
            bank = (address - 0x1FF4) << 12
            self.romSlice[0x80:0x1000]  = self.rom[ bank + 0x80 : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return [('SuperChip 128 bytes', self.romSlice[:0x80])]
    def getRom(self):
        return self.romSlice

class CBS:
    "CBS"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = self.rom[:0x1000]
    def access(self, address,value):
        if address < 0x1100 and address >= 0x1000:
            return self.romSlice[address & 0xFF]
        elif address < 0x1200 and address >= 0x1100:
            self.romSlice[address & 0xFF] = value
        elif address >= 0x1FF8 and address <= 0x1FFA:
            bank = address - 0x1FF8 << 12
            self.romSlice = self.rom[ bank : bank + 0x1000 ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return [('CBS 128 bytes', self.romSlice[:0x100])]
    def getRom(self):
        return self.romSlice

class Activision:
    "Activision"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = self.rom[ : 0x1000 ]
    def access(self, address, value):
        if address == 0x1FF:
            self.romSlice = self.rom[ : 0x1000 ]
        elif address == 0x1FE:
            self.romSlice = self.rom[ 0x1000 : ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.romSlice

class ParkerBrothers:
    "Parker Brothers"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = numpy.zeros((0x1000),numpy.uint8)
        self.romSlice[0xC00:] = self.rom[0x1C00:]
        self.romSlice[:0xC00] = self.rom[:0xC00]
    def access(self, address,value):
        if address >= 0x1FE0 and address < 0x1FF8:
            page = (address << 7) & 0xC00
            bank = (address & 0x7) << 10
            self.romSlice[ page : page + 0x400 ] = self.rom[ bank : bank + 0x400 ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.romSlice

class TigerVision:
    "TigerVision"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = numpy.zeros((0x1000),numpy.uint8)
        self.romSlice[0x800:] = self.rom[1800:]
    def access(self, address, value):
        if address < 0x40:
            bank = value & 3 << 11
            self.romSlice[:0x800] = self.rom[ bank : bank + 0x800 ]
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.romSlice

class MNetwork:
    "M-Network"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.ram = numpy.zeros((1024),numpy.uint8)
        self.romSlice = numpy.zeros((0x1000),numpy.uint8)
        self.romSlice[:0x800] = self.rom[:0x800]
        self.romSlice[0x800:] = self.rom[0x3800:]
        self.rombank = 0
        self.rambank = 0
    def access(self, address, value):
        if address >= 0x1FE0 and address <= 0x1FE7:
            if self.rombank == 0x3800:
                self.rom[self.romBank:] = self.romSlice[:0x800]
            self.rombank = address & 0x7 << 11
            self.romSlice[:0x800] = self.rom[self.rombank:self.rombank+0x800]
        elif address >= 0x1FF8 and address <= 0x1FFB:
            self.ram[self.rambank:self.rambank+0x1000] = self.romSlice[0x800:0x1100]
            self.rambank = (address & 0x3) << 8
            self.romSlice[0x1000:0x1100] = self.ram[ self.rambank:self.rambank+0x100 ]
        elif address >= 0x1800 and address <= 0x18FF:
            self.romSlice[ address & 0xFF | 0x800] = value
        elif address >= 0x1900 and address <= 0x19FF:
            return self.romSlice[ address & 0xFF | 0x800 ]
        elif address >= 0x1000 and address <= 0x1FFF:
            if self.rombank == 0x3800:
                if not ( address & 0x400 ):
                    self.romSlice[ address & 0x3FF ] = value
        return self.romSlice[ address & 0xFFF ]
    def getRam( self ):
        return [('MNetwork 256 pages', self.ram), ('MNetwork 1024 bank',self.rom[0x3800:])]
    def getRom( self ):
        return self.romSlice

class MegaBoy:
    "MegaBoy"
    def __init__(self, array):
        self.rom = numpy.array(array,numpy.uint8)
        self.romSlice = self.rom[:0x1000]
        self.bank = 0
    def access(self, address,value):
        if address == 0x1FF0:
            self.bank = (self.bank + 1) % 16
            self.romSlice = self.rom[ bank : bank+0x1000 ]
        elif address == 0x1EC:
            return self.bank
        return self.romSlice[ address & 0xFFF ]
    def getRam(self):
        return []
    def getRom(self):
        return self.romSlice

Mappers = {TwoK.__doc__:TwoK,
           FourK.__doc__:FourK,
           Standard.__doc__:Standard,
           MegaBoy.__doc__:MegaBoy,
           ParkerBrothers.__doc__:ParkerBrothers,
           TigerVision.__doc__:TigerVision,
           Activision.__doc__:Activision,
           SuperChip.__doc__:SuperChip,
           CBS.__doc__:CBS,
           MNetwork.__doc__:MNetwork,
           2048:[TwoK],
           4096:[FourK],
           8192:[Standard,SuperChip,ParkerBrothers,TigerVision,Activision],
           12288:[CBS],
           16384:[Standard,SuperChip,MNetwork],
           32768:[Standard,SuperChip],
           65536:[MegaBoy]}

