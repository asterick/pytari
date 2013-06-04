#
#   Chemistry:  A Micro GUI designed for use with pygame
#
#   Chemistry was designed for use with pytari, although
#   it is self contained and can be exported for use with
#   any project.
#   
#   On a side note, this is infact inspired by MacOS (TM),
#   as well as Amiga Workbench (TM). I, however, own
#   neither system.
#
#   Currently, the code is very messy, and unoptomized.
#   I'm writting this with a nasty case of the flu, and
#   like any code monkey, I would rather sit at my terminal
#   than get the much needed bed rest that is required
#
#   Optomizations and Clean ups will be done in parallel
#   development of the GUI, for things I think needs to
#   be revised, look in the known issues section
#
#   Current Atoms
#       Button  List    Lable   Image
#       Edit    Radio   Check   Scroll
#       Spinner
#
#   Notes:
#   o   Mouse event positions are relative to the location the
#       atom was when the MOUSEBUTTONDOWN event occured
#
#   KNOWN ISSUES:
#   o   The focusing window with mouse click has issues
#   o   Need a ClientRect -> WindowSize function
#   o   Need to Move Window Size and Pos properties to diffrent dict keys
#   o   NEED TO COMMENT LOCATIONS OF MAGIC NUMBERS
#   o   Need to remove MAGIC NUMBERS
#   o   There are a lot of order dependant functions
#   o   I would like to see the code a little more modular, as in
#       breaking down the event and paint loops some more, it is
#       currently a tad more bulky than I would like
#

import pygame
from pygame.locals import *
from types import *
from string import *

# Constant definitions

False = 0
True = 1
IconSize = (16, 16)
DefaultIcon = (64, 32)
PopupArrow = (64, 48)
Padding = 4
SeperatorThickness = 2
Seperator = 'Sep'

