#
#   Television Interface Adapter Emulation
#
#   This is the 'smartest' processor in the whole system,
#   providing I/O to the joysticks, video signal generation,
#   and audio output.  It has very simple, although robust
#   collision detection.  This will be the hardest part of the
#   project to create.
#
#   Addendum: This turned out to be the third hardest part to
#   create
#
#   pygame, as of right now, does not have an API supportive of
#   realtime audio.  as a result of this, no sound emulation
#   will be supplied.
#
#			  [----]	Object Bit Identifier
#			 @  ||		Priority encoder bit	
#			@|  ||		ORed in on the second half of the palette (SCORE mode)
#			||  ||
#	PF	0x41	01000001	Playfield
#	BL	0x42	01000010	Ball
#	P0	0x04	00000100	Player 1
#	M0	0x08	00001000	Player 1 Missle
#	P1	0x10	00010000	Player 2
#	M1	0x20	00100000	Player 2 Missle
#
#
#       The bits are converted to a number, which is used as an index.
#       The way the palette is generated is pretty self explainitory,
#       I made an excel sheet for the mapping, so It would be rather
#       hard to cut and paste, so I'll spare you.
#


import pygame, random, numpy, thread, Palettes
from pygame.locals import *

bufferSize = 33100
threadWait = 10

NTSC = 0
PAL = 1
SECAM = 2

# The bitmask for a specific object, for fast blitting, and their inverse

PF,PF_	= 0x01, 0x01 ^ 0x7F
BL,BL_	= 0x02, 0x02 ^ 0x7F
P0,P0_	= 0x04, 0x04 ^ 0x7F
M0,M0_	= 0x08, 0x08 ^ 0x7F
P1,P1_	= 0x10, 0x10 ^ 0x7F
M1,M1_	= 0x20, 0x20 ^ 0x7F

# The mask used for collision detection.

PF_BL   = BL_PF     = PF | BL
PF_P0   = P0_PF     = PF | P0
PF_M0   = M0_PF     = PF | M0
PF_P1   = P1_PF     = PF | P1
PF_M1   = M1_PF     = PF | M1
BL_P0   = P0_BL     = BL | P0
BL_M0   = M0_BL     = BL | M0
BL_P1   = P1_BL     = BL | P1
BL_M1   = M1_BL     = BL | M1
P0_M0   = M0_P0     = P0 | M0
P0_P1   = P1_P0     = P0 | P1
P0_M1   = M1_P0     = P0 | M1
M0_P1   = P1_M0     = M0 | P1
M0_M1   = M1_M0     = M0 | M1
P1_M1   = M1_P1     = P1 | M1

# Color Ranges, HI is one extra, due to slice notation
SET_BK_LO,  SET_BK_HI,  SET_BK_STEP     = 0x00, 0x80 + 1, 0x80  # ALWAYS BK
SET_P0L_LO, SET_P0L_HI, SET_P0L_STEP    = 0x04, 0x0C + 1, 0x04  # ALWAYS P0
SET_P0H_LO, SET_P0H_HI, SET_P0H_STEP    = 0x84, 0x8C + 1, 0x04  # ALWAYS P0
SET_P0S_LO, SET_P0S_HI, SET_P0S_STEP    = 0x41, 0x43 + 1, 0x01  # P0 ON SCORE, ELSE PF
SET_P0P_LO, SET_P0P_HI, SET_P0P_STEP    = 0x44, 0x4F + 1, 0x01  # PF ON PRI, ELSE P0
SET_P0B_LO, SET_P0B_HI, SET_P0B_STEP    = 0xC4, 0xCF + 1, 0x01  # P1 ON PRI AND SCORE, ELSE PF ON PRI, ELSE P0
SET_P1L_LO, SET_P1L_HI, SET_P1L_STEP    = 0x10, 0x3C + 1, 0x04  # ALWAYS P1
SET_P1H_LO, SET_P1H_HI, SET_P1H_STEP    = 0x90, 0xBC + 1, 0x04  # ALWAYS P1
SET_P1S_LO, SET_P1S_HI, SET_P1S_STEP    = 0xC1, 0xC3 + 1, 0x01  # P1 ON SCORE, ELSE PF
SET_P1P_LO, SET_P1P_HI, SET_P1P_STEP    = 0xD0, 0xFF + 1, 0x01  # PF ON PRI, ELSE P1
SET_P1B_LO, SET_P1B_HI, SET_P1B_STEP    = 0x50, 0x7F + 1, 0x01  # P0 ON PRI AND SCORE, ELSE PF ON PRI, ELSE P1

