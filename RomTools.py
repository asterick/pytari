#
#   Load file is a Chemistry dialog set for loading roms from pytari,
#   it only requires that you pass a profile set, roms directory, a
#   GUI object so it can register itself, and a callback function
#
#   Threading is used for the profile checking, to keep the GUI
#   responcive
#
#   KNOWN ISSUES:
#       DupeChecker doesn't compare contents of matching CRCS
#

import os, thread, Chemistry, zlib
import Cart, Control, CPUops

class LoadDialog:
    def __init__( self, GUI, directory, profile, callback ):
        self.files = os.listdir( directory )
        self.shown = self.files[:]
        self.profile = profile
        self.callback = callback
        self.directory = directory
        self.list = Chemistry.AtomList((0,0,192,128), self.shown,self.ListCB)
        self.scroll = Chemistry.AtomScroll((196,0,-80),(0,len(self.shown)-1),self.ScrollCB)

        self.controllers = Control.Controllers.keys()
        thread.start_new_thread( self.UpdateThread, () )
        
        self.RomList = {
            'size':(140,36,229,193),
            'icon':(96,32),
            'tray':['iconify','close'],
            'title':'Load rom...',
            'atoms':[
                Chemistry.AtomButton((148,132,64,24),'OK',self.callBack),
                Chemistry.AtomButton((80,132,64,24),'Profile',self.editProfile),
                self.scroll, self.list
                ]
            }

        self.signals = ['NTSC','PAL','SECAM']
        self.AtomName = Chemistry.AtomEdit((0,0,256,24))
        self.AtomMapper = Chemistry.AtomList((124,28,132,40))
        self.AtomCtrlA = Chemistry.AtomList((124,72,132,40),self.controllers)
        self.AtomCtrlB = Chemistry.AtomList((124,116,132,40),self.controllers)
        self.AtomSignal = Chemistry.AtomRadio((16,44),self.signals)

        self.UpdateProfile = {
            'size':(45,45,273,224),
            'icon':Chemistry.DefaultIcon,
            'tray':['close'],
            'title':'Configure Rom Profile',
            'atoms':[
                Chemistry.AtomButton((192,160,64,24),'Update',self.DoProfile),
                Chemistry.AtomButton((192-68,160,64,24),'Remove',self.RemoveProfile),
                Chemistry.AtomLable((110,126),'B'),
                self.AtomCtrlB,
                Chemistry.AtomLable((110,84),'A'),
                self.AtomCtrlA,
                self.AtomSignal,
                self.AtomMapper,
                self.AtomName
                ]
            }
        GUI.register(self.UpdateProfile, visible = Chemistry.False)
        GUI.register(self.RomList, visible = Chemistry.False)
        self.GUI = GUI
    def ShowDialog( self ):
        self.GUI.hide( Chemistry.False, self.RomList )
    def UpdateThread( self ):
        length = len(self.shown)
        keys = self.profile.keys()
        values = range(length)
        values.reverse()
        for index in values:
            try:
                handle = open(  os.path.join(self.directory, self.files[index]), 'rb' )                
            except IOError:
                continue
            data = handle.read()
            crc = zlib.crc32( data )
            handle.close()
            if Cart.Mappers.has_key(len(data)):
                if self.profile.has_key(crc):
                    self.shown[index] = self.profile[crc]['name']
                else:
                    self.shown[index] = '* ' + self.files[index]
            else:
                del self.shown[index]
                del self.files[index]
    def editProfile( self ):
        name = self.files[self.list.get()]
        file = os.path.join(self.directory, name)
        try:
            handle = open( file, 'rb' )
        except IOError:
            return
        self.GUI.hide( Chemistry.False, self.UpdateProfile )
        contents = handle.read()
        size = len(contents)
        self.mappers = []
        for mapperClass in Cart.Mappers[size]:
            self.mappers.append( mapperClass.__doc__ )
        self.UpdatingCRC = zlib.crc32(contents)
        handle.close()
        self.AtomMapper.set( self.mappers )
        if self.profile.has_key(self.UpdatingCRC):
            profile = self.profile[self.UpdatingCRC]
            self.AtomName.set( profile['name'] )
            self.AtomMapper.set( self.mappers.index( profile['mapper'] ) )
            self.AtomCtrlA.set( self.controllers.index( profile['portA'] ) )
            self.AtomCtrlB.set( self.controllers.index( profile['portB'] ) )
            self.AtomSignal.set( self.signals.index( profile['signal'] ) )
        else:
            self.AtomName.set( name )
            self.AtomMapper.set( 0 )
            self.AtomCtrlA.set( 0 )
            self.AtomCtrlB.set( 0 )
            self.AtomSignal.set( 0 )
    def RemoveProfile( self ):
        if self.profile.has_key(self.UpdatingCRC):
            del self.profile[self.UpdatingCRC]
            self.GUI.hide( Chemistry.True, self.UpdateProfile )
        thread.start_new_thread( self.UpdateThread, () )
    def DoProfile( self ):
        self.GUI.hide( Chemistry.True, self.UpdateProfile )
        name = self.AtomName.get()
        ctrla = self.controllers[self.AtomCtrlA.get()]
        ctrlb = self.controllers[self.AtomCtrlB.get()]
        signal = self.signals[ self.AtomSignal.get() ]
        mapper = self.mappers[ self.AtomMapper.get() ]
        self.profile.update({self.UpdatingCRC:{'name':name,'portA':ctrla,'portB':ctrlb,'mapper':mapper,'signal':signal}})
        thread.start_new_thread( self.UpdateThread, () )
    def ListCB( self, value ):
        self.scroll.set( value )
    def ScrollCB( self, value ):
        self.list.set( value )
    def callBack( self ):
        file = os.path.join(self.directory, self.files[self.list.get()])
        try:
            handle = open( file, 'rb' )
        except IOError:
            return
        contents = handle.read()
        handle.close()
        crc = zlib.crc32( contents )
        if self.profile.has_key(crc):
            self.callback( contents, self.profile[crc] )
            self.RomList['visible'] = Chemistry.False
        else:
            self.editProfile()