class Compound:
    "Chemistry: A micro gui"
    def __init__( self, surface, configuration, font, icons, menu = None ):
        self.molicules = []
        self.font = font
        self.icons = icons
        self.SetMenu( menu )
        self.surface = surface
        self.targetSize = surface.get_size()

        colors = configuration['colors']
        desktop = configuration['desktop']

        self.bodyFocus = colors['body.focus']
        self.desktopColor = desktop['color']
        self.titleFocus = colors['title.focus']
        self.focused = colors['focused']
        self.bodyUnfocus = colors['body.unfocus']
        self.titleUnfocus = colors['title.unfocus']
        self.atomFore = colors['widget.fore']
        self.atomBack = colors['widget.back']
        self.highlight = colors['highlight']
        self.desktop = pygame.image.load(desktop['image'])
        self.alignment = desktop['alignment']
        self.text = colors['text']
        self.mouseEvent = None
        self.hidden = False
        self.iconified = []
        self.selectedIcon = None
        self.selectedShown = 0
    def hide( self, hide = True, molicule = None ):
        if molicule == None:
            self.hidden = hide
        elif molicule in self.molicules:
            if hide:
                molicule['visible'] = False
            else:
                molicule['visible'] = True
                if molicule in self.iconified:
                    self.iconified.remove(molicule)
                self.molicules.remove(molicule)
                self.molicules.append(molicule)    
    def register( self, molicule, visible = True ):
        molicule.update({'visible':visible})
        self.molicules.append(molicule)
        molicule.update({'title.rendered':self.font.render(molicule['title'],True,self.text)})
        if molicule['icon'] != None and not (type(molicule['icon']) is TupleType):
            icon = molicule['icon']
            width, height = icon.get_size()
            if width != IconSize[0] or height != IconSize[1]:
                molicule['icon'] = pygame.transform.scale(molicule['icon'],IconSize)
        for atom in molicule['atoms']:
            atom.inherit( self.font, self.atomFore, self.highlight, self.atomBack, self.icons )
    def unregister( self, molicule ):
        self.molicules.remove( molicule )
    def drag( self, event, pos = None ):
        if event.type is MOUSEBUTTONDOWN:
            x, y = pos
            mx, my, width, height = self.mouseCapture['size']
            self.dragging = False
            self.offx, self.offy = 0, 0
            self.oldPos = self.mouseCapture['size'][:2]
            # MAGIC NUMBERS: WINDOW CAPTION SIZE
            if x > 0 and y > 0 and x < width and y < 20:
                icons = self.mouseCapture['tray']
                # MAGIC NUMBERS: TRAY ICON SIZE
                size = len(icons) * 16
                # MAGIC NUMBERS: PADDING AND CAPTION SIZE
                if x >= (width - size - 6) and x < (width - 6) and y >= 4 and y < 20:
                    # MAGIC NUMBERS: PADDING AND ICON SIZE
                    index = (x - width + size + 6) / 16
                    icon = icons[len(icons)-1-index]
                    if icon == "close":
                        self.mouseCapture['visible'] = False
                    elif icon == "iconify":
                        self.mouseCapture['visible'] = False
                        self.iconified.insert(0,self.mouseCapture)
                else:
                    self.dragging = True
        if event.type is MOUSEMOTION:
            if self.dragging:
                dw,dh = self.targetSize
                x, y = self.oldPos
                width, height = self.mouseCapture['size'][2:]
                self.offx, self.offy = self.offx + event.rel[0], self.offy + event.rel[1]
                x, y = x + self.offx, y + self.offy

                fontheight = self.font.get_height()
                if x < 0:
                    x = 0
                elif x > dw - width:
                    x = dw - width
                if y < fontheight:
                    y = fontheight
                elif y > dh - height:
                    y = dh - height

                self.mouseCapture['size'] = x,y, width, height
    def DoEvent( self, event ):
        if self.hidden:
            if event.type is KEYDOWN and event.key is K_ESCAPE:
                self.hidden = False
            return
        if event.type is MOUSEBUTTONDOWN:
            self.mouseEvent = None
            pos = event.pos
            event = self.DoMenuEvent(event)
            if event == None:
                return
            for index in range(len(self.molicules)-1,-1,-1):
                molicule = self.molicules[index]
                dim = molicule['size']
                diff_x, diff_y = pos[0] - dim[0], pos[1] - dim[1]
                if diff_x < 0 or diff_y < 0 or diff_x > dim[2] or diff_y > dim[3]:
                    continue
                self.mouseEvent = self.drag
                self.mouseCapture = molicule
                self.mouseCorner = dim
                self.molicules.pop(index)
                self.molicules.append(molicule)
                atoms = molicule['atoms']
                x, y, width, height = dim
                # MAGIC NUMBERS: CLIENT SPACE
                x, y, width, height = x + 8, y + 28, width - 16, height - 36
                for index in range(len(atoms)):
                    atom = atoms[index]
                    diff_x, diff_y, width, height = atom.dim()
                    dx, dy = pos[0] - diff_x - x, pos[1] - diff_y - y
                    if dx < 0 or dy < 0 or dx > width or dy > height:
                        continue
                    self.mouseEvent = atom.event
                    self.mouseCorner = ( diff_x + x, diff_y + y )
                    index = index + 1
                    if index < len(atoms):
                        slice = atoms[:index]
                        atoms[:index] = []
                        atoms.extend(slice)
                    break
                x, y = event.pos
                corner = (x - self.mouseCorner[0], y - self.mouseCorner[1])
                self.mouseEvent( event, pos = corner )
                break
            if self.selectedIcon != None:
                icon = self.selectedIcon
                self.selectedIcon = None
                icon['visible'] = True
                self.iconified.remove(icon)
                self.molicules.remove(icon)
                self.molicules.append(icon)
            return
        elif event.type is MOUSEMOTION:
            x, y = event.pos
            if self.mouseEvent != None:
                corner = (x - self.mouseCorner[0], y - self.mouseCorner[1])
                self.mouseEvent(event, pos = corner )
                return
            event = self.DoMenuEvent( event )
            if event == None:
                return
            width, height = self.targetSize
            icons = len(self.iconified)
            area = icons * (IconSize[0] + Padding) + self.selectedShown
            if y < height - Padding and y >= height - (IconSize[1] + Padding) and x < width - (IconSize[0] + Padding) and x >= width - (IconSize[0] + Padding) - area:
                cx = width - (IconSize[0] + Padding) * 2
                for index in range(icons):
                    icon = self.iconified[index]
                    if icon == self.selectedIcon:
                        cx = cx - self.selectedShown
                    if x > cx:
                        if icon != self.selectedIcon:
                            self.selectedShown = 0
                        self.selectedIcon = icon
                        break
                    cx = cx - (IconSize[0] + Padding)
            else:
                self.selectedIcon = None
            return
        elif event.type is MOUSEBUTTONUP:
            if self.mouseEvent != None:
                x, y = event.pos
                corner = (x - self.mouseCorner[0], y - self.mouseCorner[1])
                self.mouseEvent(event, pos = corner )
                self.mouseEvent = None
            return
        elif event.type is KEYDOWN:
            if event.key is K_ESCAPE:
                self.hidden = True
                return
            elif event.key is K_TAB:
                if KMOD_CTRL & event.mod:
                    if len(self.molicules) > 1:
                        self.molicules.insert(0,self.molicules.pop(-1))
                else:
                    if len(self.molicules) > 1:
                        molicule = self.molicules[-1]
                        atoms = molicule['atoms']
                        if len(atoms) > 1:
                            atoms.insert(0,atoms.pop(-1))
                return
        atom = self.molicules[-1]['atoms'][-1]
        atom.event(event)

    def DoUpdate(self):
        surface = self.surface
        if not len(self.molicules) or self.hidden:
            return
        surface.fill(self.desktopColor)
        dw, dh = self.targetSize
        if self.alignment == 'centered':
            desktop = self.desktop
            width, height = desktop.get_size()
            pos =  ((dw - width) / 2, (dh - height) / 2)
            surface.blit( desktop, pos )
        elif self.alignment == 'tiled':
            width, height = self.desktop.get_size()
            for x in range( 0, dw, width ):
                for y in range( 0, dh, height ):
                    surface.blit( self.desktop, (x,y) )
        # MAGIC NUMBERS: CORNER LOCATION
        surface.blit( self.icons, (0,dh-IconSize[1]), (96,16) + IconSize )
        # MAGIC NUMBERS: CORNER LOCATION
        surface.blit( self.icons, (dw-IconSize[0],dh-IconSize[1]), (112,16) + IconSize )
        x, y = dw - IconSize[0] - Padding, dh - IconSize[1] - Padding
        for molicule in self.iconified:
            icon = molicule['icon']
            if molicule == self.selectedIcon:
                caption = molicule['title.rendered']
                width, height = caption.get_size()
                x = x - self.selectedShown
                if self.selectedShown > Padding:
                    # MAGIC NUMBERS: CAPTION LOCATION AND HEIGHT
                    surface.blit( caption, (x, y-(Padding/2)), (0, 0, self.selectedShown - Padding, height) )
                if self.selectedShown < (width + Padding):
                    self.selectedShown = self.selectedShown + 1
                x = x - Padding
            x = x - IconSize[0] - Padding
            if icon == None:                
                surface.blit( self.icons, (x, y), DefaultIcon + IconSize )
            elif type(icon) is TupleType:
                surface.blit( self.icons, (x, y), icon + IconSize )
            else:
                surface.blit( icon, (x, y) )
        for molicule in self.molicules[:-1]:
            if molicule['visible']:
                x, y, width, height = molicule['size']
                # MAGIC NUMBERS: CAPTION SIZE
                pygame.draw.rect( surface, self.bodyUnfocus, (x, y+16, width, height - 16))
                # MAGIC NUMBERS: CAPTION SIZE
                pygame.draw.rect( surface, self.titleUnfocus, (x,y,width,20))
                # MAGIC NUMBERS: LINE WEIGHT AND COLOR AND CAPTION SIZE
                pygame.draw.line( surface, (0,0,0), (x, y + 20), (x + width,y + 20), 3 )
                # MAGIC NUMBERS: LINE WEIGHT AND COLOR
                pygame.draw.rect( surface, (0,0,0), (x, y, width, height), 3 )
                if molicule['icon'] == None:                
                    # MAGIC NUMBERS: CAPTION LOCATION
                    surface.blit( molicule['title.rendered'], (x+8, y+2) )
                else:
                    icon = molicule['icon']
                    if type(icon) is TupleType:
                        molicule['icon'] = self.icons.subsurface( icon + IconSize )
                        icon = molicule['icon']
                    # MAGIC NUMBER: ICON LOCATION
                    surface.blit( icon, (x+6, y+2) )
                    # MAGIC NUMBERS: CAPTION LOCATION
                    surface.blit( molicule['title.rendered'], (x+28, y+2) )
                # MAGIC NUMBERS: TRAY ICON SIZE AND PADDING
                tx = x + width - 22
                for button in molicule['tray']:
                    if button == 'iconify':
                        # MAGIC NUMBERS: TRAY LOCATION, AND PADDING
                        surface.blit( self.icons, ( tx, y+2 ), (0,16) + IconSize )
                    if button == 'close':
                        # MAGIC NUMBERS: TRAY LOCATION, AND PADDING
                        surface.blit( self.icons, ( tx, y+2 ), (0,0) + IconSize )
                    tx = tx - IconSize[0]
                # MAGIC NUMBERS: CLIENT AREA SIZE
                x, y, width, height = x + 8, y + 28, width - 16, height - 36
                sw, sh = self.targetSize
                client_area = surface.subsurface( (x, y, width, height) )
                atoms = molicule['atoms']
                for atom in atoms:
                    atom.paint( client_area )
        molicule = self.molicules[-1]
        if molicule['visible']:
            x, y, width, height = molicule['size']
            # MAGIC NUMBERS: CAPTION SIZE
            pygame.draw.rect( surface, self.bodyFocus, (x, y+16, width, height - 16))
            # MAGIC NUMBERS: CAPTION SIZE
            pygame.draw.rect( surface, self.titleFocus, (x,y,width,20))
            # MAGIC NUMBERS: CAPTION SIZE AND LINE WEIGHT
            pygame.draw.line( surface, self.focused, (x, y + 20), (x + width,y + 20), 3 )
            # MAGIC NUMBERS: LINE WEIGHT AND COLOR
            pygame.draw.rect( surface, (255,255,255), (x, y, width, height), 3 )            
            if molicule['icon'] == None:
                # MAGIC NUMBER: CAPTION LOCATION
                surface.blit( molicule['title.rendered'], (x+8, y+2) )
            else:
                icon = molicule['icon']
                if type(icon) is TupleType:
                    molicule['icon'] = self.icons.subsurface( icon + IconSize )
                    icon = molicule['icon']
                # MAGIC NUMBER: ICON LOCATION
                surface.blit( icon, (x+6, y+2) )
                # MAGIC NUMBER: CAPTION LOCATION
                surface.blit( molicule['title.rendered'], (x+28, y+2) )
            # MAGIC NUMBERS: TRAY ICON SIZE AND PADDING
            tx = x + width - 22
            for button in molicule['tray']:
                if button == 'iconify':
                    # MAGIC NUMBERS: TRAY LOCATION
                    surface.blit( self.icons, ( tx, y+2 ), (0,16) + IconSize )
                if button == 'close':
                    # MAGIC NUMBERS: TRAY LOCATION
                    surface.blit( self.icons, ( tx, y+2 ), (0,0) + IconSize )
                # MAGIC NUMBERS: TRAY ICON SIZE
                tx = tx - IconSize[0]
            # MAGIC NUMBERS: CLIENT AREA SIZE
            x, y, width, height = x + 8, y + 28, width - 16, height - 36
            atoms = molicule['atoms']
            if len(atoms):          
                sw, sh = self.targetSize
                client_area = surface.subsurface( (x, y, width, height) )
                for atom in atoms[:-1]:
                    atom.paint( client_area )
                atom = atoms[-1]
                atom.paint( client_area, focus = True )
                if atom.showFocus():
                    dx, dy, width, height = atom.dim()
                    # MAGIC NUMBERS: FOCUS RECTANGLE PADDING
                    dx, dy, width, height = dx + x - 2, dy + y - 2, width + 4, height + 4
                    # MAGIC NUMBERS: LINE WEIGHT
                    surface.set_clip( molicule['size'] )
                    pygame.draw.rect(surface,self.focused,(dx,dy,width,height),2)
                    surface.set_clip()
        else:
            self.molicules = self.molicules[:-1]
            self.molicules.insert(0, molicule)
        self.DoMenu( surface )
        surface.blit( self.icons, (0,0), (96,0) + IconSize )
        surface.blit( self.icons, (dw-16,0), (112,0) + IconSize )        

    def PreprocessMenu( self, menu ):
        if type(menu) is not ListType:
            return
        for index in range(len(menu)):
            if type(menu[index]) is not TupleType:
                continue
            caption, contents = menu[index]
            if type(caption) is StringType:
                caption = None, self.font.render( caption, 1, (0,0,0) )
            elif type(caption) is TupleType:
                icon, text = caption
                if type(icon) is IntType:
                    caption = self.icons.subsurface( caption + IconSize ), None
                elif type(icon) is TupleType:
                    caption = self.icons.subsurface( icon + IconSize ), self.font.render( text, 1, (0,0,0) )
                elif type(text) is StringType:
                    caption = icon, self.font.render( text, 1, (0,0,0) )
            else:
               caption = caption, None
            menu[index] = caption, contents
            self.PreprocessMenu( contents )

    def SetMenu( self, menu ):
        self.selected = None
        self.menu = menu
        self.menuPopups = []
        self.PreprocessMenu( menu )

    def DoMenu( self, surface ):
        fontHeight = self.font.get_height()
        tx, ty = self.targetSize
        pygame.draw.rect(surface,(255,255,255),(0,0,tx,fontHeight))
        if type(self.menu) is ListType:
            x = 24
            for index in range(len(self.menu)):
                caption, contents = self.menu[index]
                icon, text = caption
                left = x - Padding
                if icon != None:
                    NewX = x + icon.get_size()[0] + Padding * 2
                    if index == self.selected:
                        pygame.draw.rect( surface, self.focused, (left, 0, NewX + Padding - left, fontHeight) )
                    surface.blit( icon, (x, 0) )
                    left, x = NewX, NewX
                if text != None:
                    NewX = x + text.get_size()[0]
                    if index == self.selected:
                        pygame.draw.rect( surface, self.focused, (left, 0, NewX + Padding - left, fontHeight) )
                    surface.blit( text, (x, 0) )
                    x = NewX
                x = x + Padding * 4
        for popUp in self.menuPopups:
            menuImage, location, boundBox, extendBox, contents = popUp
            x, y, width, height = extendBox
            surface.blit( menuImage, location )
        pygame.draw.line(surface,(0,0,0),(0,fontHeight),(tx,fontHeight),2)
            
    def DoMenuEvent( self, event ):
        if type(self.menu) is not ListType:
            return event
        # Should do a highlight, but doesn't.
        if event.type is MOUSEMOTION:
            if len(self.menuPopups):
                while len(self.menuPopups) > 0:
                    surface, location, boundBox, extendBox, menu = self.menuPopups[-1]
                    x, y, width, height = boundBox
                    mouseX, mouseY = event.pos
                    if mouseX >= x and mouseY >= y and mouseX < x + width and mouseY < y + height:
        # TESTING FOR INDEX
                        boxX, boxY = location
                        drawY = boxY + Padding
                        if mouseY < drawY:
                            return None
                        for index in range(len(menu)):
                            item = menu[index]
                            if item == Seperator:
                                drawY = drawY + Padding + SeperatorThickness                        
                            else:
                                caption, contents = item
                                menuIcon, menuText = caption
                                if menuText != None:
                                    textWidth, textHeight = menuText.get_size()
                                elif menuIcon != None:
                                    textHeight = IconSize[1]                    
                                drawY = drawY + Padding + textHeight
                            if mouseY < drawY:
                                surface = self.MakeMenuSurface( menu, index )
                                self.menuPopups[-1] = surface, location, boundBox, extendBox, menu
                                return None
        # TESTING FOR INDEX
                        return None
                    x, y, width, height = extendBox
                    if mouseX >= x and mouseY >= y and mouseX < x + width and mouseY < y + height:
                        surface, location, boundBox, extendBox, menu = self.menuPopups[-1]
                        surface = self.MakeMenuSurface( menu )
                        self.menuPopups[-1] = surface, location, boundBox, extendBox, menu
                        return None
                    self.menuPopups.pop()
                self.selected = None
                return event
            else:
                self.selected = None
                fontHeight = self.font.get_height()
                mouseX, mouseY = event.pos
                if mouseY >= fontHeight:
                    return event
                relativeX = 24
                if mouseX < relativeX:
                    return event
                for index in range(len(self.menu)):
                    caption, contents = self.menu[index]
                    icon, text = caption
                    width = 0
                    if icon != None:
                        width = icon.get_size()[0] + Padding * 2
                    if text != None:
                        width = width + text.get_size()[0]
                    if mouseX - relativeX < width:
                        self.selected = index
                        return None
                    elif mouseX - relativeX < (width + Padding * 4):                        
                        return None
                    else:
                        relativeX = relativeX + width + Padding * 4
                return None
        elif event.type is MOUSEBUTTONDOWN:
            mouseX, mouseY = event.pos
            fontHeight = self.font.get_height()
            if len(self.menuPopups) > 0:
                if mouseY < Padding:
                    return None

                popUp = self.menuPopups[-1]
                surface, location, boundBox, extendBox, contents = popUp
                menuX, menuY = location

                x, y, width, height = boundBox
                if mouseX < x or mouseY < y or mouseX >= x + width or mouseY >= y + height:
                    return None

                srcWidth, srcHeight = boundBox[2:]
                relativeY = Padding + menuY

                for index in range(len(contents)):
                    item = contents[index]
                    if item == Seperator:
                        relativeY = relativeY + Padding + SeperatorThickness
                        if mouseY < relativeY:
                            return None
                    else:
                        if mouseY < relativeY + fontHeight:
                            caption, contents = contents[index]
                            if type(contents) is ListType:
                                menuRendered = self.MakeMenuSurface( contents )
                                menuWidth, menuHeight = menuRendered.get_size()
                                location = (menuX + srcWidth - Padding, relativeY)
                                boundBox = location + (menuWidth, menuHeight)
                                extraBox = (menuX, relativeY, srcWidth, fontHeight)
                                self.menuPopups.append( (menuRendered, location, boundBox, extraBox, contents) )
                            elif contents != None:
## DO TUPLE ARGUEMENT BREAK DOWN HERE!
                                contents()
                                self.menuPopups = []
                            return None
                        relativeY = relativeY + Padding + fontHeight
                        if mouseY < relativeY:
                            return None
                return None
            else:
                mouseX, mouseY = event.pos
                if mouseY >= fontHeight:
                    return event
                relativeX = 24
                if mouseX < relativeX:
                    return event
                for index in range(len(self.menu)):
                    caption, contents = self.menu[index]
                    icon, text = caption
                    width = 0
                    if icon != None:
                        width = icon.get_size()[0] + Padding * 2
                    if text != None:
                        width = width + text.get_size()[0]
                    if mouseX - relativeX < width:
                        if type(contents) is ListType:
                            menuRendered = self.MakeMenuSurface( contents )
                            menuWidth, menuHeight = menuRendered.get_size()
                            location = (relativeX, fontHeight)
                            boundBox = (relativeX, fontHeight, menuWidth, menuHeight)
                            extraBox = (relativeX - 16, 0, width + 32, fontHeight)
                            self.menuPopups.append( (menuRendered, location, boundBox, extraBox, contents) )
                        elif contents != None:
## DO TUPLE ARGUEMENT BREAK DOWN HERE!
                            contents()
                        return None
                    elif mouseX - relativeX < (width + Padding * 4):                        
                        return None
                    else:
                        relativeX = relativeX + width + Padding * 4
        return event

    def MakeMenuSurface( self, menu, selected = None ):
        width, height = 0, (len(menu) + 1) * Padding
        for item in menu:
            if item == Seperator:
                height = height + SeperatorThickness
            else:
                caption, contents = item
                icon, text = caption
                textWidth, textHeight = text.get_size()
                height = height + textHeight
                if width < textWidth:
                    width = textWidth

        SurfaceWidth = width + (Padding * 4) + (IconSize[0] * 2)
        menuSurface = pygame.Surface( (SurfaceWidth + 1, height + 1) )
        pygame.draw.rect(menuSurface,(255,255,255),(0,0,SurfaceWidth,height))
        drawY = Padding

        for index in range(len(menu)):
            item = menu[index]
            if item == Seperator:
                pygame.draw.line(menuSurface, (200,200,200),(Padding+IconSize[0]/2,drawY),(Padding+IconSize[0]*3/2+width, drawY),SeperatorThickness)
                drawY = drawY + Padding + SeperatorThickness                        
            else:
                caption, contents = item
                menuIcon, menuText = caption
                if menuText != None:
                    textWidth, textHeight = menuText.get_size()
                elif menuIcon != None:
                    textHeight = IconSize[1]                    
                if selected == index:
                    pygame.draw.rect( menuSurface, self.focused, (0, drawY, SurfaceWidth, textHeight ) )
                if menuIcon != None:
                    menuSurface.blit( menuIcon, (Padding, drawY) )
                if menuText != None:
                    menuSurface.blit( menuText, (Padding * 2 + IconSize[0], drawY) )
                if type(contents) == ListType:
                    menuSurface.blit( self.icons, ( width + IconSize[0] + Padding * 2, drawY + 2), PopupArrow + IconSize )
                drawY = drawY + Padding + textHeight

        pygame.draw.rect(menuSurface,(0,0,0),(0,0,SurfaceWidth,height),2)
        return menuSurface
                
