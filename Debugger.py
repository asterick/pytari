#
#   This is the debugger module, containing some chemistry dialogs
#   that can be used to do various things with the atari emulator,
#   generally used for bug testing
#

import CPUops, Chemistry, numpy, pygame, TIA
from pygame.locals import *
from string import *
from types import *

class AtomUpdater:
    """This class is used to update a dialog on repaint"""
    def __init__( self, callback ):
        self.callback = callback
    def showFocus( self ):
        return False
    def get( self ):
        return self.callback
    def set( self, callback ):
        self.callback = callback
    def dim( self ):
        return 0,0,1,1
    def inherit( self, font, fore, selected, back, icons ):
        pass
    def paint( self, surface, focus = False ):
        self.callback()
    def event( self, event, pos = None ):
        pass

class RamViewer:
    def __init__( self, GUI, RAM, font, Registers = None ):
        self.containerClass = Chemistry.AtomContainer((0,0,374+16,208),[])
        scrollClass = Chemistry.AtomScroll((362+32,0,-160),(0,0),self.ScrollChanged)

        if type(RAM) is not ListType:
            RAM = [RAM]
        
        self.GUI = GUI
        self.Registers = Registers
        self.RAM = RAM
  
        self.View = {
            'size':(32,32,395+32,208+36),
            'icon':None,
            'title':'Memory',
            'tray':['iconify', 'close'],
            'atoms':[
                AtomUpdater(self.Update),
                self.containerClass,
                scrollClass
                ]
            }

        
        GUI.register( self.View )

        x, y = 48, -4
        for setIndex in range(len(RAM)):
            RamSet = RAM[setIndex]
            name, contents = RamSet
            lableSet = []
            RAM[setIndex] = (numpy.array(contents), contents, lableSet)
            
            if x != 48:
                x = 48, y + 20
            lable = Chemistry.AtomLable((32,y), name, color = (255,255,100), font = font)
            self.containerClass.set(lable)
            y = y + 20
            for index in range(len(contents)):
                if (index % 16) == 0:
                    lable = Chemistry.AtomLable((8,y),'%02X' % index,color = (255,220,150), font = font)
                    self.containerClass.set(lable)
                if index % 2:
                    color = (0,255,255)
                else:
                    color = (255,255,255)
                lable = Chemistry.AtomLable((x,y),'%02X' % (contents[index]),color = color, font = font)
                self.containerClass.set(lable)
                lableSet.append(lable)
                if (index % 16) == 15:
                    x, y = 48, y + 20
                else:
                    x = x + 20
        if y > 216 - 16:
            scrollClass.set((0,y - 216 + 16))
        else:
            self.View['atoms'].remove(scrollClass)
            self.View['size'] = (32,32,395+10,208+36)
        self.containerClass.set((0,0))

    def Unload( self ):
        self.GUI.unregister( self.View )
        
    def Show( self ):
        self.GUI.hide( Chemistry.False, self.dialog )

    def ScrollChanged( self, value ):
        self.containerClass.set((0,-value))

    def Update( self ):
        for RamSet in self.RAM:
            old, new, lableSet = RamSet

            for index in range(len(new)):
                if new[index] != old[index]:
                    lableSet[index].set('%02X' % (new[index]))
                old[index] = new[index]