class DupeCheck:
    def __init__( self, GUI, directory ):
        self.directory = directory
        self.GUI = GUI
        self.UpdateProfile = {
            'size':(192,192,256,64),
            'icon':Chemistry.DefaultIcon,
            'tray':[],
            'title':'Duplicate Finder',
            'atoms':[
                Chemistry.AtomLable((50,4),'Locating Duplicates')
                ]
            }

        self.dupeList = Chemistry.AtomList((0,0,255-16,95),[])
        self.dupeSets = Chemistry.AtomLable((8,231-118-10),'')
        self.DupeManager = {
            'size':(192,148,256,160),
            'icon':Chemistry.DefaultIcon,
            'tray':['iconify','close'],
            'title':'Duplicate Finder',
            'atoms':[
                self.dupeSets,
                Chemistry.AtomButton((256-64-16-1,231-16-20-96,64,24),'Next',self.nextSet),
                Chemistry.AtomButton((256-64-68-16-1,231-16-20-96,64,24),'Remove',self.remove),
                self.dupeList
                ]
            }

        GUI.register( self.UpdateProfile, visible = Chemistry.False )
        GUI.register( self.DupeManager, visible = Chemistry.False )
    def LocateDupes( self ):
        thread.start_new_thread( self.SearchThread, () )
    def remove( self ):
        index = self.dupeList.get()
        os.remove( os.path.join( self.directory, self.list[ index ] ) )
        del self.list[ index ]
        self.dupeList.set( 0 )
        if len(self.list) > 1:
            self.dupeList.set( self.list )
        else:
            self.nextSet()
    def nextSet( self ):
        if len(self.duplicates) == 0:
            self.GUI.hide( Chemistry.True, self.DupeManager )
        else:
            self.list = self.duplicates[0]
            self.dupeList.set( self.list )
            del self.duplicates[0]
            self.dupeSets.set( str(len(self.duplicates)) + " sets" )
    def SearchThread( self ):
        crcDict = {}
        duplicates = []
        self.GUI.hide( Chemistry.False, self.UpdateProfile )
        for file in os.listdir(self.directory):
            try:
                handle = open( os.path.join( self.directory, file ), 'rb' )
            except IOError:
                continue
            contents = handle.read()
            handle.close()
            crc = zlib.crc32(contents)
            if crcDict.has_key(crc):
                crcDict[crc].append(file)
            else:
                crcDict.update({crc:[file]})
        self.duplicates = []
        for key in crcDict:
            if len(crcDict[key]) > 1:
                self.duplicates.append( crcDict[key] )
        self.GUI.hide( Chemistry.True, self.UpdateProfile )
        self.GUI.hide( Chemistry.False, self.DupeManager )
        self.nextSet()