class AtomContainer:
    def __init__( self, pos, atoms = [] ):
        self.atoms = atoms
        self.pos = pos
        self.offset = (0,0)
        self.surface = pygame.Surface(pos[2:],SRCALPHA)
        self.gotInit = False
    def showFocus( self ):
        return False
    def get( self ):
        return self.atoms
    def set( self, value ):
        if type(value) is TupleType:
            self.offset = value
        elif type(value) is InstanceType:
            self.atoms.append(value)
            value.inherit( self.font, self.fore, self.selected, self.back, self.icons )
        else:
            self.atoms = self.atoms + value
            for atom in value:
                atom.inherit( self.font, self.fore, self.selected, self.back, self.icons )
    def dim( self ):
        return self.pos
    def paint( self, surface, focus = False ):
        dx, dy = self.pos[:2]
        dx, dy = dx + self.offset[0], dy + self.offset[1]

        if len(self.atoms) == 0:
            return self.pos
        for atom in self.atoms[:-1]:
            atom.paint( surface, offset = (dx,dy) )
        atom = self.atoms[-1]
        atom.paint( surface, focus = True, offset = (dx,dy) )
        if atom.showFocus():
            dx, dy, width, height = atom.dim()
            dx, dy, width, height = dx + x - 2, dy + y - 2, width + 4, height + 4
            pygame.draw.rect(surface,self.selected,(dx,dy,width,height),2)

        return self.pos
    def inherit( self, font, fore, selected, back, icons ):
        self.font = font
        self.fore = fore
        self.selected = selected
        self.back = back
        self.icons = icons
        for atom in self.atoms:
            atom.inherit( font, fore, selected, back, icons )
    def event( self, event, pos = None ):
        # TODO: FORWARD EVENTS TO THE FOCUSED ATOM
        pass