class Disassembler:
    def __init__( self, gui, atari, font ):
        self.gui = gui
        self.atari = atari

        self.PCLable = Chemistry.AtomLable( (24, 77), '', (0,0,0), font = font )
        self.ALable = Chemistry.AtomLable(  (24, 97), '', (0,0,0), font = font )
        self.XLable = Chemistry.AtomLable(  (24,117), '', (0,0,0), font = font )
        self.YLable = Chemistry.AtomLable(  (24,137), '', (0,0,0), font = font )
        self.SLable = Chemistry.AtomLable(  (24,157), '', (0,0,0), font = font )
        self.PLable = Chemistry.AtomLable(  (24,177), '', (0,0,0), font = font )
        self.focusAddress = self.atari.reg.PC + 1

        self.followPC = Chemistry.AtomCheck(( 0,0),'Follow PC')
        self.dumpTrace = Chemistry.AtomCheck(( 0,20),'Dump Trace',self.ToggleTrace)
        self.scrollBar = Chemistry.AtomScroll((395+16,0,-160),(0,0),self.AddressChanged)

        self.instruction = []
        self.data = []
        self.address = []
        
        for x in range(13):
            self.address.append( Chemistry.AtomLable( (128, x*16 -7), '', color = (0,0,0), font = font ) )
            self.instruction.append( Chemistry.AtomLable( (176, x*16 -7), '', font = font ) )
            self.data.append( Chemistry.AtomLable( (316, x*16 -7), '', color = (0,255,255), font = font ) )

        self.modAddress = Chemistry.AtomEdit((304,215,64,20))

        atoms =     [
                        AtomUpdater(self.Update),
                        Chemistry.AtomRadio(( 0,40),['Cartridge','RIOT Memory'],self.BaseChanged),
                        Chemistry.AtomLable(( 0,84),'PC'),
                        Chemistry.AtomLable(( 0,104),'A'),
                        Chemistry.AtomLable(( 0,124),'X'),
                        Chemistry.AtomLable(( 0,144),'Y'),
                        Chemistry.AtomLable(( 0,164),'S'),
                        Chemistry.AtomLable(( 0,184),'P'),
                        Chemistry.AtomButton((0,212,48,26),'Run',self.atari.run),
                        Chemistry.AtomButton((52,212,48,26),'Stop',self.atari.stop),
                        Chemistry.AtomButton((104,212,48,26),'Step',self.DoStep),
                        Chemistry.AtomButton((156,212,72,26),'Jump To',self.JumpTo),
                        Chemistry.AtomButton((232,212,64,26),'Run To',self.RunTo),
                        self.modAddress,
                        self.PCLable, self.ALable, self.XLable,
                        self.YLable, self.SLable, self.PLable,
                        self.followPC, self.dumpTrace,
                        self.scrollBar
                    ] + self.address + self.data + self.instruction

        self.followPC.set(1)
        self.BaseChanged(0)
        
        self.dialog = {
            'size':(32,32,395+32+16,208+36+32),
            'icon':None,
            'title':'Disassembly',
            'tray':['iconify', 'close'],
            'atoms':atoms
            }

        gui.register(self.dialog)

    def DoStep( self ):
        self.atari.step()
        
    def RunTo( self ):
        self.atari.runTo( int( self.modAddress.get(), 16 ) )

    def JumpTo( self ):
        self.scrollBar.set( int(self.modAddress.get(), 16) )

    def BaseChanged( self, value ):
        if value == 0:
            self.scrollBar.set((0x1000,0x1FFF))
            self.scrollBar.set(0x1000)
        else:
            self.scrollBar.set((0x80,0xFF))
            self.scrollBar.set(0x80)

    def ToggleTrace( self, allowTrace ):
        self.atari.DoTrace(allowTrace)

    def AddressChanged( self, value ):
        self.focusAddress = value
        self.modAddress.set('%04X' % (value))

    def Show( self ):
        self.gui.hide( Chemistry.False, self.dialog )

    def Update( self ):
        self.PCLable.set('%04X' % (self.atari.reg.PC))
        self.ALable.set('%02X' % (self.atari.reg.A))
        self.XLable.set('%02X' % (self.atari.reg.X))
        self.YLable.set('%02X' % (self.atari.reg.Y))
        self.SLable.set('%02X' % (self.atari.reg.S))

        flags = 'CZIDB1VS'
        P = ''
        for index in range(8):
            if self.atari.reg.P & 1<<index:
                P = P + flags[index]
            else:
                P = P + '-'

        self.PLable.set(P)

        if self.followPC.get():
            self.AddressChanged(self.atari.reg.PC)
        address = self.focusAddress

        for index in range(13):
            size, instruction, data = self.atari.instruction( address )
            if address == self.atari.reg.PC:
                self.instruction[index].set(instruction, (255,255,100) )
            else:
                self.instruction[index].set(instruction, (255,255,255) )                
            self.address[index].set('%04X' % (address))
            self.data[index].set(data)
            address = address + size
    def Unload( self ):
        self.gui.unregister( self.dialog )