BLGrpSet = [1,2,4,8]

BitMaps = numpy.zeros((256,8),numpy.uint8)

Repeats = [0,1,1,2,1,0,2,0]
Stretch = [1,1,1,1,1,2,1,4]
GapSize = [0,8,24,8,56,0,24,0]

for byte in range(256):    
    for bit in range(8):
        if byte & (0x80 >> bit):
            BitMaps[byte][bit] = 0xFF

class AudioChannel:
    def __init__( self, channel ):
        self.channel = channel
##        self.samples = numpy.zeros((bufferSize),numpy.uint8)
##        sound = pygame.sndarray.make_sound(self.samples)
##        self.samples = pygame.sndarray.samples(sound)
##        channel.play( sound, -1 )
##        self.lastTime = pygame.time.get_ticks()
##        self.lastSample = 0
##        self.active = 1
##        thread.start_new_thread( self.audioThread, () )
    def set_rate( self, rate = 31440 ):
        self.rate = value
    def set_vol( self, dummy, value ):
        self.volume = ( value & 0xF ) << 4
    def set_freq( self, dummy, value ):
        self.freq = value & 0x1F
    def set_form( self, dummy, value ):
        self.form = value & 0x1F
    def volume( self, value ):
        self.channel.set_volume( value )

class TIA:
    def __init__( self, clock, ControlA, ControlB ):
        self.clock = clock

        self.place = 0
        
        channelA = AudioChannel( pygame.mixer.Channel(0) )
        channelB = AudioChannel( pygame.mixer.Channel(1) )

        self.mappingWrite[ 0x15 ] = channelA.set_form
        self.mappingWrite[ 0x16 ] = channelB.set_form
        self.mappingWrite[ 0x17 ] = channelA.set_freq
        self.mappingWrite[ 0x18 ] = channelB.set_freq
        self.mappingWrite[ 0x19 ] = channelA.set_vol
        self.mappingWrite[ 0x1A ] = channelB.set_vol

        self.clocks = 0
        self.ControlA = ControlA                # Start off with dummy controllers, these do nothing
        self.ControlB = ControlB                # but return OFF states, only player one gets an IRQ
        self.CollisionMap = {
            PF_BL:0,PF_P0:0,PF_M0:0,PF_P1:0,PF_M1:0,
            BL_P0:0,BL_M0:0,BL_P1:0,BL_M1:0,P0_M0:0,
            P0_P1:0,P0_M1:0,M0_P1:0,M0_M1:0,P1_M1:0
            }
        self.CollisionSet = self.CollisionMap.keys()

        self.hDirty = 0
        self.hPos = 0
        self.vPos = 0

        self.P0Pos = 0        
        self.P1Pos = 0        
        self.M0Pos = 0        
        self.M1Pos = 0        
        self.BLPos = 0
        self.MP0Lock = 0
        self.MP1Lock = 0
        self.EnaM0 = 0
        self.EnaM1 = 0
        self.EnaBLDel = self.EnaBL = 0

        self.MoveP0, self.MoveP1    = 0,0
        self.MoveM0, self.MoveM1    = 0,0
        self.MoveBL                 = 0

        self.RefPF = 1
        self.RefP0 = 1
        self.RefP1 = 1

        self.GapP0 = 0
        self.GapP1 = 0
        self.StretchP0 = 1
        self.StretchP1 = 1
        self.RepeatP0 = 0
        self.RepeatP1 = 0
        
        self.VDelP0 = 0
        self.VDelP1 = 0
        self.VDelBL = 0
        self.P0GrpDel = self.P0GrpBin = numpy.zeros((8)).astype(numpy.uint8)
        self.P1GrpDel = self.P1GrpBin = numpy.zeros((8)).astype(numpy.uint8)

        self.BLGrp = numpy.array([0]).astype(numpy.uint8)
        self.M0Grp = numpy.array([0]).astype(numpy.uint8)
        self.M1Grp = numpy.array([0]).astype(numpy.uint8)
        self.PFGrp = numpy.zeros((80)).astype(numpy.uint8)
        self.P0Grp = self.P0GrpBin
        self.P1Grp = self.P1GrpBin
        self.ScanLine = numpy.zeros(256,numpy.uint8)
        self.ScanLine[80:] = 0x40               # Score encoder for palette

        self.ScoreMode = 0
        self.PlayfieldPriority = 0
        
        self.SetSignal( NTSC )

        self.Screen = pygame.Surface((160,264))
        self.BackBuffer = pygame.Surface((160,264))
        self.UserFrame = pygame.Surface((320,264))
        self.ScreenLine = pygame.Surface((160,1),SWSURFACE,8)
        self.colors = numpy.zeros((256,3),numpy.uint8)

        for x in range(0x80,0x100):
            self.colors[x][:] = (x & 0x7F) << 1
            
        self.ScreenLine.set_palette(self.colors)

        self.ChromaBK = self.ChromaPF = self.ChromaP0 = self.ChromaP1 = numpy.zeros((3),numpy.uint8)

        self.Syncing = 0
        self.Blanking = 0
        
    def SetSignal( self, signal ):
        if signal == NTSC:
            self.palette = Palettes.NTSC
            sampleRate = 31440
            self.BlankPeriod = -40
        elif signal == PAL:
            self.palette = Palettes.PAL
            sampleRate = 31200
            self.BlankPeriod = -48
        else:
            self.palette = Palettes.SECAM
            sampleRate = 31200
            self.BlankPeriod = -48
        # SOUND REINITIALIZATION
            
    def plug( self, ControlA, ControlB ):
        self.ControlA = ControlA
        self.ControlB = ControlB

    def fetch( self, address ):
        self.ClockCatchUp()
        address = address & 0x1F
        if address <= 0x0D:
            return self.mappingRead[ address ]( self )
        return 0
    
    def throw( self, address, value ):
        self.ClockCatchUp()
        self.DumpDirtyBlock()
        address = address & 0x3F
        if address <= 0x2C:
            self.mappingWrite[ address ]( self, value )

    def ClockCatchUp( self ):
        self.hPos = self.hPos + self.clocks
        self.clocks = 0

    def DumpDirtyBlock( self ):
        if self.Syncing or self.Blanking:
            while self.hPos >= 160:
                self.hDirty = 0
                self.vPos = self.vPos + 1
                self.hPos = self.hPos - 160 - 68
            return
        if self.hPos >= 160:            
            slice = self.ScanLine[self.hDirty:160]
            segment = pygame.surfarray.pixels2d(self.ScreenLine)
            segment[self.hDirty:160,0] = slice.astype(numpy.uint8)
            self.FindCollisions( slice )            
            del segment
            self.Screen.blit(self.ScreenLine,(self.hDirty,self.vPos),(self.hDirty,0,160-self.hDirty,1))
            self.vPos = self.vPos + 1
            self.hPos = self.hPos - 160 - 68
            self.hDirty = 0

            self.BlitGRP0()
            self.BlitGRP1()
                        
            while self.hPos >= 160:
                slice = self.ScanLine[self.hDirty:160]
                segment = pygame.surfarray.pixels2d(self.ScreenLine)
                segment[:160,0] = slice.astype(numpy.uint8)
                self.FindCollisions( slice )
                del segment
                self.Screen.blit(self.ScreenLine,(0,self.vPos))
                self.vPos = self.vPos + 1
                self.hPos = self.hPos - 160 - 68
        if self.hPos > 0:
            slice = self.ScanLine[self.hDirty:self.hPos]
            segment = pygame.surfarray.pixels2d(self.ScreenLine)            
            segment[self.hDirty:self.hPos,0] = slice.astype(numpy.uint8)
            del segment
            self.Screen.blit(self.ScreenLine,(self.hDirty,self.vPos),(self.hDirty,0,self.hPos-self.hDirty,1))
            self.FindCollisions( slice )
            self.hDirty = self.hPos

    def FindCollisions( self, dirtySlice ):
        for Mask in self.CollisionSet[:]:
            if Mask in ( dirtySlice & Mask ):
                self.CollisionMap[Mask] = 0x40
                self.CollisionSet.remove(Mask)

    def UpdatePalette( self ):
        if self.ScoreMode:
            if self.PlayfieldPriority:
                self.colors[0x01:0x3F:0x01] = self.ChromaP0
                self.colors[0x41:0x7F:0x01] = self.ChromaP1
            else:
                self.colors[0x01:0x03:0x01] = self.ChromaP0
                self.colors[0x44:0x4F:0x01] = self.ChromaP0
                self.colors[0x40:0x43:0x01] = self.ChromaP1
                self.colors[0x10:0x3F:0x01] = self.ChromaP1
            self.colors[0x04:0x0C:0x01] = self.ChromaP0
            self.colors[0x44:0x4C:0x40] = self.ChromaP0
            self.colors[0x10:0x7C:0x01]	= self.ChromaP1
        elif self.PlayfieldPriority:
            self.colors[0x01:0x7F:0x01] = self.ChromaPF
            self.colors[0x04:0x0C:0x01] = self.ChromaP0
            self.colors[0x44:0x4C:0x40] = self.ChromaP0
            self.colors[0x10:0x7C:0x01]	= self.ChromaP1
        else:
            self.colors[0x01:0x03:0x01] = self.ChromaPF
            self.colors[0x41:0x43:0x01] = self.ChromaPF
            self.colors[0x04:0x0F:0x01] = self.ChromaP0
            self.colors[0x44:0x4F:0x01] = self.ChromaP0
            self.colors[0x10:0x7F:0x01] = self.ChromaP1
        self.ScreenLine.set_palette( self.colors )

    def BlitGRP0( self ):
        if self.VDelP0:
            bitmap = self.P0GrpDel
        else:
            bitmap = self.P0GrpBin

        if self.RepeatP0 == 2:
            if self.hPos < self.P0Pos + 8:
                self.P0Grp [:8] = bitmap
            if self.hPos < self.P0Pos + self.GapP0 + 16:
                self.P0Grp [8+self.GapP0:16+self.GapP0] = bitmap
            if self.hPos < self.P0Pos + self.GapP0 * 2 + 24:
                self.P0Grp [-8:] = bitmap
        elif self.RepeatP0 == 1:
            if self.hPos < self.P0Pos + 8:
                self.P0Grp [:8] = bitmap
            if self.hPos < self.P0Pos + self.GapP0 + 16:
                self.P0Grp [-8:] = bitmap
        else:
            if self.hPos < self.P0Pos + 8 * self.RepeatP0:
                self.P0Grp = numpy.repeat(bitmap, self.RepeatP0).astype(numpy.uint8)
        
    def BlitGRP1( self ):
        if self.VDelP1:
            bitmap = self.P1GrpDel
        else:
            bitmap = self.P1GrpBin

        if self.RepeatP1 == 2:
            if self.hPos < self.P1Pos:
                self.P1Grp[:8] = bitmap
            if self.hPos < self.P1Pos + self.GapP1 + 16:
                self.P1Grp[8+self.GapP1:16+self.GapP1] = bitmap
            if self.hPos < self.P1Pos + self.GapP1 * 2 + 24:
                self.P1Grp[-8:] = bitmap
        elif self.RepeatP1 == 1:
            if self.hPos < self.P1Pos:
                self.P1Grp[:8] = bitmap
            if self.hPos < self.P1Pos + self.GapP1 + 16:
                self.P1Grp[-8:] = bitmap
        else:
            if self.hPos < self.P1Pos + 8 * self.RepeatP1:
                self.P1Grp = numpy.repeat(bitmap, self.RepeatP1).astype(numpy.uint8)

    def VSYNC( self, value ):        
        if not self.Syncing and value & 0x2:
##            test = pygame.Surface((160,264))
##            first = pygame.surfarray.pixels3d( self.Screen )
##            second = pygame.surfarray.pixels3d( self.BackBuffer )
##            pygame.surfarray.pixels3d(test)[:] = first + second
            self.UserFrame = pygame.transform.scale(self.Screen,(320,264))
            self.BackBuffer, self.Screen = self.Screen, self.BackBuffer
            self.Screen.fill((0,0,0))
            self.vPos = self.BlankPeriod
        self.Syncing = value & 0x2
    def VBLANK( self, value ):
        self.Blanking = value & 0x2
        self.ControlA.ground( value & 0x80 )
        self.ControlB.ground( value & 0x80 )
        self.ControlA.latch( value & 0x40 )
        self.ControlB.latch( value & 0x40 )
    def WSYNC( self, value ):
        self.clock( 160 - self.hPos )
        self.ClockCatchUp()
    def RSYNC( self, value ):
        self.hPos = 0
        self.clocks = 0
        self.hDirty = 0
    def NUSIZ0( self, value ):
        self.M0Grp = numpy.repeat([self.EnaM0],BLGrpSet[ value >> 4 & 0x3 ]).astype(numpy.uint8)
        slice = self.ScanLine[self.M0Pos:self.M0Pos+len(self.M0Grp)]
        slice[:] = (slice & M0_).astype(numpy.uint8) | self.M0Grp

        nusiz = value & 0x7
        self.GapP0 = GapSize[nusiz]
        self.StretchP0 = Stretch[nusiz]
        self.RepeatP0 = Repeats[nusiz]

        if self.RepeatP0 == 2:
            self.P0Grp = numpy.zeros( 24 + self.GapP0 * 2, numpy.uint8 )
        elif self.RepeatP0 == 1:
            self.P0Grp = numpy.zeros( 16 + self.GapP0, numpy.uint8 )
        
        self.BlitGRP0()
        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
    def NUSIZ1( self, value ):
        self.M1Grp = numpy.repeat([self.EnaM1],BLGrpSet[ value >> 4 & 0x3 ]).astype(numpy.uint8)
        slice = self.ScanLine[self.M1Pos:self.M1Pos+len(self.M1Grp)]
        slice[:] = (slice & M1_).astype(numpy.uint8) | self.M1Grp

        nusiz = value & 0x7
        self.GapP1 = GapSize[nusiz]
        self.StretchP1 = Stretch[nusiz]
        self.RepeatP1 = Repeats[nusiz]

        if self.RepeatP1 == 2:
            self.P1Grp = numpy.zeros( 24 + self.GapP1 * 2, numpy.uint8 )
        elif self.RepeatP1 == 1:
            self.P1Grp = numpy.zeros( 16 + self.GapP1, numpy.uint8 )
        
        self.BlitGRP1()
        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
    def COLUP0( self, value ):
        self.ChromaP0 = self.palette[value >> 1]
        self.UpdatePalette()
    def COLUP1( self, value ):
        self.ChromaP1 = self.palette[value >> 1]
        self.UpdatePalette()
    def COLUPF( self, value ):
        self.ChromaPF = self.palette[value >> 1]
        self.UpdatePalette()
    def COLUBK( self, value ):
        self.ChromaBK = self.palette[value >> 1]        
        self.colors[0x00:0x41:0x40] = self.ChromaBK
        self.ScreenLine.set_palette(self.colors)
    def CTRLPF( self, value ):
        if value & 0x1:            
            self.RefPF = -1
        else:
            self.RefPF = 1
        self.ScoreMode = value & 0x2
        self.PlayfieldPriority = value & 0x4

        self.UpdatePalette()

        if self.VDelBL:
            self.BLGrp = numpy.repeat([self.EnaBLDel],BLGrpSet[value>>4&0x3]).astype(numpy.uint8)
        else:
            self.BLGrp = numpy.repeat([self.EnaBL],BLGrpSet[value>>4&0x3]).astype(numpy.uint8)

        slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
        slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp
        
        self.ScanLine[:] = (self.ScanLine & PF_).astype(numpy.uint8)
        slice = self.ScanLine[0:80]
        slice[:] = slice | self.PFGrp
        slice = self.ScanLine[80:160]
        slice[:] = slice | self.PFGrp[::self.RefPF]
    def REFP0( self, value ):
        if value & 0x8:
            self.RefP0 = -1
        else:
            self.RefP0 = 1
        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
    def REFP1( self, value ):
        if value & 0x8:
            self.RefP1 = -1
        else:
            self.RefP1 = 1
        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
    def PF0( self, value ):
        self.PFGrp[:16] = numpy.repeat(BitMaps[value][:4] & PF,4)[::-1].astype(numpy.uint8)

        self.ScanLine[:] = (self.ScanLine & PF_).astype(numpy.uint8)
        slice = self.ScanLine[0:80]
        slice[:] = slice | self.PFGrp
        slice = self.ScanLine[80:160]
        slice[:] = slice | self.PFGrp[::self.RefPF]
    def PF1( self, value ):
        self.PFGrp[16:48] = numpy.repeat(BitMaps[value] & PF,4).astype(numpy.uint8)
        
        self.ScanLine[:] = (self.ScanLine & PF_).astype(numpy.uint8)
        slice = self.ScanLine[0:80]
        slice[:] = slice | self.PFGrp
        slice = self.ScanLine[80:160]
        slice[:] = slice | self.PFGrp[::self.RefPF]
    def PF2( self, value ):
        self.PFGrp[48:80] = numpy.repeat(BitMaps[value] & PF,4)[::-1].astype(numpy.uint8)
        
        self.ScanLine[:] = (self.ScanLine & PF_).astype(numpy.uint8)
        slice = self.ScanLine[0:80]
        slice[:] = slice | self.PFGrp
        slice = self.ScanLine[80:160]
        slice[:] = slice | self.PFGrp[::self.RefPF]
    def RESP0( self, value ):
        if self.hPos >= 0:
            self.P0Pos = self.hPos
        else:
            self.P0Pos = 0

        if self.MP0Lock:
            self.M0Pos = (len(self.P0Grp) - len(self.M0Grp)) / 2 + self.P0Pos
            slice = self.ScanLine[self.M0Pos:self.M0Pos+len(self.M0Grp)]
            slice[:] = (slice & M0_).astype(numpy.uint8) | self.M0Grp

        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
    def RESP1( self, value ):
        if self.hPos >= 0:
            self.P1Pos = self.hPos
        else:
            self.P1Pos = 0

        if self.MP1Lock:
            self.M1Pos = (len(self.P1Grp) - len(self.M1Grp)) / 2 + self.P1Pos
            slice = self.ScanLine[self.M1Pos:self.M1Pos+len(self.M1Grp)]
            slice[:] = (slice & M1_).astype(numpy.uint8) | self.M1Grp

        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]        
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
    def RESM0( self, value ):
        if self.MP0Lock:
            return
        elif self.hPos >= 0:            
            self.M0Pos = self.hPos
        else:
            self.M0Pos = 0
        slice = self.ScanLine[self.M0Pos:self.M0Pos+len(self.M0Grp)]
        slice[:] = (slice & M0_).astype(numpy.uint8) | self.M0Grp
    def RESM1( self, value ):
        if self.MP1Lock:
            return
        elif self.hPos >= 0:
            self.M1Pos = self.hPos
        else:
            self.M1Pos = 0
        slice = self.ScanLine[self.M1Pos:self.M1Pos+len(self.M1Grp)]
        slice[:] = (slice & M1_).astype(numpy.uint8) | self.M1Grp
    def RESBL( self, value ):
        if self.hPos >= 0:            
            self.BLPos = self.hPos
        else:
            self.BLPos = 0
        slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
        slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp
    def GRP0( self, value ):
        self.P0GrpBin = (BitMaps[value] & P0).astype(numpy.uint8)
        self.P1GrpDel = self.P1GrpBin

        if self.VDelP1:
            self.BlitGRP1()
            slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]
            slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]

        self.BlitGRP0()
        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
        
    def GRP1( self, value ):
        self.P1GrpBin = (BitMaps[value] & P1).astype(numpy.uint8)
        self.P0GrpDel = self.P0GrpBin
        self.EnaBLDel = self.EnaBL

        if self.VDelBL:
            self.BLGrp[:] = self.EnaBLDel
            slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
            slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp

        if self.VDelP0:
            self.BlitGRP0()
            slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
            slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]

        self.BlitGRP1()
        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
    def ENAM0( self, value ):
        if value & 0x2:
            self.EnaM0 = M0
        else:
            self.EnaM0 = 0
        self.M0Grp[:] = self.EnaM0
        slice = self.ScanLine[self.M0Pos:self.M0Pos+len(self.M0Grp)]
        slice[:] = (slice & M0_).astype(numpy.uint8) | self.M0Grp
    def ENAM1( self, value ):
        if value & 0x2:
            self.EnaM1 = M1
        else:
            self.EnaM1 = 0
        self.M1Grp[:] = self.EnaM1
        slice = self.ScanLine[self.M1Pos:self.M1Pos+len(self.M1Grp)]
        slice[:] = (slice & M1_).astype(numpy.uint8) | self.M1Grp
    def ENABL( self, value ):
        if value & 0x2:
            self.EnaBL = BL
        else:
            self.EnaBL = 0

        if self.VDelBL:
            self.BLGrp[:] = self.EnaBLDel
        else:
            self.BLGrp[:] = self.EnaBL

        slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
        slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp
    def HMP0( self, value ):
        if value & 0x80:
            self.MoveP0 = -(value >> 4 ^ 0xF) - 1
        else:
            self.MoveP0 = (value >> 4)
    def HMP1( self, value ):
        if value & 0x80:
            self.MoveP1 = -(value >> 4 ^ 0xF) - 1
        else:
            self.MoveP1 = (value >> 4)
    def HMM0( self, value ):
        if value & 0x80:
            self.MoveM0 = -(value >> 4 ^ 0xF) - 1
        else:
            self.MoveM0 = (value >> 4)
    def HMM1( self, value ):
        if value & 0x80:
            self.MoveM1 = -(value >> 4 ^ 0xF) - 1
        else:
            self.MoveM1 = (value >> 4)
    def HMBL( self, value ):
        if value & 0x80:
            self.MoveBL = -(value >> 4 ^ 0xF) - 1
        else:
            self.MoveBL = (value >> 4)
    def VDELP0( self, value ):
        self.VDelP0 = value & 0x1
        self.BlitGRP0()        
        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]        
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
    def VDELP1( self, value ):
        self.VDelP1 = value & 0x1
        self.BlitGRP1()        
        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]        
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
    def VDELBL( self, value ):
        self.VDelBL = value & 0x1

        if self.VDelBL:
            self.BLGrp[:] = self.EnaBLDel
        else:
            self.BLGrp[:] = self.EnaBL

        slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
        slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp
    def RESMP0( self, value ):
        self.MP0Lock = value & 0x2
    def RESMP1( self, value ):
        self.MP1Lock = value & 0x2
    def HMOVE( self, value ):
        self.P0Pos = self.P0Pos - self.MoveP0
        self.P1Pos = self.P1Pos - self.MoveP1
        self.M0Pos = self.M0Pos - self.MoveM0
        self.M1Pos = self.M1Pos - self.MoveM1
        self.BLPos = self.BLPos - self.MoveBL

        if self.P0Pos < 0 or self.P0Pos >= 160:
            self.P0Pos = 0
        if self.P1Pos < 0 or self.P1Pos >= 160:
            self.P1Pos = 0
        if self.M0Pos < 0 or self.M0Pos >= 160:
            self.M0Pos = 0
        if self.M1Pos < 0 or self.M1Pos >= 160:
            self.M1Pos = 0
        if self.BLPos < 0 or self.BLPos >= 160:
            self.BLPos = 0

        self.ScanLine = self.ScanLine & PF
        slice = self.ScanLine[self.P0Pos:self.P0Pos+len(self.P0Grp)]
        slice[:] = (slice & P0_).astype(numpy.uint8) | self.P0Grp[::self.RefP0]
        slice = self.ScanLine[self.P1Pos:self.P1Pos+len(self.P1Grp)]
        slice[:] = (slice & P1_).astype(numpy.uint8) | self.P1Grp[::self.RefP1]
        slice = self.ScanLine[self.M0Pos:self.M0Pos+len(self.M0Grp)]
        slice[:] = (slice & M0_).astype(numpy.uint8) | self.M0Grp
        slice = self.ScanLine[self.M1Pos:self.M1Pos+len(self.M1Grp)]
        slice[:] = (slice & M1_).astype(numpy.uint8) | self.M1Grp
        slice = self.ScanLine[self.BLPos:self.BLPos+len(self.BLGrp)]
        slice[:] = (slice & BL_).astype(numpy.uint8) | self.BLGrp
    def HMCLR( self, value ):
        self.MoveP0, self.MoveP1    = 0,0
        self.MoveM0, self.MoveM1    = 0,0
        self.MoveBL                 = 0
    def CXCLR( self, value ):
        for Key in self.CollisionMap:
            self.CollisionMap[Key] = 0
        self.CollisionSet = self.CollisionMap.keys()

    def CXM0P( self ):
        return self.CollisionMap[ M0_P1 ] << 1 | self.CollisionMap[ M0_P0 ]
    def CXM1P( self ):
        return self.CollisionMap[ M1_P1 ] << 1 | self.CollisionMap[ M1_P0 ]
    def CXP0FB( self ):
        return self.CollisionMap[ P0_PF ] << 1 | self.CollisionMap[ P0_BL ]
    def CXP1FB( self ):
        return self.CollisionMap[ P1_PF ] << 1 | self.CollisionMap[ P1_BL ]
    def CXM0FB( self ):
        return self.CollisionMap[ M0_PF ] << 1 | self.CollisionMap[ M0_BL ]
    def CXM1FB( self ):
        return self.CollisionMap[ M1_PF ] << 1 | self.CollisionMap[ M1_BL ]
    def CXBLPF( self ):
        return self.CollisionMap[ BL_PF ] << 1
    def CXPPMM( self ):
        return self.CollisionMap[ P0_P1 ] << 1 | self.CollisionMap[ M0_M1 ]
    def INPT0( self ):
        return self.ControlA.pot1()
    def INPT1( self ):
        return self.ControlA.pot2()
    def INPT2( self ):
        return self.ControlB.pot1()
    def INPT3( self ):
        return self.ControlB.pot2()
    def INPT4( self ):
        return self.ControlA.fire()
    def INPT5( self ):
        return self.ControlB.fire()

    mappingWrite = [
        VSYNC,  VBLANK, WSYNC,  RSYNC,  NUSIZ0, NUSIZ1, COLUP0, COLUP1, COLUPF,
        COLUBK, CTRLPF, REFP0,  REFP1,  PF0,    PF1,    PF2,    RESP0,  RESP1,
        #                       AUDC0,  AUDC1,  AUDF0,  AUDF1,  AUDV0,  AUDV1
        RESM0,  RESM1,  RESBL,  None,   None,   None,   None,   None,   None,
        GRP0,   GRP1,   ENAM0,  ENAM1,  ENABL,  HMP0,   HMP1,   HMM0,   HMM1,
        HMBL,   VDELP0, VDELP1, VDELBL, RESMP0, RESMP1, HMOVE,  HMCLR,  CXCLR
        ]

    mappingRead = [
            CXM0P,  CXM1P,  CXP0FB, CXP1FB, CXM0FB, CXM1FB, CXBLPF, CXPPMM, 
            INPT0,  INPT1,  INPT2,  INPT3,  INPT4,  INPT5
        ]