class AtomImage:
    def __init__( self, image, pos ):
        self.image = image
        self.pos = pos
        self.width, self.height = 0, 0
    def showFocus( self ):
        return False
    def get( self ):
        return self.image
    def set( self, value ):
        if type(value) is TupleType:
            self.image = self.icons.subsurface(value + (16,16))
        else:
            self.image = value
        self.width, self.height = self.image.get_size()
    def dim( self ):
        return self.pos + (self.width, self.height)
    def paint( self, surface, focus = False, offset = (0,0) ):
        draw_x, draw_y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        surface.blit(self.image, self.pos)     
        return self.pos + (self.width, self.height)
    def inherit( self, font, fore, selected, back, icons ):
        self.icons = icons
        self.set(self.image)
    def event( self, event, pos = None ):
        pass

class AtomLable:
    def __init__( self, pos, caption, color = None, font = None, alignment = 'left' ):
        self.caption = caption
        self.color = color
        self.pos = pos
        self.alignment = alignment
        self.font = font
    def showFocus( self ):
        return False
    def dim( self ):
        return self.pos + (self.width, self.height)
    def get( self ):
        return self.caption
    def setFont( self, font ):
        self.font = font
        self.set( self.caption )
    def set( self, value, color = None ):
        if type(value) is TupleType:
            self.color = value
            color = value
        else:
            if color != None:
                self.color = color
            else:
                color = self.color
            self.caption = value
        self.lines = split( value, '\n' )
        width, height = 0, 0
        lineheight = self.font.get_height()
        for index in range(len(self.lines)):
            if self.lines[index] != '':
                self.lines[index] = self.font.render( self.lines[index], True, self.color )
                linewidth, lineheight = self.lines[index].get_size()
                if width < linewidth:
                    width = linewidth
            else:
                self.lines[index] = None
            height = lineheight + height
        self.width, self.height = width, height
    def inherit( self, font, fore, selected, back, icons ):
        if self.font == None:
            self.font = font
        if self.color == None:
            self.color = back
        self.set( self.caption )
    def paint( self, surface, focus = False, offset = (0,0) ):
        x, y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        if self.alignment == 'left':
            for line in self.lines:
                if line != None:
                    surface.blit(line, (x,y))
                y = y + self.font.get_height()
        elif self.alignment == 'right':
            for line in self.lines:
                if line != None:
                    width, height = line.get_size()
                    surface.blit(line, (x - width,y))
                y = y + self.font.get_height()
        elif self.alignment == 'center':            
            for line in self.lines:
                if line != None:
                    width, height = line.get_size()
                    surface.blit(line, ((self.width - width) / 2 + x,y))
                y = y + self.font.get_height()
            
    def event( self, event, pos = None ):
        pass