#
#   TIA Register viewer class
#
#   Needs:
#       Player Size (repeats, gaps, stretching)
#       Sound registers (volume, form, freq)
#

class TIARegisters:
    def __init__( self, gui, tia, font ):
        self.gui = gui
        self.tia = tia
        self.font = font

        self.volumeBar = pygame.Surface((64,16))#image.load('pytari.volume.png')

        self.ColorBK = pygame.Surface((16,16))
        self.ColorPF = pygame.Surface((16,16))
        self.ColorP0 = pygame.Surface((16,16))
        self.ColorP1 = pygame.Surface((16,16))

        self.PosBL  = Chemistry.AtomImage( (48,112), (103,0) )
        self.PosP0  = Chemistry.AtomImage( (64,112), (103,0) )
        self.PosM0  = Chemistry.AtomImage( (80,112), (103,0) )
        self.PosP1  = Chemistry.AtomImage( (96,112), (103,0) )
        self.PosM1  = Chemistry.AtomImage( (112,112), (103,0) )
        self.PosP0t = Chemistry.AtomLable( (64, 140), '0' )
        self.PosP1t = Chemistry.AtomLable( (64, 160), '0' )
        self.PosBLt = Chemistry.AtomLable( (64, 180), '0' )
        self.PosM0t = Chemistry.AtomLable( (64, 200), '0' )
        self.PosM1t = Chemistry.AtomLable( (64, 220), '0' )
        self.HPos   = Chemistry.AtomImage( (32,112), (103,20) )
        self.HPost  = Chemistry.AtomLable( (64, 40), '0' )
        self.VPost  = Chemistry.AtomLable( (96, 40), '0' )

        self.P0Del  = Chemistry.AtomLable( (128, 140), '0' )
        self.P1Del  = Chemistry.AtomLable( (128, 160), '0' )
        self.BLDel  = Chemistry.AtomLable( (128, 180), '0' )

        self.GRPF   = pygame.Surface((320, 16),SWSURFACE, 8)
        self.GRP0   = pygame.Surface((128, 16),SWSURFACE, 8)
        self.GRP1   = pygame.Surface((128, 16),SWSURFACE, 8)
        self.GRP0A  = pygame.Surface((128, 16),SWSURFACE, 8)
        self.GRP1A  = pygame.Surface((128, 16),SWSURFACE, 8)

        self.GRBL   = pygame.Surface((16, 16),SWSURFACE)
        self.GRM0   = pygame.Surface((16, 16),SWSURFACE)
        self.GRM1   = pygame.Surface((16, 16),SWSURFACE)
        self.GRBLA  = pygame.Surface((16, 16),SWSURFACE)

        colors = numpy.zeros((256,3),numpy.uint8)
        colors[1:] = 0xFF

        self.GRPF.set_palette( colors )
        self.GRP0.set_palette( colors )
        self.GRP1.set_palette( colors )
        self.GRP0A.set_palette( colors )
        self.GRP1A.set_palette( colors )

        self.ScanLine = pygame.Surface((456,4),SWSURFACE,8)
        ScanLine = pygame.surfarray.pixels2d(self.ScanLine)
        for x in range(135):
            ScanLine[x] = (x * 0x7F / 134) | 0x80
            ScanLine[x] = ((135-x) * 0x7F / 134) | 0x80
        ScanLine[134] = 0xFF

        self.moveP0 = Chemistry.AtomLable( (96,140), '0' )
        self.moveP1 = Chemistry.AtomLable( (96,160), '0' )
        self.moveBL = Chemistry.AtomLable( (96,180), '0' )
        self.moveM0 = Chemistry.AtomLable( (96,200), '0' )
        self.moveM1 = Chemistry.AtomLable( (96,220), '0' )

        self.matrix = pygame.image.load('pytari.matrix.png')

        self.PFModes = Chemistry.AtomLable( (144,80), '', color = (160,160,160) )

        atoms = [
                AtomUpdater(self.Update),
                Chemistry.AtomLable( (0,80), 'BK' ),
                Chemistry.AtomLable( (64,80), 'PF' ),
                Chemistry.AtomImage( self.ColorBK, (32,80)),
                Chemistry.AtomImage( self.ColorPF, (32+64,80) ),
                Chemistry.AtomImage( self.GRPF, (64+64,80) ),
                
                self.PFModes,

                Chemistry.AtomImage( self.matrix, (360+16, 204-8-32) ),

                Chemistry.AtomLable( (0,140), 'P0' ),
                Chemistry.AtomImage( self.ColorP0, (32,140) ),
                Chemistry.AtomImage( self.GRP0, (96+64,140) ),
                Chemistry.AtomImage( self.GRP0A, (240+64,140) ),

                Chemistry.AtomLable( (0,160), 'P1' ),
                Chemistry.AtomImage( self.ColorP1, (32,160) ),
                Chemistry.AtomImage( self.GRP1, (96+64,160) ),
                Chemistry.AtomImage( self.GRP1A, (240+64,160) ),

                Chemistry.AtomLable( (0,180), 'BL' ),
                Chemistry.AtomImage( self.GRBL, (96+64,180) ),
                Chemistry.AtomImage( self.GRBLA, (128+64,180) ),

                Chemistry.AtomLable( (0,200), 'M0' ),
                Chemistry.AtomImage( self.GRM0, (96+64,200) ),

                Chemistry.AtomLable( (0,220), 'M1' ),
                Chemistry.AtomImage( self.GRM1, (96+64,220) ),

                Chemistry.AtomLable( (0,40), 'Raster' ),

                Chemistry.AtomLable( (128,120), 'Del' ),
                Chemistry.AtomLable( (96,120), 'HM' ),
                Chemistry.AtomLable( (64,120), 'Pos' ),
                self.moveBL, self.moveP0, self.moveM0,
                self.moveP1, self.moveM1,

                Chemistry.AtomImage( self.ScanLine, (8,16) ),
                self.HPos,  self.PosBL,
                self.PosP0, self.PosM0,
                self.PosP1, self.PosM1,

                self.HPost,  self.VPost,
                self.PosP0t, self.PosM0t,
                self.PosP1t, self.PosM1t,
                self.PosBLt,

                self.P0Del, self.P1Del, self.BLDel
            ]

        self.collisionMap = [
            (TIA.BL_PF,1*16,5*16),
            (TIA.BL_M0,2*16,5*16),
            (TIA.BL_P0,3*16,5*16),
            (TIA.BL_M1,4*16,5*16),
            (TIA.BL_P1,5*16,5*16),
            (TIA.PF_M0,2*16,4*16),
            (TIA.PF_P0,3*16,4*16),
            (TIA.PF_M1,4*16,4*16),
            (TIA.PF_P1,5*16,4*16),
            (TIA.M0_P0,3*16,3*16),
            (TIA.M0_M1,4*16,3*16),
            (TIA.M0_P1,5*16,3*16),
            (TIA.P0_M1,4*16,2*16),
            (TIA.P0_P1,5*16,2*16),
            (TIA.M1_P1,5*16,1*16),
        ]

        self.dialog = {
            'size':(32,32,456+32,300),
            'icon':None,
            'title':'TIA Registers',
            'tray':['iconify','close'],
            'atoms':atoms
            }

        gui.register(self.dialog)

    def Unload( self ):
        self.gui.unregister( self.dialog )

    def Show( self ):
        self.gui.hide( Chemistry.False, self.dialog )

    def Update( self ):
        self.tia.ClockCatchUp()
        self.tia.DumpDirtyBlock()
        self.ColorBK.fill( self.tia.ChromaBK )
        self.ColorPF.fill( self.tia.ChromaPF )
        self.ColorP0.fill( self.tia.ChromaP0 )
        self.ColorP1.fill( self.tia.ChromaP1 )
        self.PosBL.pos = (8+(68+self.tia.BLPos)*2,0)
        self.PosP0.pos = (8+(68+self.tia.P0Pos)*2,0)
        self.PosM0.pos = (8+(68+self.tia.M0Pos)*2,0)
        self.PosP1.pos = (8+(68+self.tia.P1Pos)*2,0)
        self.PosM1.pos = (8+(68+self.tia.M1Pos)*2,0)
        self.HPos.pos  = (8+(68+self.tia.hPos)*2,20)
        self.PosBLt.set( str(self.tia.BLPos) )
        self.PosP0t.set( str(self.tia.P0Pos) )
        self.PosM0t.set( str(self.tia.M0Pos) )
        self.PosP1t.set( str(self.tia.P1Pos) )
        self.PosM1t.set( str(self.tia.M1Pos) )
        self.HPost.set( str(self.tia.hPos) )
        self.VPost.set( str(self.tia.vPos) )

        self.ScanLine.set_palette( self.tia.colors )
        scanline = pygame.surfarray.pixels2d( self.ScanLine )
        scanline[136:,0] = numpy.repeat(self.tia.ScanLine[:160],2).astype(numpy.uint8)
        scanline[136:,1] = numpy.repeat(self.tia.ScanLine[:160],2).astype(numpy.uint8)
        scanline[136:,2] = numpy.repeat(self.tia.ScanLine[:160],2).astype(numpy.uint8)
        scanline[136:,3] = numpy.repeat(self.tia.ScanLine[:160],2).astype(numpy.uint8)

        modes = ""
        if self.tia.RefPF == -1:
            modes = 'Reflected  '
        if self.tia.ScoreMode:
            modes += 'Score  '
        if self.tia.PlayfieldPriority:
            modes += 'Priority'
        self.PFModes.set(modes)

        if self.tia.EnaBL:
            self.GRBL.fill((255,255,255))
        else:
            self.GRBL.fill((0,0,0))

        if self.tia.EnaM0:
            self.GRM0.fill((255,255,255))
        else:
            self.GRM0.fill((0,0,0))

        if self.tia.EnaM1:
            self.GRM1.fill((255,255,255))
        else:
            self.GRM1.fill((0,0,0))

        if self.tia.EnaBLDel:
            self.GRBLA.fill((255,255,255))
        else:
            self.GRBLA.fill((0,0,0))

        if self.tia.VDelP0:
            self.P0Del.set('X')
        else:
            self.P0Del.set('')

        if self.tia.VDelP1:
            self.P1Del.set('X')
        else:
            self.P1Del.set('')

        if self.tia.VDelP0:
            self.BLDel.set('X')
        else:
            self.BLDel.set('')

        self.moveBL.set( str(-self.tia.MoveBL) )
        self.moveP0.set( str(-self.tia.MoveP0) )
        self.moveM0.set( str(-self.tia.MoveM0) )
        self.moveP1.set( str(-self.tia.MoveP1) )
        self.moveM1.set( str(-self.tia.MoveM1) )

        PF = pygame.surfarray.pixels2d( self.GRPF )
        P0 = pygame.surfarray.pixels2d( self.GRP0 )
        P1 = pygame.surfarray.pixels2d( self.GRP1 )
        P0A = pygame.surfarray.pixels2d( self.GRP0A )
        P1A = pygame.surfarray.pixels2d( self.GRP1A )

        for slot in self.collisionMap:
            mask, x, y = slot
            if self.tia.CollisionMap[mask]:
                self.matrix.blit( self.gui.icons, (x,y), (112,48,16,16))
            else:
                self.matrix.blit( self.gui.icons, (x,y), (96,48,16,16))                
            

        for x in range(16):
            PF[:,x] = numpy.repeat( self.tia.PFGrp, 4 )
            P0[:,x] = numpy.repeat( self.tia.P0GrpBin, 16 )
            P1[:,x] = numpy.repeat( self.tia.P1GrpBin, 16 )
            P0A[:,x] = numpy.repeat( self.tia.P0GrpDel, 16 )
            P1A[:,x] = numpy.repeat( self.tia.P1GrpDel, 16 )