### MAGIC NUMBERS {{{

class AtomList:
    def __init__( self, size, contents = [], callback = None ):
        self.list = contents
        self.size = size
        self.selected = 0
        self.position = 0
        self.limit = (size[3]-8) / 16 + 1
        self.extra = (size[3]-8) % 16
        self.center = size[3] / 2 - 10
        self.callback = callback
    def showFocus( self ):
        return True
    def dim( self ):
        return self.size
    def get( self ):
        return self.selected
    def set( self, value ):
        if type(value) is ListType:
            self.list = value
            self.selected = 0
            self.position = 0
        else:
            self.selected = value
    def inherit( self, font, fore, selected, back, icons ):
        self.fore = fore
        self.highlight = selected
        self.back = back
        self.font = font
        self.icons = icons
    def paint( self, surface, focus = False, offset = (0,0) ):
        draw_x,draw_y,width,height = self.size
        draw_x,draw_y = draw_x + offset[0], draw_y + offset[1]
        rect = (draw_x,draw_y,width,height)
        pygame.draw.rect(surface, self.back, rect)
        pygame.draw.rect(surface, self.fore, rect,2)

        if not len(self.list):
            return

        rect = draw_x+4, draw_y+4, width-6, height-8
        surface.set_clip(rect)

        goal = self.selected * 16 - self.center

        if goal < 0:
            goal = 0
        elif goal > (len(self.list) - self.limit + 1) * 16 + self.extra:
            if self.extra:
                extra = self.extra - 16
            else:
                extra = 0
            goal = (len(self.list) - self.limit + 1) * 16  + extra

        if goal > self.position:
            diffrence = (goal - self.position - 1)
            self.position = self.position + diffrence / 50 + 1
        elif goal < self.position:
            diffrence = (self.position - goal - 1)
            self.position = self.position - diffrence / 50 - 1
        
        rect = draw_x+4, draw_y + self.selected * 16 - self.position + 2,width-7, 18
        pygame.draw.rect( surface, self.highlight, rect )

        index = self.position / 16
        offset = self.position % 16        

        for y in range(self.limit):
            if ( y + index ) < len(self.list):
                surface.blit(self.font.render(self.list[y+index],True,self.fore),(draw_x+4,draw_y+(y*16)+2-offset))
        
        surface.set_clip()
    def event( self, event, pos = None ):
        if event.type is KEYDOWN:
            if event.key == K_UP and self.selected > 0:
                self.selected = self.selected - 1
            elif event.key == K_DOWN and self.selected < len(self.list)-1:
                self.selected = self.selected + 1
            elif event.key == K_PAGEUP:
                self.selected = self.selected - self.center / 16
                if self.selected < 0:
                    self.selected = 0
            elif event.key == K_PAGEDOWN:
                self.selected = self.selected + self.center / 16
                if self.selected >= len(self.list):
                    self.selected = len(self.list) - 1
            elif event.key == K_HOME:
                self.selected = 0
            elif event.key == K_END:
                self.selected = len(self.list) - 1
            else:
                return
            if self.callback != None:
                self.callback( self.selected )
        if event.type is MOUSEBUTTONDOWN:
            self.selected = (self.position + pos[1]) / 16
            if self.selected >= len(self.list):
                self.selected = len(self.list) - 1
            if self.callback != None:
                self.callback( self.selected )
                

class AtomEdit:
    def __init__( self, size, value = '', callback = None ):
        self.value = value
        self.size = size
        self.blink = 0
        self.callback = None
    def dim( self ):
        return self.size
    def showFocus( self ):
        return True
    def get( self ):
        return self.value
    def set( self, value ):
        self.value = value
    def inherit( self, font, fore, selected, back, icons ):
        self.font, self.fore, self.back = font, fore, back
        x, y, width, height = self.size
    def paint( self, surface, focus = False, offset = (0,0) ):
        draw_x, draw_y, width, height = self.size
        draw_x, draw_y = draw_x + offset[0], draw_y + offset[1]
        rect = self.size
        pygame.draw.rect(surface, self.back, rect)
        pygame.draw.rect(surface, self.fore, rect, 2)
            
        if len(self.value):
            rect = draw_x+4, draw_y+4, width-4, height-4
            surface.set_clip(rect)
            caption = self.font.render(self.value,True,self.fore)
            text_width, height = caption.get_size()
            text_width = text_width + 6
            if text_width > width - 6:
                cursorPoint = ( draw_x + width - 6, draw_y + 4 ), ( draw_x + width - 6, draw_y + 16 )
                rect = (draw_x + 4 - text_width + (width-6), draw_y + 2)
            else:
                cursorPoint = ( draw_x + text_width, draw_y + 4 ), ( draw_x + text_width, draw_y + 16 )
                rect = (draw_x + 4, draw_y + 2)
            surface.blit(caption,rect)
        else:
            cursorPoint = ( draw_x + 6, draw_y + 4 ) , ( draw_x + 6, draw_y + 16 )
        if self.blink >= 30 and focus:
            pygame.draw.line( surface, self.fore, cursorPoint[0], cursorPoint[1], 2 )
        self.blink = (self.blink + 1) % 60
        surface.set_clip()
    def event( self, event, pos = None ):
        if event.type is KEYDOWN:
            if event.key == K_BACKSPACE:
                if len(self.value) > 0:
                    self.value = self.value[:-1]
            else:
                self.value = self.value + event.unicode
            if self.callback != None:
                self.callback( self.value )

class AtomCheck:    
    def __init__( self, pos, contents, callback = None ):
        self.value = False
        self.pos = pos
        self.contents = contents
        self.callback = callback
    def dim( self ):
        return self.pos + ( 20 + self.width, 20 )
    def showFocus( self ):
        return True
    def get( self ):
        return self.value
    def set( self, value ):
        self.value = value
    def inherit( self, font, fore, selected, back, icons ):
        self.icons = icons
        self.contents = font.render( self.contents, True, back )
        self.width = self.contents.get_size()[0]
    def paint( self, surface, focus = False, offset = (0,0) ):
        x, y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        surface.blit( self.icons, (x, y+2), (32,self.value*16) + IconSize )
        surface.blit( self.contents, (x + 20, y) )
    def event( self, event, pos = None ):
        if event.type is KEYDOWN:
            if event.key is K_RETURN or event.key is K_SPACE:
                self.value = not self.value
                if self.callback != None:
                    self.callback( self.value )

        elif event.type is MOUSEBUTTONDOWN:
            x, y = pos
            if x < 16:
                self.value = not self.value
                if self.callback != None:
                    self.callback( self.value )

class AtomRadio:
    def __init__( self, pos, contents = [], callback = None ):
        self.value = 0
        self.pos = pos
        self.font = None
        self.width = 0
        self.rendered = 0
        self.contents = contents
        self.callback = callback
    def showFocus( self ):
        return True
    def prerender( self ):
        if self.font != None:
            self.text = []
            for index in range(len(self.contents)):
                self.text.append( self.font.render(self.contents[index], True, self.back ))
                width, height = self.text[index].get_size()
                if self.width < width:
                    self.width = width
            self.rendered = True
        else:
            self.rendered = False
    def set( self, value ):
        if type(value) is ListType:
            self.contents = value
            self.width = 0
            self.prerender()
        else:
            self.value = value
        if self.value >= len(self.contents):
            self.value = len(self.contents) - 1
    def get( self ):
        return self.value
    def inherit( self, font, fore, selected, back, icons ):
        self.fore, self.back, self.icons, self.font = fore, back, icons, font
        self.prerender()
        pass
    def dim( self ):
        return self.pos + ( 20 + self.width, len(self.contents) * 20 )
    def paint( self, surface, focus = False, offset = (0,0) ):
        x, y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        for index in range(len(self.contents)):
            if self.rendered:
                surface.blit(self.text[index], (x + 20, index * 20 + y))
            if index == self.value:
                surface.blit(self.icons, (x, index * 20 + y + 2), (16,16) + IconSize)
            else:
                surface.blit(self.icons, (x, index * 20 + y + 2), (16,0) + IconSize)
        pass
    def event( self, event, pos = None ):
        if event.type is KEYDOWN:
            if event.key == K_DOWN:
                self.value = ( self.value + 1 ) % len( self.contents )
            elif event.key == K_UP:
                if self.value:
                    self.value = ( self.value - 1 )
                else:
                    self.value = len( self.contents ) - 1
            else:
                return
        elif event.type is MOUSEBUTTONDOWN:
            x, y = pos
            if x < 16 and (y / 20) < len(self.contents):
                self.value = y / 20
            else:
                return
        if self.callback != None:
            self.callback( self.value )

class AtomButton:
    def __init__( self, size, caption, callback = None ):
        self.caption = caption
        self.size = size
        self.callback = callback
        self.pressing = False
    def showFocus( self ):
        return True
    def dim( self ):
        return self.size
    def get( self ):
        return self.caption
    def set( self, value ):
        self.caption = value
        width, height = self.size[2:]
        x, y = self.text.get_size()
        self.text_location = ((width - x) / 2, ( height - y ) / 2)
        self.text = self.font.render(self.caption,True,self.fore)
    def inherit( self, font, fore, selected, back, icons ):
        self.fore, self.back, self.font = fore, back, font
        self.text = font.render(self.caption,True,fore)
        width, height = self.size[2:]
        x, y = self.text.get_size()
        self.text_location = ((width - x) / 2, ( height - y ) / 2)
    def paint( self, surface, focus = False, offset = (0,0) ):
        draw_x,draw_y,width,height = self.size
        draw_x,draw_y = draw_x + offset[0], draw_y + offset[1]
        pygame.draw.rect(surface, self.back, self.size)
        pygame.draw.rect(surface, self.fore, self.size,2)
        text_x, text_y = self.text_location
        text_x, text_y = text_x + draw_x, text_y + draw_y
        surface.set_clip(self.size)
        surface.blit(self.text, (text_x, text_y))
        surface.set_clip()
    def event( self, event, pos = None ):
        if self.callback == None:
            return
        if event.type is KEYDOWN:
            if event.key is K_RETURN or event.key is K_SPACE:
                self.callback()
        elif event.type is MOUSEBUTTONDOWN:
            self.back, self.fore = self.fore, self.back            
            self.text = self.font.render(self.caption,True,self.fore)
            self.pressing = True
        elif event.type is MOUSEBUTTONUP:
            self.pressing = False
            self.back, self.fore = self.fore, self.back            
            self.text = self.font.render(self.caption,True,self.fore)
            width, height = self.size[2:]
            x, y = pos
            if x > 0 and y > 0 and x < width and y < height:
                self.callback()

class AtomSpinner:
    def __init__( self, size, range, callback = None ):
        self.pos = size[:2]
        self.width = size[2]
        self.value = 0
        self.callback = callback
        self.set( range )
    def showFocus( self ):
        return True
    def get( self ):
        return self.value
    def set( self, value ):
        if type(value) is TupleType:
            low, high = value
            if low < high:
                self.range = (low,high)
            else:
                self.range = (high,low)
        else:
            self.value = value
        low, high = self.range
        if self.value < low:
            self.value = low
        elif self.value > high:
            self.value = high
    def dim( self ):
        return self.pos + ( self.width + 10, 16 )
    def inherit( self, font, fore, selected, back, icons ):
        self.fore, self.back, self.font, self.icons = fore, back, font, icons
    def paint( self, surface, focus = False, offset = (0,0) ):
        x, y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        pygame.draw.rect( surface, self.back, self.pos + ( self.width, 16 ))
        pygame.draw.rect( surface, self.fore, self.pos + ( self.width, 16 ),2)
        surface.blit( self.icons, (x + self.width, y), (80,16,10,16))
        value = self.font.render( str(self.value), 1, self.fore )
        width, height = value.get_size()
        loc = (self.width - width) / 2 + x, (16 - height) / 2 + y
        surface.blit( value, loc )
    def event( self, event, pos = None  ):
        if event.type is KEYDOWN:
            low, high = self.range
            if event.key == K_UP and self.value < high:
                self.value = self.value + 1
            elif event.key == K_DOWN and self.value > low:
                self.value = self.value - 1
            elif event.key == K_END:
                self.value = high
            elif event.key == K_HOME:
                self.value = low
        if event.type is MOUSEBUTTONDOWN:
            low, high = self.range
            x, y = pos
            if x > self.width:
                if y < 8:
                    if self.value < high:
                        self.value = self.value + 1  
                else:
                    if self.value > low:
                        self.value = self.value - 1  
class AtomScroll:
    def __init__( self, pos, range, callback = None ):
        self.pos = pos[:2]
        self.length = pos[2]
        self.value = 0
        self.callback = callback
        self.set(range)
    def showFocus( self ):
        return True
    def get( self ):
        return self.value
    def set( self, value ):
        oldValue = self.value
        
        if type(value) is TupleType:
            low, high = value
            if low < high:
                self.range = (low,high)
            else:
                self.range = (high,low)
        else:
            self.value = value
        low, high = self.range
        if self.value < low:
            self.value = low
        elif self.value > high:
            self.value = high

        if self.value != oldValue and self.callback != None:
            self.callback( self.value )
    def dim( self ):
        if self.length < 0:
            return self.pos + ( 16, 48 - self.length )
        else:
            return self.pos + ( 48 + self.length, 16 )
    def inherit( self, font, fore, selected, back, icons ):
        self.fore, self.back, self.selected, self.icons = fore, back, selected, icons
    def paint( self, surface, focus = False, offset = (0,0) ):
        x, y = self.pos[0] + offset[0], self.pos[1] + offset[1]
        length = self.length
        low, high = self.range
        if low == high:
            offset = 0
        else:
            offset = (self.value - low) * length / (high - low)
        if length < 0:
            pygame.draw.rect( surface, self.back, (x, y) + ( 16, 48 - self.length ))
            pygame.draw.rect( surface, self.fore, (x, y) + ( 16, 48 - self.length ),2)
            surface.blit( self.icons, (x, y), ( 48, 0, 16, 16))
            surface.blit( self.icons, (x, y - length + 32), (48, 16, 16, 16))
            surface.blit( self.icons, (x, y + 16 - offset), (80, 0, 16, 16))
        if length > 0:
            pygame.draw.rect( surface, self.back, (x, y) + ( 48 + self.length, 16 ))
            pygame.draw.rect( surface, self.fore, (x, y) + ( 48 + self.length, 16 ),2)
            surface.blit( self.icons, (x, y), ( 64, 0, 16, 16))
            surface.blit( self.icons, (x + length + 32, y), (64, 16, 16, 16))
            surface.blit( self.icons, (x + 16 + offset, y), (80, 0, 16, 16))
    def event( self, event, pos = None ):
        oldValue = self.value
        low, high = self.range
        if event.type is KEYDOWN:
            if event.key == K_DOWN and self.value < high:
                self.value = self.value + 1
            elif event.key == K_UP and self.value > low:
                self.value = self.value - 1
            elif event.key == K_HOME:
                self.value = low
            elif event.key == K_END:
                self.value = high
        elif event.type is MOUSEBUTTONDOWN:
            if self.length < 0:
                self.dragging = False
                if pos[1] < 16:
                    if self.value > low:
                        self.value = self.value - 1
                elif pos[1] > 32 - self.length:
                    if self.value < high:
                        self.value = self.value + 1
                else:
                    self.dragging = True
            else:
                self.dragging = False
                if pos[0] < 16:
                    if self.value > low:
                        self.value = self.value - 1
                elif pos[0] > 32 + self.length:
                    if self.value < high:
                        self.value = self.value + 1
                else:
                    self.dragging = True
        if event.type is MOUSEMOTION or event.type is MOUSEBUTTONDOWN:
            if self.dragging:
                x, y = pos
                if self.length < 0:
                    self.value = (y - 24) * (high - low) / (-self.length) + low
                else:
                    self.value = (x - 24) * (high - low) / (self.length) + low
                if self.value < low:
                    self.value = low
                elif self.value > high:
                    self.value = high
        if self.value != oldValue and self.callback != None:
            self.callback( self.value )

### MAGIC NUMBERS }}}
