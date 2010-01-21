# Script Name: QPopConfigurator
# Host Application: Plugin for Softimage
# Last changed: 2009-11-19 
# Author: Stefan Kubicek
# Mail: stefan@tidbit-images.com

#Fix: oMenu argument causes menu script error in line 3775 when not using Python (e.g. JScript)
#Fix: Selecting a command does not update insert Item button after a fresh start
#Fix: Changing view does not update Menu and MenuItems (should be empty) when no Menu is assigned to the current menu sets context
#Fix: Menu selector is updated even when auto-update checkmark is not set
#TryOut: Check if it is fast enough to have a custom command to execute context scripts (VB, JS, Py) instead of using the ExecuteScriptCode command, which is very slow

#TODO: Check if CommandCollection.Filter with "Custom" is any faster refreshing the Softimage commands lister
#Report When executing context script error is thrown when last character is a whitespace or return char (Problem with text widget?)
#Report Bug: Strange bug in XSI7.01: When a command allows notifications and is executed and undone, it causes itself or other commands to be unfindable through App.Commands("Commandname") (-> returns none)
#Report Bug: Local subdivision _does_ work when assigned to a key! Currently is flagged as not.
#Report duplicate commands (Dice Polygons, Dice Object & Dice Object/Polygons does the same)
#Report duplicate commands (Invert Polygons, Invert All Normals, Invert Selected Polygons; Delete Components vs Delete Component)
#Report (custom?) commands not supporting key assignment are still listed in the keyboard mapping command list (should better not be listed?) 

#TODO: Correctly set default script code when creating Script Items and menus Items with other language than Python.
#TODO: Cleanup function do delete empty script items and menus

#TODO: Reverse menu entry display order for menus C & D? or make it an option?
#TODO: How to find out the currently selected mesh object when in sunComponent selection mode and no component is selected?
#TODO: GET XSI window handle using native Desktop.GetApplicationWindowHandle() function (faster than python and win32 code?)
#TODO: Add a checkbox to enable/disable automatic loading of the config file at startup. What for?

#Cleanup: Rename QpopMenuItem class and related functions (e.g. getQpopMenuItemByName) to "ScriptItem"
#Cleanup: Make all class attributes start with upper-case characters to  

#Perl menu items are untested 
#Japanese font is untested

#TODO: Enable color coding for text fields according to set script language - > Bug in XSI that prevents certain text editor features from being displayed already


# ============================= Helpful code snippets==========================================
"""
if ( !originalsetting ) { 
   prefs.SetPreferenceValue( "scripting.cmdlog", false ); 
"""
#AppInstallCustomPreferences("QPopConfigurator","QPop")
#============================== Plugin Code Start =============================================
import win32com.client
import win32com.server
#from timeit import Timer
import time
from win32com.client import constants as c
from win32com.client import dynamic as d
#import D:\projects\Scripting Projects\XSI\QPop\Application\Plugins\QPopFunctions.py as QF

import os
import os.path
import win32gui
#import win32con
import win32process #, pythoncom
import xml.dom.minidom as DOM

null = None
false = 0
true = 1
True = 1
False = 0

App = Application
Print = getattr(App, 'LogMessage')

#======================================== QPop ActiveX-compliant classes ==============================

class QPopLastUsedItem:
 # Declare list of exported functions:
	_public_methods_ = ['set']
	 # Declare list of exported attributes
	_public_attrs_ = ['item']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []

	def __init__(self):
	 # Initialize exported attributes:
		self.item = None
	
	def set (self, menuItem):
		self.item = menuItem
	
	
class QPopSeparator:
 # Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['type','name','UID']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.type = "QPopSeparator"
		self.UID = XSIFactory.CreateGuid()
		self.name = "NewSeparator"

class QPopSeparators: #Holds existing Separators
 # Declare list of exported functions:
	_public_methods_ = ['addSeparator','deleteSeparator']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()
	
	def addSeparator(self, sep):
		items = self.items
		sepNames = list()
		unwrappedSep = win32com.server.util.unwrap(sep)
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			sepNames.append (unwrappedItem.name)
		if not (unwrappedSep.name in sepNames):
			items.append (sep)
			return True
		else:
			Print("Could not add " + str(unwrappedSep.name) + " to global QPop Menu Sets because a set with that name already exists!", c.siError)
			return False	

	
	def deleteSep (self,sep):
		items = self.items
		try:
			items.remove(sep)
		except:
			Print(sep.name + "could not be found in globals - nothing to delete!", c.siWarning)
		
	
class QPopMenuItem:
 # Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['type','UID', 'name', 'category', 'file', 'language', 'code']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.UID = XSIFactory.CreateGuid()
		self.name = str()
		self.category = str()
		self.file = str()
		self.language = "Python"
		self.code = str()
		self.type = "QPopMenuItem"

class QPopMenuItems:
 # Declare list of exported functions:
	_public_methods_ = ['addMenuItem','deleteMenuItem']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()
	
	def addMenuItem (self, menuItem):
		items = self.items
		itemNames = list()
		unwrappedMenuItem = win32com.server.util.unwrap(menuItem)
		
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			itemNames.append (unwrappedItem.name)
		if not (unwrappedMenuItem.name in itemNames):
			items.append (menuItem)
			return True
		else:
			Print("Could not add " + str(unwrappedMenuItem.name) + " to global QPop Menu Items because an item with that name already exists!", c.siError)
			return False
			
	
	def deleteMenuItem (self, menuItem):
		items = self.items
		try:
			items.remove (menuItem)
		except:
			Print("QPop Menu Item " + str(menuItem.name) + " was not found in global QPop Menu Items and could not be deleted!", c.siError)
			

class QPopMenu:
 # Declare list of exported functions:
	_public_methods_ = ['insertMenuItem','removeMenuItem','removeAllMenuItems','removeMenuItemAtIndex','insertTempMenuItem','removeTempMenuItem','removeTempMenuItemAtIndex','removeAllTempMenuItems']
	 # Declare list of exported attributes
	_public_attrs_ = ['type','UID', 'name', 'items', 'tempItems','code','language','menuItemLastExecuted']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.UID = XSIFactory.CreateGuid()
		self.name = str()
		self.items = list()
		self.tempItems = list()
		self.code = str()
		self.language = "Python"
		self.itemLastExecuted = list()
		self.type = "QPopMenu"
		
	def insertMenuItem (self, index, menuItem):
		items = self.items
		
		if index == None:
			index = 0
		items.insert (index,menuItem)
	
	def removeMenuItem (self, menuItem):
		items = self.items
		try:
			items.remove (menuItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not have a menu item called " + str(menuItem.name) + " that could be removed!!", c.siError)
	
	def removeAllMenuItems (self):
		items = self.items
		try:
			for oItem in items:
				items.remove (oItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not contain any menu items that could be removed!!", c.siError)
	
	def removeAllTempMenuItems (self):
		items = self.tempItems
		try:
			for oItem in items:
				items.remove (oItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not contain any temporary menu items that could be removed!!", c.siError)	
	
	def removeMenuItemAtIndex (self, index):
		items = self.items
		try:
			menuItem = items[index]
			items.remove(menuItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not have a menu item at index " + str(index) + " that could be removed!!", c.siError)
			
	def insertTempMenuItem (self, index, menuItem):
		items = self.tempItems
		
		if index == None:
			index = 0
		items.insert (index,menuItem)
	
	def removeTempMenuItem (self, menuItem):
		items = self.tempItems
		try:
			items.remove (menuItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not have a temporary menu called '" + str(menuItem.name) + "' that could be removed!", c.siError)
	
	def removeTempMenuItemAtIndex (self, index):
		items = self.tempItems
		try:
			menuItem = items[index]
			items.remove(menuItem)
		except:
			Print("QPop Menu '" + str(self.name) + "' does not have a temporary menu item at index " + str(index) + " that could be removed!!", c.siError)

class QPopMenus:
 # Declare list of exported functions:
	_public_methods_ = ['addMenu','deleteMenu']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()

	def addMenu (self, menu):
		items = self.items
		menuNames = list()
		unwrappedMenu = win32com.server.util.unwrap(menu)
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			menuNames.append (unwrappedItem.name)
		if not (unwrappedMenu.name in menuNames):
			items.append (menu)
			return True
		else:
			Print("Could not add " + str(unwrappedMenu.name) + " to global QPop Menus because a menu with that name already exists!", c.siError)
			return False		

	
	def deleteMenu (self, menu):
		items = self.items
		try:
			items.remove (menu)
		except:
			Print("QPop Menu" + str(menu.name) + " was not found in global QPop Menu and could not be deleted!", c.siError)
			
			
 
class QPopMenuSet:
 # Declare list of exported functions:
	_public_methods_ = ['insertMenuAtIndex', 'removeMenuAtIndex','insertContext', 'removeContext', 'setMenu']
	 # Declare list of exported attributes
	_public_attrs_ = ['type','UID', 'name', 'AMenus', 'AContexts', 'BMenus', 'BContexts', 'CMenus', 'CContexts', 'DMenus', 'DContexts']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.type = "QPopMenuSet"
		self.UID = XSIFactory.CreateGuid()
		self.name = str()
		self.AMenus = list()
		self.AContexts = list()
		self.BMenus = list()
		self.BContexts = list()
		self.CMenus = list()
		self.CContexts = list()
		self.DMenus = list()
		self.DContexts = list()
	
	def setMenu (self, index, menu, menuList):
		if menuList == "A":
			self.AMenus[index] = menu
		if menuList == "B":
			self.BMenus[index] = menu
		if menuList == "C":
			self.CMenus[index] = menu
		if menuList == "D":
			self.DMenus[index] = menu
	
	def insertMenuAtIndex (self, index, menu, menuList):
		if menuList == "A":
			self.AMenus.insert(index,menu)
		if menuList == "B":
			self.BMenus.insert(index,menu)
		if menuList == "C":
			self.CMenus.insert(index,menu)
		if menuList == "D":
			self.DMenus.insert(index,menu)
	
	def removeMenuAtIndex (self, index, menuList):
		if menuList == "A":
			self.AMenus.pop(index)
		if menuList == "B":
			self.BMenus.pop(index)
		if menuList == "C":
			self.CMenus.pop(index)
		if menuList == "D":
			self.DMenus.pop(index)
	
	def insertContext (self, index, context, contextList):
		if contextList == "A":
			self.AContexts.insert(index,context)
		if contextList == "B":
			self.BContexts.insert(index,context)
		if contextList == "C":
			self.CContexts.insert(index,context)
		if contextList == "D":
			self.DContexts.insert(index,context)

	def removeContext (self, index, contextList):
		if contextList == "A":
			self.AContexts.pop(index)
		if contextList == "B":
			self.BContexts.pop(index)
		if contextList == "C":
			self.CContexts.pop(index)
		if contextList == "D":
			self.DContexts.pop(index)
			

class QPopMenuSets: #Holds existing MenuSets
 # Declare list of exported functions:
	_public_methods_ = ['addSet','deleteSet']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()
	
	def addSet(self, set):
		items = self.items
		setNames = list()
		unwrappedSet = win32com.server.util.unwrap(set)
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			setNames.append (unwrappedItem.name)
		if not (unwrappedSet.name in setNames):
			items.append (set)
			return True
		else:
			Print("Could not add " + str(unwrappedSet.name) + " to global QPop Menu Sets because a set with that name already exists!", c.siError)
			return False	

	
	def deleteSet (self,set):
		items = self.items
		try:
			items.remove(set)
		except:
			Print(set.name + "could not be found in globals - nothing to delete!", c.siWarning)
		

class QPopMenuDisplayContext:   #Holds the code, which should return True or False (display or not display the menu)
 # Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['type','UID', 'name', 'language', 'code']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.type = "QPopMenuDisplayContext"
		self.UID = XSIFactory.CreateGuid()
		self.name = str()
		self.language = str()
		self.code = str()
		

class QPopMenuDisplayContexts:   #Holds existing display rules
 # Declare list of exported functions:
	_public_methods_ = ['addContext', 'deleteContext']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()
		
	def addContext(self, context):
		items = self.items
		contextNames = list()
		unwrappedContext = win32com.server.util.unwrap(context)
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			contextNames.append (unwrappedItem.name)
		#Print("unwrappedContext.name found is: " + unwrappedContext.name)
		if not(unwrappedContext.name in contextNames):
			items.append (context)
			return True
		else:
			Print("Could not add " + str(unwrappedContext.name) + " to global QPop Menu Display Contexts because a Display Context with that name already exists!", c.siError)
			return False
		
	def deleteContext (self, context):
		items = self.items
		if len(items) > 0:
			items.remove (context)
		

class QPopDisplayEvent:
	# Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['type','UID', 'number','key', 'keyMask']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.type = "QPopDisplayEvent"
		self.UID = XSIFactory.CreateGuid()
		self.number = int()
		self.key = int()
		self.keyMask = int()
		

class QPopDisplayEvents:
	# Declare list of exported functions:
	_public_methods_ = ['addEvent','deleteEvent']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()
	
	def addEvent(self, Event):
		items = self.items
		items.append(Event)
	
	def deleteEvent(self, index):
		items = self.items
		items.pop(index)


class QPopViewSignature:
 # Declare list of exported functions:
	_public_methods_ = ['insertMenuSet','removeMenuSet']
	 # Declare list of exported attributes
	_public_attrs_ = ['UID','type','signature','name','menuSets']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = ['type']
	
	def __init__(self):
		 # Initialize exported attributes:
		self.UID = XSIFactory.CreateGuid()
		self.type = "QPopViewSignature"
		self.signature = str()
		self.name = str()
		self.menuSets = list()
	
	def insertMenuSet (self, index, menuSet):
		menuSets = self.menuSets
		menuSets.insert(index,menuSet)
	
	def removeMenuSet (self, index):
		menuSets = self.menuSets
		menuSets.pop(index)
			

class QPopViewSignatures:
 # Declare list of exported functions:
	_public_methods_ = ['addSignature', 'deleteSignature']
	 # Declare list of exported attributes
	_public_attrs_ = ['items']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.items = list()

	def addSignature (self, signature):
		items = self.items
		signatureNames = list()
		unwrappedSignature = win32com.server.util.unwrap(signature)
		for item in items:
			unwrappedItem = win32com.server.util.unwrap(item)
			signatureNames.append (unwrappedItem.name)
		if not (unwrappedSignature.name in signatureNames):
			items.append (signature)
			return True
		else:
			Print("Could not add " + str(unwrappedSignature.name) + " to global QPop View Signatures because a signature with that name already exists!", c.siError)
			return False
	
	def deleteSignature (self, signature):
		items = self.items
		if len(items) > 0:
			items.remove (signature)	

class QPopConfigStatus:
 # Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['changed']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.changed = False

class QPopCommandPlaceholder:
 # Declare list of exported functions:
	_public_methods_ = []
	 # Declare list of exported attributes
	_public_attrs_ = ['type','name','UID']
	 # Declare list of exported read-only attributes:
	_readonly_attrs_ = []
	
	def __init__(self):
		 # Initialize exported attributes:
		self.type = "CommandPlaceholder"
		self.name = ""
		self.UID = ""



#==================Plugin Initialisation ====================================	

def XSILoadPlugin( in_reg ):
	in_reg.Author = "Stefan Kubicek"
	in_reg.Name = "QPopConfigurator"
	in_reg.Email = "stefan@tidbit-images.com"
	in_reg.URL = "mailto:stefan@tidbit-images.com"
	in_reg.Major = 0
	in_reg.Minor = 98

	#Register the configurator custom property
	in_reg.RegisterProperty( "QPopConfigurator" )
	
	#Register Custom QPop Commands
	#in_reg.RegisterCommand( "QPopGetView", "QPopGetView" )
	in_reg.RegisterCommand( "CreateQPop" , "CreateQPop" )
	#in_reg.RegisterCommand( "QPopDisplayMenuSet" , "QPopDisplayMenuSet" )
	in_reg.RegisterCommand( "QPopExecuteMenuItem" , "QPopExecuteMenuItem" )
	in_reg.RegisterCommand( "QPopConfiguratorCreate", "QPopConfiguratorCreate" )
	
	in_reg.RegisterCommand( "QPopDisplayMenuSet_0", "QPopDisplayMenuSet_0" )
	in_reg.RegisterCommand( "QPopDisplayMenuSet_1", "QPopDisplayMenuSet_1" )
	in_reg.RegisterCommand( "QPopDisplayMenuSet_2", "QPopDisplayMenuSet_2" )
	#in_reg.RegisterCommand( "QPopDisplayMenuSet_3", "QPopDisplayMenuSet_3" )

	in_reg.RegisterCommand( "QPopRepeatLastCommand", "QPopRepeatLastCommand" )
	
	#Register Menus
	in_reg.RegisterMenu( c.siMenuTbGetPropertyID , "QPopConfigurator" , true , true)
	
	#Register events
	in_reg.RegisterEvent( "InitQPop", c.siOnStartup )
	in_reg.RegisterEvent( "DestroyQPop", c.siOnTerminate)
	#in_reg.RegisterEvent( "QPopRecordViewSignature" , c.siOnKeyDown ) 
	in_reg.RegisterEvent( "QPopCheckDisplayEvents" , c.siOnKeyDown ) #Does not work very well, using simple commands to trigger menuSet rendering instead
	
	return True

def XSIUnloadPlugin( in_reg ):
	strPluginName = in_reg.Name
	Print (str(strPluginName) + str(" has been unloaded."),c.siVerbose)
	return true




#=============== QPop Configurator UI Callbacks  =============================

def QPopConfigurator_OnInit( ):
	Print ("QPopConfigurator_OnInit called",c.siVerbose)
	globalQPopConfigStatus = App.GetGlobal("globalQPopConfigStatus")
	globalQPopConfigStatus.changed = True
	
	#Lets seee if this is the first time the QPop PPG is inspected
	bFirstStart = False
	try:	
		bFirstStart = str(App.GetValue("preferences.QPop.FirstStartup")) #We need to use GetValue GetPreferenceValue because the custom preference might not yet be known
	except: #If the preference cannot be found we assume it has never been used before
		bFirstStart = "True"
	
	if bFirstStart == "True": #On very first startup... 
		Print("Qpop First Startup detected, trying to find default config file!", c.siVerbose)
		#... build and set the default config file path from the plugin location
		DefaultConfigFile = GetDefaultConfigFilePath()
		if DefaultConfigFile != "": #Fomally set PPG values and Preference values for FirstStartup and ConfigFile and save them
			App.Preferences.SetPreferenceValue("QPop.QPopConfigurationFile",DefaultConfigFile)
			PPG.QPopConfigurationFile.Value = DefaultConfigFile	
			App.Preferences.SetPreferenceValue("QPop.FirstStartup", False)
			PPG.FirstStartup.Value = False
			App.Preferences.SaveChanges()
			
	RefreshQPopConfigurator()
	PPG.Refresh()

def QPopConfigurator_OnClosed():
	Print ("QPopConfigurator_OnClosed called",c.siVerbose)
	App.Preferences.SetPreferenceValue("QPop.DisplayEventKeys_Record", False)
	App.Preferences.SetPreferenceValue("QPop.RecordViewSignature", False)

def QPopConfigurator_Define( in_ctxt ):
	# Warning! !!Don't set capability flags here (e.g.siReadOnly), it causes errros when copying the property from one object to another (e.g. <parameter>.SetCapabilityFlag (c.siReadOnly,true)   )
	Print ("QPopConfigurator_Define called", c.siVerbose)
	DefaultConfigFile = ""

	oCustomProperty = in_ctxt.Source
	
	oCustomProperty.AddParameter2("QPopEnabled",c.siBool,True,null,null,null,null,c.siClassifUnknown,c.siPersistable)	
	oCustomProperty.AddParameter2("FirstStartup",c.siBool,True,null,null,null,null,c.siClassifUnknown,c.siPersistable)	
	oCustomProperty.AddParameter2("QPopConfigurationFile",c.siString,DefaultConfigFile,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("CommandCategory",c.siString,"_ALL_",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("CommandList",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ShowHotkeyableOnly",c.siBool,True,null,null,null,null,c.siClassifUnknown,c.siPersistable)	
	oCustomProperty.AddParameter2("ShowScriptingNameInBrackets",c.siBool,False,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("View",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuContexts",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ContextConfigurator",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("AutoSelectMenu",c.siBool,True,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuSets",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuSetName",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuSetChooser",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ViewMenuSets",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("MenuSelector",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("QPopMenuA",c.siBool,True,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("QPopMenuB",c.siBool,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("QPopMenuC",c.siBool,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("QPopMenuD",c.siBool,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("Menus",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuChooser",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ContextChooser",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("MenuName",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuItems",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("MenuItem_Category",c.siString,"_ALL_",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuItem_Name",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuItemList",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("MenuItem_Code",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuItem_ScriptLanguage",c.siString,"Python",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuItem_CategoryChooser",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("NewMenuItem_Category",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)

	oCustomProperty.AddParameter2("MenuDisplayContexts",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuDisplayContext_Code",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuDisplayContext_Name",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("MenuDisplayContext_ScriptLanguage",c.siString,"Python",null,null,null,null,c.siClassifUnknown,c.siPersistable)

	#Indepth configuration attributes
	oCustomProperty.AddParameter2("RecordViewSignature",c.siBool,False,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ViewSignatures",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ViewSignatureName",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ViewSignature",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	
	oCustomProperty.AddParameter2("DisplayEvent",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	#oCustomProperty.AddParameter2("DisplayEventName",c.siString,"",null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("DisplayEventKey",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("DisplayEventKeyMask",c.siInt4,0,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("DisplayEventKeys_Record",c.siBool,False,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("ShowQpopMenuString",c.siBool,False,null,null,null,null,c.siClassifUnknown,c.siPersistable)
	oCustomProperty.AddParameter2("IncludeWindowHandle",c.siBool,False,null,null,null,null,c.siClassifUnknown,c.siPersistable)

	
def QPopConfigurator_DefineLayout( in_ctxt ):
	oLayout = in_ctxt.Source
	
	oLayout.Clear()
	oLayout.SetAttribute( c.siUIHelpFile, "http://www.tidbit-images.com/tools/xsi/qpop")
	
	CustomGFXFilesPath = GetCustomGFXFilesPath()
	
	oLayout.AddTab("Main Configuration")
	oLayout.AddGroup()
	oLayout.AddItem("QPopEnabled", "Enable QPop")
	oLayout.AddRow()
	oQPopConfigFile = oLayout.AddItem("QPopConfigurationFile", "QPop Config File", c.siControlFilePath)
	oQPopConfigFile.SetAttribute (c.siUIFileFilter, "QPop Configuration Files (*.xml)|*.xml|All Files (*.*)|*.*||")
	oQPopConfigFile.SetAttribute (c.siUIInitialDir, "C:\\")
	oQPopConfigFile.SetAttribute (c.siUIOpenFile, True)
	oQPopConfigFile.SetAttribute (c.siUIFileMustExist, False)
	oLayout.AddButton("LoadConfig","Load")
	oLayout.AddButton("SaveConfig","Save")
	oLayout.EndRow()
	oLayout.EndGroup()
	
	
	#oLayout.AddRow() #Main Interface Row
	oSC = oLayout.AddGroup("Menu Set Configuration") #Second column for  menu sets editing start#=======================================
	
	oViews = oLayout.AddEnumControl ("View", None, "Configure QPop for",c.siControlCombo)
	oViews.SetAttribute(c.siUILabelMinPixels,100 )
	
	oLayout.AddRow()
	oGr = oLayout.AddGroup("Select Menu Set and Quadrant")
	oGr.SetAttribute(c.siUIWidthPercentage, 15)
	oMSChooser = oLayout.AddEnumControl ("MenuSetChooser", None, "Menu Set", c.siControlCombo)
	oMSChooser.SetAttribute(c.siUINoLabel, True)

	aUIitems = (CustomGFXFilesPath + "QPopMenuA.bmp", 0, CustomGFXFilesPath + "QPopMenuB.bmp", 1, CustomGFXFilesPath + "QPopMenuD.bmp", 3, CustomGFXFilesPath + "QPopMenuC.bmp",2)
	#oLayout.AddSpacer()
	oLayout.AddSpacer()
	oLayout.AddStaticText("       Select Quadrant")
	oMenuSelector = oLayout.AddEnumControl ("MenuSelector", aUIitems, "Quadrant", c.siControlIconList)
	oMenuSelector.SetAttribute(c.siUINoLabel, True)
	oMenuSelector.SetAttribute(c.siUIColumnCnt,2)
	oMenuSelector.SetAttribute(c.siUILineCnt,2)
	oMenuSelector.SetAttribute(c.siUISelectionColor,0x000ff)

	oLayout.EndGroup() #End of Menu Set Configuration Group

	oLayout.AddGroup("Assign QPop Menus to Contexts")
	oLayout.AddSpacer()
	oMenuContexts = oLayout.AddEnumControl ("MenuContexts", None, "",c.siControlListBox)
	oMenuContexts.SetAttribute(c.siUINoLabel, True)
	oMenuContexts.SetAttribute(c.siUICY, 135)
	oLayout.AddRow()
	oLayout.AddButton ("AssignMenu", "Assign Menu to Context")
	oLayout.AddButton ("RemoveMenu", "Remove Menu from Context")
	oLayout.EndRow()
	oLayout.EndGroup()

	oLayout.AddGroup("Menu Items in QPop Menu")
	oLayout.AddRow()
	oItems = oLayout.AddEnumControl ("MenuChooser", None, "Menu",c.siControlCombo)
	#oItems.SetAttribute(c.siUICY, 200)
	oLayout.AddItem ("AutoSelectMenu", "Auto-select from context")
	oLayout.EndRow()
	
	oLayout.AddRow()
	oMenuItems = oLayout.AddEnumControl ("MenuItems", None, "Menu Items",c.siControlListBox)
	oMenuItems.SetAttribute(c.siUINoLabel, True)
	oMenuItems.SetAttribute(c.siUICY, 135)
	oMenuItems.SetAttribute(c.siUIWidthPercentage, 20)
	oLayout.EndRow()
	oLayout.AddRow()

	oInsertCommandButton = oLayout.AddButton ("ItemInsert", "Insert Item")
	oLayout.AddButton ("ItemUp", "Move Up    ")
	oLayout.AddButton ("ItemDown", "Move Down")
	oLayout.AddButton ("RemoveMenuItem", "Remove     ")
	
	oLayout.AddButton ("FindItem", "Find Selected Item")
	oLayout.AddButton("InsertSeparator","Insert Separator")
	oLayout.EndRow()
	oLayout.EndGroup()
	oLayout.EndRow()
	
	oLayout.EndGroup() #Second column for  menu sets editing End #========================================================
	
	#oFG = oLayout.AddGroup("") #First column for  existing assets #=======================================================
	#oFG.SetAttribute(c.siUIShowFrame, False)
	oLayout.AddStaticText("Choose a command, menu, or script item below to add to the selected menu above...")
	oLayout.AddRow()
	oLayout.AddGroup("Existing Softimage Commands")
	#oLayout.AddSpacer()
	oLayout.AddItem ("ShowHotkeyableOnly", "Show Commands supporting key assignment only")
	#oLayout.AddSpacer()
	oLayout.AddItem ("ShowScriptingNameInBrackets", "Show ScriptingName in Brackets")
	oLayout.AddEnumControl ("CommandCategory", None, "Category",c.siControlCombo)
	#oLayout.AddSpacer(0,10)
	oCommands = oLayout.AddEnumControl ("CommandList", None, "Commands",c.siControlListBox)
	oCommands.SetAttribute(c.siUINoLabel, True)
	oLayout.AddRow()
	oLayout.AddButton("InspectCommand", "Inspect Command")
	oLayout.AddButton("ConvertCommandToMenuItem", "Create Script Item from selected Command")
	oLayout.EndRow()
	oLayout.EndGroup()


	oLayout.AddGroup("Existing QPop Menus")
	oLayout.AddSpacer()
	oLayout.AddSpacer()
	oLayout.AddSpacer()
	oMenus = oLayout.AddEnumControl ("Menus", None, "Menus",c.siControlListBox)
	oMenus.SetAttribute(c.siUINoLabel, True)
	#oLayout.AddItem("MenuName", "Name", c.siControlString)
	oLayout.AddRow()
	oLayout.AddButton ("CreateNewMenu", "Create new Menu")
	oLayout.AddButton ("DeleteMenu", "Delete selected Menu")
	oLayout.EndRow() #End Button Row
	oLayout.EndGroup() #End Group Existing Menus
	oLayout.EndRow()
	
	oLayout.AddRow()
	oLayout.AddGroup("Existing QPop Script Items")
	oLayout.AddEnumControl ("MenuItem_Category", None, "Category",c.siControlCombo)
	oMenuItems = oLayout.AddEnumControl ("MenuItemList", None, "Menu Item List",c.siControlListBox)
	oMenuItems.SetAttribute(c.siUINoLabel, True)
	oLayout.AddRow()
	oLayout.AddButton("CreateNewScriptItem","Create new Script Item")
	oLayout.AddButton("DeleteScriptItem","Delete selected Script Item")
	oLayout.EndRow()
	oLayout.EndGroup()
	
	
	oLayout.AddGroup("Edit Menu or Script Item properties")
	oLayout.AddItem("MenuItem_Name", "Item Name", c.siControlString)
	oLayout.AddItem("MenuItem_CategoryChooser", "Category", c.siControlCombo)
	oLayout.AddItem("NewMenuItem_Category", "Change Category", c.siControlString)
	oLayout.EndGroup()
	oLayout.EndRow()

	oLayout.AddGroup("Edit selected QPop Menu or Script Item")
	oLayout.AddRow()
	oLayout.AddButton("ExecuteCode", "Execute")
	oSpacer = oLayout.AddSpacer(10,1)
	oLanguage = oLayout.AddEnumControl("MenuItem_ScriptLanguage", ("Python","Python","JScript","JScript","VBasic","VBScript","Perl","Perl"), "      Scripting Language", c.siControlCombo)
	oLayout.EndRow()
	
	oCodeEditor = oLayout.AddItem("MenuItem_Code", "Code", c.siControlTextEditor)
	#TODO: Implement Text Editor features as a custom JScript or VBS command, Python does not work
	oCodeEditor.SetAttribute(c.siUIToolbar, True )
	oCodeEditor.SetAttribute(c.siUILineNumbering, True )
	oCodeEditor.SetAttribute(c.siUIFolding, True )
	oLayout.EndGroup()
	
	#================================== Display Events Tab =======================================================================================
	oLayout.AddTab("Display Events")
	oLayout.AddGroup("Description")
	oLayout.AddStaticText("There are two ways of invoking menu sets:\n\n1. Using 'Display Events', as described below. This is the recommended way for Softimage 7.0 to 2010 without SP1.\n\n2. Using commands, which can be bound to hotkeys of your choice using the standard Keyboard Mapping dialogue.\nLook in the 'Custom Script Commands' category for commands called 'QPopDisplayMenuSet_0 - 3').\nThis is the recommended way for Softimage versions 2010-SP1 and above,\nalthough display events or even a combination of commands and display events work equally fine.\n\nNote: You can also use commands in Softimage prior 2010-SP1, but due to a bug in these earlier versions PPG's won't open automatically after command execution -> Not recommended.\nAlso note that display events override your command mapping for the assigned key(s) as long as QPop is enabled.\n",0,230 )
	oLayout.EndGroup()
	oLayout.AddGroup("QPop Display Events")
	
	oLayout.AddStaticText("\nSet the 'Record' check mark below, then press your desired key or key combination ( key + Shift, Alt or Ctrl) for the selected menu display event.\n\nNote: The record check mark will be automatically unchecked when a valid key or key combination has been pressed, or when leaving this tab or closing the configurator.",0,100)
	oLayout.AddRow()
	
	oLayout.AddGroup("",False,0)
	oEvents = oLayout.AddEnumControl ("DisplayEvent", None, "DisplayEvents", c.siControlListBox)
	oEvents.SetAttribute(c.siUINoLabel, True)
	oLayout.EndGroup()
	
	oLayout.AddGroup("",False,0)
	oLayout.AddItem("DisplayEventKeys_Record","Record")
	oKey = oLayout.AddItem("DisplayEventKey", "Key", c.siControlString)
	oKeyMask = oLayout.AddItem("DisplayEventKeyMask", "KeyMask", c.siControlString)
	oLayout.AddButton("AddDisplayEvent","Add Display Event")
	oLayout.AddButton("DeleteDisplayEvent","Delete selected Display Event")
	oLayout.EndGroup()
	
	oLayout.EndRow()
	
	oLayout.EndGroup()

#========================= Low-Level Configuration Tab =============================================================================	

	oLayout.AddTab("Low-Level Configuration")
	oLayout.AddGroup("Assign Qpop Menu Sets to Views")
	oLayout.AddRow()
	oLayout.AddGroup("Existing Views")
	oViews = oLayout.AddEnumControl ("ViewSignatures", None, "Views", c.siControlListBox)
	oViews.SetAttribute(c.siUINoLabel, True)
	oLayout.AddRow()
	oLayout.AddButton("AddQPopViewSignature", "Create New View")
	oLayout.AddButton("DelQPopViewSignature", "Delete Selected View")
	oLayout.EndRow()
	oLayout.AddItem("ViewSignatureName","Name")
	#oLayout.AddRow()
	oRecCheck = oLayout.AddItem("RecordViewSignature","Record Signature")
	oRecCheck.SetAttribute(c.siUIWidthPercentage,1)
	oLayout.AddItem("ViewSignature","Signature")
	
	#oLayout.AddButton("PickQPopViewSignature", "Pick")
	#oLayout.EndRow()
	oLayout.EndGroup()
	
	oLayout.AddGroup("QPop Menu Set(s) in selected View")
	oSets = oLayout.AddEnumControl ("ViewMenuSets", None, "Menu Sets",c.siControlListBox)
	oSets.SetAttribute(c.siUINoLabel, True)
	oLayout.AddRow()
	oLayout.AddButton ("InsertSetInView", "Insert Qpop Menu Set")
	oLayout.AddButton ("RemoveSetInView", "Remove QPop Menu Set")
	oLayout.AddButton ("MoveSetUpInView", "Move Up")
	oLayout.AddButton ("MoveSetDownInView", "Move Down")
	oLayout.EndRow()
	oLayout.EndGroup()
	oLayout.EndRow()
	oLayout.EndGroup()
	
	oLayout.AddGroup("Assign QPop Menu Contexts to Menu Sets")
	oLayout.AddRow() #New Row of Groups
	
	oLayout.AddGroup("Existing QPop Menu Sets")
	oMenuSets = oLayout.AddEnumControl ("MenuSets", None, "", c.siControlListBox)
	oMenuSets.SetAttribute(c.siUINoLabel, True)
	oMenuSets.SetAttribute(c.siUICY, 152)
	oLayout.AddItem("MenuSetName","Name")
	oLayout.AddRow()
	oLayout.AddButton("CreateMenuSet", "Create new Menu Set")
	oLayout.AddButton("DeleteMenuSet", "Delete Menu Set")
	oLayout.EndRow()
	oLayout.EndGroup() #Edit QpopMenuSets
	
	oLayout.AddGroup ("QPop Menu Contexts in selected Menu Set")
	oLayout.AddRow()
	
	oQG = oLayout.AddGroup("", False, 25)
	#oQG.SetAttribute(c.siUIWidthPercentage, 25)
	oLayout.AddStaticText("       Select Quadrant")
	oMenuSelector2 = oLayout.AddEnumControl ("MenuSelector", aUIitems, "Select Quadrant", c.siControlIconList)
	oMenuSelector2.SetAttribute(c.siUINoLabel, True)
	oMenuSelector2.SetAttribute(c.siUIColumnCnt,2)
	oMenuSelector2.SetAttribute(c.siUILineCnt,2)
	oMenuSelector2.SetAttribute(c.siUISelectionColor,0x000ff)
	oLayout.EndGroup()
	
	oContexts = oLayout.AddEnumControl("ContextConfigurator",None,"",c.siControlListBox)
	oContexts.SetAttribute(c.siUINoLabel,True)
	oContexts.SetAttribute(c.siUICY, 152)
	oLayout.EndRow()
	
	oLayout.AddRow()
	oLayout.AddButton ("InsertMenuContext", "Insert Context")
	oLayout.AddButton ("RemoveMenuContext", "Remove Context")
	oLayout.AddButton ("CtxUp", "Move Up")
	oLayout.AddButton ("CtxDown", "Move Down")
	oLayout.EndRow()
	oLayout.EndGroup() #Menu Contexts
	
	oLayout.EndRow() #New Row of Groups
	oLayout.EndGroup() #Manage QPopMenuSets
	
	oLayout.AddGroup("Existing QPop Menu Display Contexts")
	oDisplayContexts = oLayout.AddEnumControl ("MenuDisplayContexts", None, "Menu Display Contexts", c.siControlListBox)
	oDisplayContexts.SetAttribute(c.siUINoLabel, True)
	oLayout.AddRow()
	oLayout.AddButton("CreateNewDisplayContext","Create New Context")
	oLayout.AddButton("DeleteDisplayContext","Delete Selected Context")
	oLayout.EndRow()
	
	oLayout.AddRow()
	oLayout.AddItem("MenuDisplayContext_Name", "Name", c.siControlString)
	#oLayout.AddEnumControl("MenuDisplayContext_ScriptLanguage", ("Python","Python","JScript","JScript","VBasic","VBasic","Perl","Perl"), "Language", c.siControlCombo)
	oLayout.AddEnumControl("MenuDisplayContext_ScriptLanguage", ("Python","Python"), "Language", c.siControlCombo) #Only Python for now due to execution speed penalty of ExecuteScriptCommand command
	oLayout.AddButton("ExecuteDisplayContextCode", "Execute")
	oLayout.EndRow()
	
	oCodeEditor = oLayout.AddItem("MenuDisplayContext_Code", "Code", c.siControlTextEditor)
	#oCodeEditor.SetAttribute(c.siUIToolbar, 1 )
	#oCodeEditor.SetAttribute(c.siUILineNumbering, 1 )
	#oCodeEditor.SetAttribute(c.siUIFolding, True )
	#oCodeEditor.SetAttribute(c.siUIKeywords , "for in def print" )
	#oCodeEditor.SetAttribute(c.siUIKeywordFile , "C:\users\Administrator\Autodesk\Softimage_7.5\Addons\QPop\Data\Preferences\Python.keywords" )
	oLayout.EndGroup()
	
	#================================ Debugging Options Tab ============================================================================================
	oLayout.AddTab("Debug Options")
	oLayout.AddButton ("Refresh", "Reset/Delete everything")
	oLayout.AddGroup("Debug Options")
	oQPopConfigFile = oLayout.AddItem("FirstStartup", "First Startup")
	oLayout.AddItem("ShowQpopMenuString","Show Qpop Menu String")
	oLayout.AddItem("IncludeWindowHandle","Append Window Handle to Qpop Menu String")
	oLayout.EndGroup()
	
	

def QPopConfigurator_CommandList_OnChanged():
	Print("QPopConfigurator_CommandList_OnChanged called", c.siVerbose)
	PPG.Menus.Value = ""
	PPG.MenuItemList.Value = ""
	RefreshMenuItemDetailsWidgets()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
	
def QPopConfigurator_MenuItemList_OnChanged():
	Print ("QPopConfigurator_MenuItemList_OnChanged called",c.siVerbose)
	PPG.Menus.Value = ""
	PPG.CommandList.Value = ""
	RefreshMenuSetDetailsWidgets()
	RefreshMenuItemDetailsWidgets()
	PPG.Refresh()

def QPopConfigurator_Menus_OnChanged():
	Print ("QPopConfigurator_Menus_OnChanged called",c.siVerbose)	
	PPG.MenuItemList.Value = ""
	PPG.CommandList.Value = ""
	RefreshMenuItemDetailsWidgets()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
	
	
def QPopConfigurator_MoveSetUpInView_OnClicked():
	Print("QPopConfigurator_MoveSetUpInView_OnClicked called", c.siVerbose)
	CurrentViewName = PPG.ViewSignatures.Value
	CurrentSetName = PPG.ViewMenuSets.Value
	oCurrentView = getQPopViewSignatureByName(CurrentViewName)
	oCurrentSet = getQPopMenuSetByName(CurrentSetName)
	
	if oCurrentView != None and oCurrentSet != None:
		CurrentSetIndex = oCurrentView.menuSets.index(oCurrentSet)
		if CurrentSetIndex > 0:
			oCurrentView.removeMenuSet(CurrentSetIndex)
			oCurrentView.insertMenuSet(CurrentSetIndex -1,oCurrentSet)
			RefreshViewMenuSets()
			PPG.Refresh()

def QPopConfigurator_MenuItems_OnChanged():
	Print("QPopConfigurator_MenuItems_OnChanged called", c.siVerbose)
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
			
def QPopConfigurator_MoveSetDownInView_OnClicked():
	Print("QPopConfigurator_MoveSetUpInView_OnClicked", c.siVerbose)
	CurrentViewName = PPG.ViewSignatures.Value
	CurrentSetName = PPG.ViewMenuSets.Value
	oCurrentView = getQPopViewSignatureByName(CurrentViewName)
	oCurrentSet = getQPopMenuSetByName(CurrentSetName)
	
	if oCurrentView != None and oCurrentSet != None:
		CurrentSetIndex = oCurrentView.menuSets.index(oCurrentSet)
		if CurrentSetIndex < (len(oCurrentView.menuSets)-1):
			oCurrentView.removeMenuSet(CurrentSetIndex)
			oCurrentView.insertMenuSet(CurrentSetIndex +1,oCurrentSet)
			RefreshViewMenuSets()
			PPG.Refresh()
	
def QPopConfigurator_AutoSelectMenu_OnChanged():
	Print("QPopConfigurator_AutoSelectMenu_Onchanged called", c.siVerbose)
	if PPG.AutoSelectMenu.Value == True:
		PPG.MenuChooser.SetCapabilityFlag (c.siReadOnly,True)
		RefreshMenuChooser()
		RefreshMenuSetDetailsWidgets()
		RefreshMenuItems()
		PPG.Refresh()
	else:
		PPG.MenuChooser.SetCapabilityFlag (c.siReadOnly,False)

def QPopConfigurator_MenuChooser_OnChanged():
	Print ("QPopConfigurator_MenuChooser_OnChanged called",c.siVerbose)
	RefreshMenuItems()
	PPG.refresh()

	
def QPopConfigurator_SaveConfig_OnClicked ():
	Print("QPopConfigurator_SaveConfig_OnClicked called",c.siVerbose)
	fileName = PPG.QPopConfigurationFile.Value
	QPopSaveConfiguration(fileName)
	
def QPopConfigurator_LoadConfig_OnClicked():
	Print("QPopConfigurator_LoadConfig_OnClicked called",c.siVerbose)
	fileName = PPG.QPopConfigurationFile.Value
		
	if str(fileName) != "":
		result = False
		result = QPopLoadConfiguration(fileName)
		if result == True:
			RefreshQPopConfigurator()
			PPG.Refresh()

def QPopConfigurator_QPopConfigurationFile_OnChanged():
	Print("QPopConfigurator_QPopConfigurationFile_OnChanged called",c.siVerbose)
	#When config filename is changed we assume that the user knows what he's doing and do not load default config on next startup
	App.Preferences.SetPreferenceValue("QPop.FirstStartup",False)
	
def QPopConfigurator_CommandCategory_OnChanged():
	Print("ExportSettings_OnChanged called", c.siVerbose)
	RefreshCommandList ()
	PPG.Refresh()


def QPopConfigurator_CreateNewScriptItem_OnClicked():
	Print ("QPopConfigurator_CreateNewMenuItem_OnClicked called",c.siVerbose)
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	#Print("Found globalQPopMenuItems: " + str(globalQPopMenuItems) + " of type" + str(type(globalQPopMenuItems)))
	newMenuItem = App.CreateQPop("MenuItem")
	
	#Find the Category for the new menu item
	MenuItem_Category = ""
	try:
		#try to get the current menuItemCategory for the new menu item's category
		if (str(MenuItem_Category) == "") or (str(MenuItem_Category) == "_ALL_"):
			MenuItem_Category = "Miscellaneous"	
		else:
			MenuItem_Category = (str(PPG.MenuItem_Category.Value))
	except:
		MenuItem_Category = "Miscellaneous"	
	
	#Find a unique name for the new menu item
	listKnownMenuItem_Names = list()
	for menuItem in globalQPopMenuItems.items:
		listKnownMenuItem_Names.append (menuItem.name)

	uniqueName = getUniqueName("New Script Item",listKnownMenuItem_Names)
	
	newMenuItem.name = uniqueName
	newMenuItem.UID = XSIFactory.CreateGuid()
	newMenuItem.category = MenuItem_Category
	
	#Language = PPG.MenuItem_ScriptLanguage.Value
	#if str(Language) == "":
	Language = "Python"	
	newMenuItem.language = Language #Set Scritping language 
	newMenuItem.code = ('Application.LogMessage("Empty QPop Menu Item executed")')
	globalQPopMenuItems.addMenuItem(newMenuItem)

	RefreshMenuItem_CategoryList()
	PPG.MenuItem_Category.Value = MenuItem_Category
	RefreshMenuItemList()

	PPG.MenuItemList.Value = uniqueName
	PPG.CommandList.Value = ""
	PPG.Menus.Value = ""
	RefreshMenuItemDetailsWidgets()
	PPG.Refresh()
	
def QPopConfigurator_CreateNewMenu_OnClicked():
	Print ("QPopConfigurator_CreateNewMenu_OnClicked called",c.siVerbose)
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	listKnownQPopMenuNames = list()
	for menu in globalQPopMenus.items:
		listKnownQPopMenuNames.append(menu.name)
	
	UniqueMenuName = getUniqueName("NewQPopMenu",listKnownQPopMenuNames)
		
	oNewMenu = App.CreateQPop("Menu")
	oNewMenu.name = UniqueMenuName
	Language = PPG.MenuItem_ScriptLanguage.Value
	if str(Language) == "":
		Language = "Python"
	oNewMenu.language = Language
	
	oNewMenu.Code = ("def QPopMenu_Eval(oMenu):\t#This function must not be renamed!\n\t#Add your script code here\n\tDoNothing = True")
	globalQPopMenus.addMenu(oNewMenu)

	PPG.Menus.Value = UniqueMenuName
	RefreshMenus()
	RefreshMenuChooser()
	PPG.MenuItemList.Value = ""
	PPG.CommandList.Value = ""
	RefreshMenuItemDetailsWidgets()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()

def QPopConfigurator_DeleteScriptItem_OnClicked():
	Print("QPopConfigurator_DeleteMenuItem_OnClicked called", c.siVerbose)
	CurrentMenuItemName = str(PPG.MenuItemList.Value)
	if CurrentMenuItemName != "":
		#deleteQPopMenuItem(CurrentMenuItemName)
		globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
		
		CurrentMenuItemIndex = None
		MenuItemsEnum = PPG.PPGLayout.Item("MenuItemList").UIItems
		CurrentMenuItemIndex = MenuItemsEnum.index(CurrentMenuItemName)
		
		deleteQPopMenuItem(CurrentMenuItemName)
		#RefreshMenuItems()
			
		if CurrentMenuItemIndex != None:
			if CurrentMenuItemIndex < 2: #The first menuItem was selected?
				if len(MenuItemsEnum) > 2: # and more than 1 menu items in the enum list left?
					PreviousMenuItemName = MenuItemsEnum[CurrentMenuItemIndex +2]
				else: PreviousMenuItemName = ""
			else: #the first menu item was not selected, make the previous one selected after deletion..
				PreviousMenuItemName = MenuItemsEnum[CurrentMenuItemIndex - 2]
						
			PPG.MenuItemList.Value = PreviousMenuItemName
			RefreshMenuItemDetailsWidgets()
			RefreshMenuSetDetailsWidgets()
			CurrentCategory = PPG.MenuItem_Category.Value
			RefreshMenuItem_CategoryList()
			MenuItemCategories = PPG.PPGLayout.Item("MenuItem_Category").UIItems
			if CurrentCategory in MenuItemCategories:
				PPG.MenuItem_Category.Value = CurrentCategory
			else:
				PPG.MenuItem_Category.Value = "_ALL_"
			RefreshMenuItemList()
			PPG.Refresh()

def QPopConfigurator_DeleteMenu_OnClicked():
	Print("QPopConfigurator_DeleteMenu_OnClicked called", c.siVerbose)
	CurrentMenuName = PPG.Menus.Value
	if str(CurrentMenuName) != "":
		globalQPopMenus = App.GetGlobal("globalQPopMenus")
		CurrentMenuIndex = None
		
		MenusEnum = PPG.PPGLayout.Item("Menus").UIItems
		for oMenu in globalQPopMenus.items:
			if oMenu.name == CurrentMenuName:
				CurrentMenuIndex = MenusEnum.index(CurrentMenuName)
		
		deleteQPopMenu(CurrentMenuName)	
		RefreshMenus()
			
		if CurrentMenuIndex != None:
			#Print("CurrentContextIndex is: " + str(CurrentContextIndex))
			if CurrentMenuIndex < 2: #The first menuitem was selected?
				if len(MenusEnum) > 2: # and more than 1 contexts in the enum list left?
					PreviousMenuName = MenusEnum[CurrentMenuIndex +2]
				else: PreviousMenuName = ""
			else: #the first menu was not selected, make the previous one selected after deletion..
				PreviousMenuName = MenusEnum[CurrentMenuIndex - 2]
						
			PPG.Menus.Value = PreviousMenuName
		RefreshMenuContexts()
		RefreshMenuItems()
		RefreshMenuItemDetailsWidgets()
		RefreshMenuSetDetailsWidgets()
		PPG.Refresh()
					

def QPopConfigurator_RemoveMenu_OnClicked():
	CurrentMenuSetName = str(PPG.MenuSetChooser.Value)
		
	if CurrentMenuSetName != "":
		oCurrentMenuSet = None
		oChosenMenu = None
		oCurrentMenuSet = getQPopMenuSetByName(CurrentMenuSetName)
		
		if oCurrentMenuSet != None: #The menu set was found?
			globalQPopMenus = App.GetGlobal("globalQPopMenus")
			
			if PPG.MenuSelector.Value == 0: CurrentMenus = "A"
			if PPG.MenuSelector.Value == 1: CurrentMenus = "B"
			if PPG.MenuSelector.Value == 2: CurrentMenus = "C"
			if PPG.MenuSelector.Value == 3: CurrentMenus = "D"
			
			CurrentMenuNumber = (PPG.MenuContexts.Value)
			oCurrentMenuSet.setMenu (CurrentMenuNumber, None, CurrentMenus)
			RefreshMenuContexts()
			RefreshMenuChooser()
			RefreshMenuSetDetailsWidgets()
			RefreshMenuItems()
			PPG.Refresh()

					
def QPopConfigurator_AssignMenu_OnClicked():
	Print ("QPopConfigurator_AssignMenu_OnClicked called",c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	CurrentMenuSetName = str(PPG.MenuSetChooser.Value)
		
	if CurrentMenuSetName != "":
		oCurrentMenuSet = None
		oChosenMenu = None
		oCurrentMenuSet = getQPopMenuSetByName(CurrentMenuSetName)
		
		if oCurrentMenuSet != None:
			globalQPopMenus = App.GetGlobal("globalQPopMenus")
			
			if PPG.MenuSelector.Value == 0: CurrentMenus = "A"
			if PPG.MenuSelector.Value == 1: CurrentMenus = "B"
			if PPG.MenuSelector.Value == 2: CurrentMenus = "C"
			if PPG.MenuSelector.Value == 3: CurrentMenus = "D"
			
			CurrentMenuNumber = (PPG.MenuContexts.Value)
			ChosenMenuName = str(PPG.Menus.Value)
			if ((ChosenMenuName != "")  and (CurrentMenuNumber > -1)):
				if (ChosenMenuName != "_NONE_"):
					oChosenMenu = getQPopMenuByName(ChosenMenuName )

				oCurrentMenuSet.setMenu (CurrentMenuNumber, oChosenMenu, CurrentMenus)
				RefreshMenuContexts()
				
	if PPG.AutoSelectMenu.Value == True:
		RefreshMenuChooser()
		RefreshMenuSetDetailsWidgets()
		RefreshMenuItems()
	PPG.Refresh()


def QPopConfigurator_MenuContexts_OnChanged():
	Print ("QPopConfigurator_MenuContexts_OnChanged called",c.siVerbose)
		
	RefreshMenuSetDetailsWidgets()
	if PPG.AutoSelectMenu.Value == True:
		RefreshMenuChooser() 
		RefreshMenuItems()
		RefreshMenuItemDetailsWidgets()
	PPG.Refresh()


def QPopConfigurator_ItemInsert_OnClicked():
	Print ("QPopConfigurator_ItemInsertMenuItem_OnClicked called",c.siVerbose)
	oCurrentMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	if oCurrentMenu != None:
		CurrentMenuItemIndex = PPG.MenuItems.Value
		if CurrentMenuItemIndex < 0:
			CurrentMenuItemIndex  = 0
		
		oItemToInsert = None
	#Insert a command in case it was selected
		if PPG.CommandList.Value != "":
			oItemToInsert = getCommandByUID(PPG.CommandList.Value)

	#Insert a script item in case it was selected	
		if PPG.MenuItemList.Value != "":
			oItemToInsert = getQPopMenuItemByName ( PPG.MenuItemList.Value)

	#Insert a menu in case it was selected
		if PPG.Menus.Value != "":
			oItemToInsert = getQPopMenuByName ( PPG.Menus.Value )
			

		if oItemToInsert != None:
			oCurrentMenu.insertMenuItem (CurrentMenuItemIndex, oItemToInsert)
			
			RefreshMenuItems()
			PPG.MenuItems.Value = CurrentMenuItemIndex
			RefreshMenuSetDetailsWidgets()
			PPG.Refresh()		

def QPopConfigurator_MenuItem_Name_OnChanged():
	Print("QPopConfigurator_MenuItem_Name_OnChanged called", c.siVerbose)
	
	if PPG.MenuItem_Name.Value != "":
		globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
		globalQPopMenus = App.GetGlobal("globalQPopMenus")
		
		NewMenuItem_Name = ""
		Done = False
		KnownMenuItemNames = list()
		oItem = None
		RefreshRequired = False
		
		#Lets see if a Script Item is selected whose name shall be changed
		if PPG.MenuItemList.Value != "":
			for oMenuItem in globalQPopMenuItems.items:
				KnownMenuItemNames.append(oMenuItem.name) #Get all known Script Items names so we can later find a new uinique name
				
			oItem = getQPopMenuItemByName(PPG.MenuItemList.Value)
			Done = True
		
		#A Script item was not selected, lets see if a menus was selected
		if Done == False:
			KnownMenuItemNames = list()
			if PPG.Menus.Value != "":
				for oMenu in globalQPopMenus.items:
					KnownMenuItemNames.append(oMenu.name) #Get all known Menu names so we can later find a new uinique name
				
				oItem = getQPopMenuByName(PPG.Menus.Value)
			
		if oItem != None:
			if oItem.Name != PPG.MenuItem_Name.Value:
				NewMenuItem_Name = getUniqueName(PPG.MenuItem_Name.Value, KnownMenuItemNames)
				oItem.name = NewMenuItem_Name	
		
		#Select the renamed object in the respective list view
		if PPG.MenuItemList.Value != "":
			PPG.MenuItemList.Value = NewMenuItem_Name
			PPG.Menus.Value = ""
			
			RefreshMenuItemList()
			RefreshMenuItems()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()
			
		if PPG.Menus.Value != "":
			PPG.Menus.Value = NewMenuItem_Name
			PPG.MenuItemList.Value = ""
			
			RefreshMenuChooser()
			RefreshMenuItems()
			RefreshMenus()
			RefreshMenuContexts()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()
		
	else:
		Print("QPop menu or script item  names must not be empty!", c.siWarning)
		if PPG.MenuItemList.Value != "":
			PPG.MenuItem_Name.Value = PPG.MenuItemList.Value
		if PPG.Menus.Value != "":
			PPG.MenuItem_Name.Value = PPG.Menus.Value
		
	

def QPopConfigurator_NewMenuItem_Category_OnChanged():
	Print("QPopConfigurator_NewMenuItem_Category_OnChanged called", c.siVerbose)
	CurrentMenuItem_Name = PPG.MenuItemList.Value
	CurrentMenuItem_Category = PPG.MenuItem_Category.Value
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	
	NewMenuItem_Category = PPG.NewMenuItem_Category.Value.replace(";","_")

	for menuItem in globalQPopMenuItems.items:
		if menuItem.name == CurrentMenuItem_Name:
			menuItem.category = NewMenuItem_Category
			
	RefreshMenuItem_CategoryList()
	
	if CurrentMenuItem_Category != "_ALL_": PPG.MenuItem_Category.Value = NewMenuItem_Category
	RefreshMenuItem_CategoryChooserList()
	RefreshMenuItemList()
	PPG.MenuItemList.Value = CurrentMenuItem_Name
	RefreshMenuItemDetailsWidgets()
	PPG.NewMenuItem_Category.Value = menuItem.category
	PPG.Refresh()

def QPopConfigurator_MenuItem_ScriptLanguage_OnChanged():
	Print("QPopConfigurator_MenuItem_ScriptLanguage_OnChanged called", c.siVerbose)
	NewScriptLanguage = str(PPG.MenuItem_ScriptLanguage.Value)
	
	if PPG.MenuItemList.Value != "":
		oMenuItem = getQPopMenuItemByName(PPG.MenuItemList.Value)
		if oMenuItem != None:
			oMenuItem.language = NewScriptLanguage
		
	elif PPG.Menus.Value != "":
		oMenu = getQPopMenuByName(PPG.Menus.Value)
		if oMenu != None:
			oMenu.language = NewScriptLanguage

def QPopConfigurator_MenuItem_Code_OnChanged():
	Print("QPopConfigurator_MenuItem_Code_OnChanged called", c.siVerbose)
	
	if PPG.MenuItemList.Value != "":
		oMenuItem = getQPopMenuItemByName(PPG.MenuItemList.Value)
		if oMenuItem != None:
			oMenuItem.code = PPG.MenuItem_Code.Value
		
	elif PPG.Menus.Value != "":
		oMenu = getQPopMenuByName(PPG.Menus.Value)
		if oMenu != None:
			oMenu.code = PPG.MenuItem_Code.Value

			
def QPopConfigurator_MenuItem_CategoryChooser_OnChanged():
	Print("QPopConfigurator_MenuItem_CategoryChooser_OnChanged called", c.siVerbose)
	CurrentMenuItem_Name = PPG.MenuItemList.Value
	CurrentMenuItem_Category = PPG.MenuItem_Category.Value
	NewMenuItem_Category = PPG.MenuItem_CategoryChooser.Value
	
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	for menuItem in globalQPopMenuItems.items:
		if menuItem.name == CurrentMenuItem_Name:
			menuItem.category = NewMenuItem_Category 
	
	RefreshMenuItem_CategoryList()
	if CurrentMenuItem_Category != "_ALL_": PPG.MenuItem_Category.Value = NewMenuItem_Category 
	RefreshMenuItemList()
	PPG.MenuItemList.Value = CurrentMenuItem_Name 
	RefreshMenuItemDetailsWidgets()
	PPG.Refresh()
	
	
def QPopConfigurator_MenuItem_Category_OnChanged():
	Print("QPopConfigurator_MenuItem_Category_OnChanged called", c.siVerbose)
	RefreshMenuItemList()
	RefreshMenuItemDetailsWidgets()
	PPG.Refresh()

def QPopConfigurator_CreateMenuSet_OnClicked():
	Print("QPopConfigurator_CreateMenuSet_OnClicked called", c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	globalQPopMenuSetNamesList = list()
	for Set in globalQPopMenuSets.items:
		globalQPopMenuSetNamesList.append(Set.name)
	
	newSetName = getUniqueName("NewQPopMenuSet",globalQPopMenuSetNamesList)
	
	newSet = App.CreateQPop("MenuSet")
	newSet.Name = newSetName
	
	globalQPopMenuSets.addSet(newSet)
	RefreshMenuSets()
	PPG.MenuSets.Value = newSetName
	PPG.MenuSetName.Value = newSetName
	RefreshContextConfigurator()
	PPG.Refresh()


def QPopConfigurator_MenuSelector_OnChanged():
	Print("QPopConfigurator_MenuSelector_OnChanged called", c.siVerbose)
	RefreshContextConfigurator()
	RefreshMenuContexts()
	RefreshMenuChooser()
	RefreshMenuItems()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
	

def QPopConfigurator_View_OnChanged():
	Print("QPopConfigurator_View_OnChanged()", c.siVerbose)
	RefreshMenuSetChooser()
	RefreshMenuContexts()
	PPG.MenuContexts.Value = 0
	RefreshMenuChooser()
	RefreshMenuItems()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
	
def QPopConfigurator_MenuSets_OnChanged():
	Print("QPopConfigurator_MenuSets_OnChanged called", c.siVerbose)
	PPG.MenuSetName.Value = PPG.MenuSets.Value
	RefreshContextConfigurator()
	PPG.Refresh()

def QPopConfigurator_MenuSetName_OnChanged():
	Print("QPopConfigurator_MenuSetName_OnChanged called", c.siVerbose)
	NewMenuSetName = PPG.MenuSetName.Value
	CurrentMenuSetName = PPG.MenuSets.Value

	if NewMenuSetName != "" :
		if NewMenuSetName != CurrentMenuSetName:		
			globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
			globalQPopMenuSetNames = list()
			for oMenuSet in globalQPopMenuSets.items:
				globalQPopMenuSetNames.append(oMenuSet.name)
			
			uniqueMenuSetName = getUniqueName(NewMenuSetName, globalQPopMenuSetNames)

			PPG.MenuSetName.Value = uniqueMenuSetName
			
			for oMenuSet in globalQPopMenuSets.items:
				if oMenuSet.name == PPG.MenuSets.Value:
					oMenuSet.name = uniqueMenuSetName
					PPG.MenuSets.Value = oMenuSet.name
			
			RefreshMenuSets()
			RefreshViewMenuSets()
			RefreshMenuSetChooser()
			PPG.Refresh()
	else:
		Print("QPop Menu Set names must not be empty!", c.siWarning)
	

def QPopConfigurator_DeleteMenuSet_OnClicked():
	Print("QPopConfigurator_DeleteMenuSet_OnClicked called", c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	currentMenuSetName = str(PPG.MenuSets.Value)
	menuSetNamesEnum = PPG.PPGLayout.Item ("MenuSets").UIItems
	currentMenuSetIndex = None
	
	if currentMenuSetName != "": 
		if len(menuSetNamesEnum) > 0:
			currentMenuSetIndex = menuSetNamesEnum.index(currentMenuSetName)
		
		oCurrentMenuSet = None
		oCurrentMenuSet = getQPopMenuSetByName (currentMenuSetName)
		
		if oCurrentMenuSet != None:
			globalQPopMenuSets.deleteSet(oCurrentMenuSet)
			for oViewSignature in globalQPopViewSignatures.items:
				for oSet in oViewSignature.menuSets:
					if oSet == oCurrentMenuSet:
						oViewSignature.removeMenuSet( oViewSignature.menuSets.index(oSet))

		RefreshMenuSets()
		RefreshViewMenuSets()
		
		if currentMenuSetIndex != None:
			if (currentMenuSetIndex < 2): #The first menu set item in the list was selected?
				if len(menuSetNamesEnum) > 2: #Were there more than 1 sets in the enum list left?
					previousMenuSetName = menuSetNamesEnum[currentMenuSetIndex +2]
				else:
					previousMenuSetName = ""
			else:
				previousMenuSetName = menuSetNamesEnum[currentMenuSetIndex -2]
				#Print("PreviousMenuSetName is: " + str(previousMenuSetName))
			PPG.MenuSets.Value = previousMenuSetName
		
		PPG.MenuSetName.Value = PPG.MenuSets.Value 
		RefreshContextConfigurator()
		PPG.Refresh()

def QPopConfigurator_ViewSignature_OnChanged():
	Print("QPopConfigurator_ViewSignature_OnChanged", c.siVerbose)
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	currentSignatureName = str(PPG.ViewSignatures.Value)
	
	if currentSignatureName != "":
		for oSignature in globalQPopViewSignatures.items:
			if oSignature.name == currentSignatureName:
				oCurrentSignature = oSignature
				oCurrentSignature.signature = PPG.ViewSignature.Value


def QPopConfigurator_ViewSignatures_OnChanged():
	Print("QPopConfigurator_ViewSignatures_OnChanged called", c.siVerbose)
	RefreshViewDetailsWidgets()
	RefreshViewMenuSets()
	PPG.Refresh()
		

def QPopConfigurator_ViewSignatureName_OnChanged():
	Print("QPopConfigurator_ViewSignatureName_OnChanged", c.siVerbose)
	currentSignatureName = PPG.ViewSignatures.Value
	newSignatureName = str(PPG.ViewSignatureName.Value)
	
	if newSignatureName != "" :
		if currentSignatureName != newSignatureName:
			globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
			listKnownViewSignatureNames = list()
			
			currentSignatureName = PPG.ViewSignatures.Value
			if str(currentSignatureName) != "":
				for signature in globalQPopViewSignatures.items:
					listKnownViewSignatureNames.append(signature.name)
						
				oCurrentSignature = getQPopViewSignatureByName(currentSignatureName)
				if oCurrentSignature != None:
		
					newSignatureName = getUniqueName(newSignatureName,listKnownViewSignatureNames)
					oCurrentSignature.name = newSignatureName

					RefreshViewSignaturesList()
					RefreshViewSelector()
					PPG.View.Value = newSignatureName
					PPG.ViewSignatures.Value = oCurrentSignature.name
					PPG.ViewSignatureName.Value = oCurrentSignature.name
					PPG.ViewSignature.Value = oCurrentSignature.signature
	else:
		Print("QPop View Signture names must not be empty!", c.siWarning)
	
	PPG.ViewSignatureName.Value = PPG.ViewSignatures.Value	


def QPopConfigurator_AddQPopViewSignature_OnClicked():
	Print("QPopConfigurator_AddQPopViewSignature_OnClicked called", c.siVerbose)
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	
	newSignature = App.CreateQPop("ViewSignature")
	listKnownViewSignatureNames = list()
	for signature in globalQPopViewSignatures.items:
		listKnownViewSignatureNames.append(signature.name)
		
	newSignatureName = getUniqueName("NewView",listKnownViewSignatureNames)
	newSignatureString = "Viewer;DS_ChildViewManager;DS_ChildRelationalView;TrayClientWindow;"
	newSignature.name = newSignatureName
	newSignature.signature = newSignatureString	
	globalQPopViewSignatures.addSignature(newSignature)
	RefreshViewSignaturesList()
	PPG.ViewSignatures.Value = newSignatureName
	PPG.ViewSignature.Value = newSignatureString
	PPG.ViewSignatureName.Value = newSignatureName
	RefreshViewSelector()
	RefreshViewMenuSets()
	PPG.Refresh()
	
def QPopConfigurator_DelQPopViewSignature_OnClicked():
	Print("QPopConfigurator_DelQPopViewSignature_OnClicked called", c.siVerbose)
	
	if str(PPG.ViewSignatures.Value) != "":
		globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
		currentSignatureName = PPG.ViewSignatures.Value
		currentViewIndex = None
		viewSignatureNamesEnum = list()
		
		viewSignatureNamesEnum = PPG.PPGLayout.Item ("ViewSignatures").UIItems
		if len(viewSignatureNamesEnum) > 0:
			currentViewIndex = viewSignatureNamesEnum.index(PPG.ViewSignatures.Value)
			
		for signature in globalQPopViewSignatures.items:
			if signature.name == currentSignatureName:
				globalQPopViewSignatures.deleteSignature(signature)
		
		RefreshViewSignaturesList()
		previousViewSignatureName = ""
		
		if currentViewIndex != None:
			if (currentViewIndex - 2) < 0:
				if len(viewSignatureNamesEnum) > 2:
					previousViewSignatureName = viewSignatureNamesEnum[currentViewIndex +2]
			else: 
				previousViewSignatureName = viewSignatureNamesEnum[currentViewIndex - 2]
						
		PPG.ViewSignatures.Value = previousViewSignatureName
		RefreshViewDetailsWidgets()
		RefreshViewMenuSets()
		RefreshViewSelector()
		RefreshMenuSetChooser()
		PPG.Refresh()
	
def QPopConfigurator_RecordViewSignature_OnChanged():
	if PPG.RecordViewSignature.Value == True:
		Print("Please move the mouse cursor over the desired window area and press any key on the keyboard", c.siWarning)
		
def QPopConfigurator_CreateNewDisplayContext_OnClicked():
	Print("QPopConfigurator_CreateNewDisplayContext_OnClicked called", c.siVerbose)
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	
	uniqueDisplayContextName = "NewDisplayContext"
	DisplayContextNames = list()
	for oDisplayContext in globalQPopMenuDisplayContexts.items:
		DisplayContextNames.append(oDisplayContext.name)
	
	uniqueDisplayContextName = getUniqueName(uniqueDisplayContextName,DisplayContextNames)
	
	oNewDisplayContext = App.CreateQPop("MenuDisplayContext")
	oNewDisplayContext.name = uniqueDisplayContextName
	oNewDisplayContext.code = ("def QPopContext_Eval(): #This function must not be renamed!\n\n\t#Add your code here\n\n\treturn True\t#This function must return a boolean!")
	oNewDisplayContext.language = "Python"
	
	globalQPopMenuDisplayContexts.addContext(oNewDisplayContext)
	RefreshMenuDisplayContextsList()
	PPG.MenuDisplayContexts.Value = uniqueDisplayContextName
	RefreshMenuDisplayContextDetailsWidgets()
	PPG.Refresh()

def QPopConfigurator_DeleteDisplayContext_OnClicked():
	Print("QPopConfigurator_DeleteDisplayContext_OnClicked called", c.siVerbose)
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
	if str(CurrentMenuDisplayContextName) != "":
		globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
		globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")

		CurrentContextIndex = None
		MenuDisplayContextsEnum = PPG.PPGLayout.Item("MenuDisplayContexts").UIItems
		
		oCurrentDisplayContext = None
		for oDisplayContext in globalQPopMenuDisplayContexts.items:
			if oDisplayContext.name == CurrentMenuDisplayContextName:
				oCurrentDisplayContext = oDisplayContext
				
		#Delete Context from MenuSets
		if oCurrentDisplayContext != None:
			for oMenuSet in globalQPopMenuSets.items:
				try:
					Index = oMenuSet.AContexts.index(oCurrentDisplayContext)
					oMenuSet.removeContext(Index, "A")
					oMenuSet.removeMenuAtIndex(Index,"A")
				except:
					DoNothin = true
				try:
					Index = oMenuSet.BContexts.index(oCurrentDisplayContext)
					oMenuSet.removeContext(Index, "B")
					oMenuSet.removeMenuAtIndex(Index,"B")
				except:
					DoNothin = true
				try:
					Index = oMenuSet.CContexts.index(oCurrentDisplayContext)
					oMenuSet.removeContext(Index, "C")
					oMenuSet.removeMenuAtIndex(Index,"C")
				except:
					DoNothin = true
				try:
					Index = oMenuSet.DContexts.index(oCurrentDisplayContext)
					oMenuSet.removeContext(Index, "D")
					oMenuSet.removeMenuAtIndex(Index,"D")
				except:
					DoNothin = true

		#Delete Context from globals
		globalQPopMenuDisplayContexts.deleteContext(oCurrentDisplayContext)
		CurrentContextIndex = MenuDisplayContextsEnum.index(CurrentMenuDisplayContextName)
		
		RefreshMenuDisplayContextsList()
		RefreshContextConfigurator()
			
		if CurrentContextIndex != None:
			#Print("CurrentContextIndex is: " + str(CurrentContextIndex))
			if CurrentContextIndex < 2: #The first menuitem was selected?
				if len(MenuDisplayContextsEnum) > 2: # and more than 1 contexts in the enum list left?
					#Print ("Length is: " + str(len(MenuDisplayContextsEnum)))
					PreviousMenuDisplayContextName = MenuDisplayContextsEnum[CurrentContextIndex +2]
				else: PreviousMenuDisplayContextName = ""
			else: #the first menu item was not selected, make the previous one selected after deletion..
				PreviousMenuDisplayContextName = MenuDisplayContextsEnum[CurrentContextIndex - 2]
				#Print("previousViewSignatureName  is: " + str(PreviousViewSignatureName))
						
			PPG.MenuDisplayContexts.Value = PreviousMenuDisplayContextName
			RefreshMenuDisplayContextDetailsWidgets()
			PPG.Refresh()

	
def QPopConfigurator_MenuDisplayContexts_OnChanged():
	Print("QPopConfigurator_MenuDisplayContexts_OnChanged called", c.siVerbose)
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	oCurrentMenuDisplayContext = None
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value

	for oDisplayContext in globalQPopMenuDisplayContexts.items:
		if oDisplayContext.name == CurrentMenuDisplayContextName:
			oCurrentMenuDisplayContext = oDisplayContext
	
	if oCurrentMenuDisplayContext != None:
		PPG.MenuDisplayContext_Name.Value = oCurrentMenuDisplayContext.name
		PPG.MenuDisplayContext_Code.Value = oCurrentMenuDisplayContext.code
		PPG.MenuDisplayContext_ScriptLanguage.Value = oCurrentMenuDisplayContext.language


def QPopConfigurator_MenuDisplayContext_Name_OnChanged():
	Print("QPopConfigurator_MenuDisplayContext_Name_OnChanged called", c.siVerbose)
	NewMenuDisplayContextName = PPG.MenuDisplayContext_Name.Value
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
	
	if str(NewMenuDisplayContextName) != "":
		if NewMenuDisplayContextName != CurrentMenuDisplayContextName:
			globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
			oCurrentMenuDisplayContext = None
			CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
			DisplayContextNames = list()
			for oDisplayContext in globalQPopMenuDisplayContexts.items:
				DisplayContextNames.append(oDisplayContext.name)
				if oDisplayContext.name == CurrentMenuDisplayContextName:
					oCurrentMenuDisplayContext = oDisplayContext
			
			if oCurrentMenuDisplayContext != None:
				UniqueMenuDisplayContextName = getUniqueName(NewMenuDisplayContextName, DisplayContextNames)
				oCurrentMenuDisplayContext.name = UniqueMenuDisplayContextName
				RefreshMenuDisplayContextsList()
				PPG.MenuDisplayContexts.Value = UniqueMenuDisplayContextName
				RefreshContextConfigurator()
				RefreshMenuDisplayContextDetailsWidgets()
				RefreshMenuContexts()
				PPG.Refresh()
	else:
		Print("QPop Menu Display Context names must not be empty!", c.siWarning)
		PPG.MenuDisplayContext_Name.Value = PPG.MenuDisplayContexts.Value
	
	
	

def QPopConfigurator_MenuDisplayContext_ScriptLanguage_OnChanged():
	Print("QPopConfigurator_MenuDisplayContext_ScriptLanguage_OnChanged called", c.siVerbose)
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	oCurrentMenuDisplayContext = None
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
	MenuDisplayContextLanguage = PPG.MenuDisplayContext_ScriptLanguage.Value

	for oDisplayContext in globalQPopMenuDisplayContexts.items:
		if oDisplayContext.name == CurrentMenuDisplayContextName:
			oCurrentMenuDisplayContext = oDisplayContext
	
	if oCurrentMenuDisplayContext != None:
		oCurrentMenuDisplayContext.language = MenuDisplayContextLanguage
	
	#TODO: implement text widget feature switching as a vbs or JScript function, python does not seem to work
	#oTextWidget = PPG.PPGLayout.Item("MenuDisplayContext_Code")
	#oTextWidget.SetAttribute(c.siUIKeywords , "for in def print if" )
	#oTextWidget.SetAttribute(c.siUIKeywordFile , "C:\users\Administrator\Autodesk\Softimage_7.5\Addons\QPop\Data\Preferences\Python.keywords" )
	

def QPopConfigurator_MenuDisplayContext_Code_OnChanged():
	Print("QPopConfigurator_MenuDisplayContext_Code_OnChanged called", c.siVerbose)
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	oCurrentMenuDisplayContext = None
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
	Code = PPG.MenuDisplayContext_Code.Value
	
	#while Code[len(Code)-1] == " ":
	
	Code = Code.rstrip()

	for oDisplayContext in globalQPopMenuDisplayContexts.items:
		if oDisplayContext.name == CurrentMenuDisplayContextName:
			oCurrentMenuDisplayContext = oDisplayContext
	
	if oCurrentMenuDisplayContext != None:
		oCurrentMenuDisplayContext.code = Code

	PPG.MenuDisplayContext_Code.Value = oCurrentMenuDisplayContext.code
		
	

def QPopConfigurator_InsertMenuContext_OnClicked():
	Print("QPopConfigurator_InsertMenuContext_OnClicked called", c.siVerbose)
	
	CurrentMenuSetName = PPG.MenuSets.Value
	SelectedMenuDisplayContextName = PPG.MenuDisplayContexts.Value #The name of the selected context that shall be assigned
	CurrentMenuDisplayContextName = PPG.ContextConfigurator.Value #The name of the already assigned context above which the new context shall be inserted
	
	oCurrentMenuSet = None
	oSelectedMenuDisplayContext = None
	oCurrentMenuSet = getQPopMenuSetByName(CurrentMenuSetName)
	oSelectedMenuDisplayContext = getQPopMenuDisplayContextByName(SelectedMenuDisplayContextName)
	oCurrentMenuDisplayContext = getQPopMenuDisplayContextByName(CurrentMenuDisplayContextName)
		
	if ((oCurrentMenuSet != None) and (oSelectedMenuDisplayContext != None)):

		if PPG.MenuSelector.Value == 0:
			Contexts = oCurrentMenuSet.AContexts
			Menus = oCurrentMenuSet.AMenus
			MenuList = ContextList = "A"
		if PPG.MenuSelector.Value == 1:
			Contexts = oCurrentMenuSet.BContexts
			Menus = oCurrentMenuSet.BMenus
			MenuList = ContextList = "B"
		if PPG.MenuSelector.Value == 2:
			Contexts = oCurrentMenuSet.CContexts
			Menus = oCurrentMenuSet.CMenus
			MenuList = ContextList = "C"
		if PPG.MenuSelector.Value == 3:
			Contexts = oCurrentMenuSet.DContexts
			Menus = oCurrentMenuSet.DMenus
			MenuList = ContextList = "D"
		
		if not(oSelectedMenuDisplayContext in Contexts):
			CurrentMenuDisplayContextIndex = 0
			try:
				CurrentMenuDisplayContextIndex = Contexts.index(oCurrentMenuDisplayContext)
			except:
				CurrentMenuDisplayContextIndex = 0
			oCurrentMenuSet.insertContext(CurrentMenuDisplayContextIndex,oSelectedMenuDisplayContext,ContextList)
			oCurrentMenuSet.insertMenuAtIndex(CurrentMenuDisplayContextIndex, None, MenuList)
				
			RefreshContextConfigurator()
			PPG.ContextConfigurator.Value = oSelectedMenuDisplayContext.name
			
			RefreshMenuContexts()
			RefreshMenuSetDetailsWidgets()
			RefreshMenuItems()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()
	
		

def QPopConfigurator_RemoveMenuContext_OnClicked():
	Print("QPopConfigurator_RemoveMenuContext_OnClicked called", c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	
	CurrentMenuSetName = PPG.MenuSets.Value
	CurrentMenuDisplayContextName = PPG.ContextConfigurator.Value
	CurrentMenuDisplayContextIndex = None
	CurrentMenuDisplayContextEnum = PPG.PPGLayout.Item("ContextConfigurator").UIItems
	#Print("CurrentMenuDisplayContextEnum is: " + str(CurrentMenuDisplayContextEnum))

	if str(CurrentMenuDisplayContextName) != "":
		DisplayContextIndex = None
		oCurrentMenuSet = None
		oCurrentMenuDisplayContext = None

		oCurrentMenuSet = getQPopMenuSetByName(CurrentMenuSetName)
		
		for oMenuDisplayContext in globalQPopMenuDisplayContexts.items:
			if oMenuDisplayContext.name == CurrentMenuDisplayContextName:
				oCurrentMenuDisplayContext = oMenuDisplayContext
				CurrentMenuDisplayContextIndex = CurrentMenuDisplayContextEnum.index(CurrentMenuDisplayContextName)

		if PPG.MenuSelector.Value == 0:
			#Print("A is active")
			Contexts = oCurrentMenuSet.AContexts
			MenuList = ContextList = "A"
		if PPG.MenuSelector.Value == 1:
			Contexts = oCurrentMenuSet.BContexts
			MenuList = ContextList = "B"
		if PPG.MenuSelector.Value == 2:
			Contexts = oCurrentMenuSet.CContexts
			MenuList = ContextList = "C"
		if PPG.MenuSelector.Value == 3:
			Contexts = oCurrentMenuSet.DContexts
			MenuList = ContextList = "D"
		
		DisplayContextIndex = Contexts.index(oCurrentMenuDisplayContext)
			
		oCurrentMenuSet.removeContext (DisplayContextIndex, ContextList)
		oCurrentMenuSet.removeMenuAtIndex(DisplayContextIndex,MenuList)
		
		#Print("DisplayContextIndex is: " + str(DisplayContextIndex))
		
		if CurrentMenuDisplayContextIndex != None:
			if CurrentMenuDisplayContextIndex < 2: #The first menu display context was selected?
				if len(CurrentMenuDisplayContextEnum) > 2: # and more than 1 menu display context still in list?
					PreviousMenuDisplayContextName = CurrentMenuDisplayContextEnum[CurrentMenuDisplayContextIndex + 2]
				else: 
					#Print("previousViewSignatureName  is: " + str(PreviousViewSignatureName))
					PreviousMenuDisplayContextName = ""
			else: #the first display context item was not selected, make the previous one selected after deletion..
				PreviousMenuDisplayContextName = CurrentMenuDisplayContextEnum[CurrentMenuDisplayContextIndex - 2]
				
			PPG.ContextConfigurator.Value = PreviousMenuDisplayContextName
			RefreshContextConfigurator()
			RefreshMenuContexts()
			RefreshMenuChooser()
			RefreshMenuItems()
			RefreshMenuSetDetailsWidgets()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()

	
def QPopConfigurator_InsertSetInView_OnClicked():
	Print("QPopConfigurator_InsertSetInView_OnClicked called", c.siVerbose)
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	CurrentViewSignatureName = str(PPG.ViewSignatures.Value)
	CurrentMenuSetName = str(PPG.ViewMenuSets.Value)
	oCurrentMenuSet = None
	oCurrentViewSignature = None
	SelectedMenuSetName = str(PPG.MenuSets.Value)
	oSelectedMenuSet = None #The Menu Set selected in Existing QPop Menu Sets
	
	MenuSetIndex = 0

	if (CurrentViewSignatureName != "") and (SelectedMenuSetName != ""): #Is a View Signature and an existing QPop menu Set selected?
		for oMenuSet in globalQPopMenuSets.items:
			if oMenuSet.name == SelectedMenuSetName:
				oSelectedMenuSet = oMenuSet
			
		for oSignature in globalQPopViewSignatures.items:
			if oSignature.name == CurrentViewSignatureName:
				oCurrentViewSignature = oSignature
		
		if CurrentMenuSetName == "":
			MenuSetIndex = 0
			
		if CurrentMenuSetName != "":
			MenuSetNameList = list()
			MenuSets = oCurrentViewSignature.menuSets
			for oMenuSet in MenuSets:
				if oMenuSet.name == CurrentMenuSetName:
					oCurrentMenuSet = oMenuSet
			if oCurrentMenuSet != None:
				try:
					MenuSetIndex = MenuSets.index(oCurrentMenuSet)
				except:
					MenuSetIndex = 0
		
		if not(oSelectedMenuSet in oCurrentViewSignature.menuSets):
			oCurrentViewSignature.insertMenuSet(MenuSetIndex, oSelectedMenuSet)
			PPG.ViewMenuSets.Value = oSelectedMenuSet.name
			RefreshViewMenuSets()
		RefreshViewSelector()
		RefreshMenuSetChooser()
		RefreshMenuContexts()
		RefreshMenuSetDetailsWidgets()
		PPG.Refresh()
			
def QPopConfigurator_RemoveSetInView_OnClicked():
	Print("QPopConfigurator_RemoveSetInView_OnClicked called", c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	
	CurrentViewSignatureName = str(PPG.ViewSignatures.Value)
	CurrentMenuSetName = str(PPG.ViewMenuSets.Value)
	oCurrentMenuSet = None
	oCurrentViewSignature = None
	
	if (CurrentMenuSetName != "") and (CurrentViewSignatureName!= ""):
	
		for oMenuSet in globalQPopMenuSets.items:
			if oMenuSet.name == CurrentMenuSetName:
				oCurrentMenuSet = oMenuSet
		
		CurrentViewSignatureMenuSets = list()
		
		for oSignature in globalQPopViewSignatures.items:
			if oSignature.name == CurrentViewSignatureName:
				oCurrentViewSignature = oSignature
				CurrentViewSignatureMenuSets = oCurrentViewSignature.menuSets
		
		if len(CurrentViewSignatureMenuSets) > 0:
			try:
				CurrentMenuSetIndex = CurrentViewSignatureMenuSets.index(oCurrentMenuSet)
			except:
				CurrentMenuSetIndex = None
				
			if oCurrentMenuSet != None:
				if (CurrentMenuSetIndex == 0):
					if len(CurrentViewSignatureMenuSets) == 1:
						PreviousViewMenuSetName = ""
					else:
						PreviousViewMenuSetName = CurrentViewSignatureMenuSets[CurrentMenuSetIndex +1].name
				else:
					PreviousViewMenuSetName = CurrentViewSignatureMenuSets[CurrentMenuSetIndex -1].name
				
				oCurrentViewSignature.removeMenuSet(CurrentMenuSetIndex) #Delete the menu set
				
			PPG.ViewMenuSets.Value = PreviousViewMenuSetName
		RefreshViewMenuSets()
		RefreshMenuSetChooser()
		RefreshMenuContexts()
		RefreshMenuSetDetailsWidgets()
		PPG.Refresh()		

def QPopConfigurator_MenuSetChooser_OnChanged():
	Print("QPopConfigurator_MenuSetChooser_OnChanged called", c.siVerbose)
	RefreshMenuContexts()
	PPG.MenuContexts.Value = -1
	RefreshMenuChooser()
	RefreshMenuItems()
	PPG.Refresh()
	
def QPopConfigurator_InspectCommand_OnClicked():
	CurrentCommandUID = PPG.CommandList.Value
	CurrentCommand = getCommandByUID(CurrentCommandUID)
	#CurrentCommand = App.Commands(CurrentCommandName)
	#Print(CurrentCommandName)
	if CurrentCommand != None:
		if CurrentCommand.Name != "":
			App.EditCommand(CurrentCommand.Name)

		
def QPopConfigurator_ConvertCommandToMenuItem_OnClicked():
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	CurrentCommandUID = PPG.CommandList.Value
	CurrentCommand = getCommandByUID(CurrentCommandUID)
	CurrentCommandName = ""
	if CurrentCommand != None:
		CurrentCommandName = CurrentCommand.Name
		if CurrentCommandName != "":
			CurrentCommand = App.Commands(CurrentCommandName)

			MenuItemCode = ""
			ArgList = list()
			if CurrentCommandName != "":
				#if PPG.MenuItem_ScriptLanguage.Value == "Python": #Works only in Python for now
				MenuItemCode += ("# QPop Automatic script conversion of command \"" + CurrentCommandName + "\" (ScriptingName: \"" + CurrentCommand.ScriptingName + "\")\n\n")
				MenuItemCode = MenuItemCode + ("Application.Commands(\"" + CurrentCommandName + "\").Execute()")
				PPG.MenuItem_ScriptLanguage.Value == "Python"
				
				NewQPopMenuItem = App.CreateQPop("MenuItem")
				
				KnownMenuItemNames = list()
				for MenuItem in globalQPopMenuItems.items:
					KnownMenuItemNames.append(MenuItem.name)
				UniqueName = getUniqueName (CurrentCommandName, KnownMenuItemNames)
				NewQPopMenuItem.Name = UniqueName
				
				if CurrentCommand.Category != "":
					Categories = CurrentCommand.Category 
					Cat = (Categories.split("|"))
					NewQPopMenuItem.Category = Cat[0]
				else:
					NewQPopMenuItem.Category = "Custom"
				
				NewQPopMenuItem.language = PPG.MenuItem_ScriptLanguage.Value
				
				NewQPopMenuItem.code = MenuItemCode
				
				globalQPopMenuItems.addMenuItem(NewQPopMenuItem)
				RefreshMenuItem_CategoryList()
				PPG.MenuItem_Category.Value = NewQPopMenuItem.Category
				RefreshMenuItemList()
				PPG.MenuItemList.Value = NewQPopMenuItem.Name
				RefreshMenuItemDetailsWidgets()
				PPG.Refresh()
					
		
def QPopConfigurator_ShowHotkeyableOnly_OnChanged():
	if PPG.ShowHotkeyableOnly.Value == True:
		CurrentCommandUID = PPG.CommandList.Value
		CurrentCommand = getCommandByUID(CurrentCommandUID)
		if CurrentCommand != None and CurrentCommand.SupportsKeyAssignment ==  False:
			PPG.CommandList.Value = ""
			
	RefreshCommandList()
	RefreshMenuItemDetailsWidgets()
	RefreshMenuSetDetailsWidgets()
	PPG.Refresh()
	
def QPopConfigurator_ShowScriptingNameInBrackets_OnChanged():
	RefreshCommandList()
	PPG.Refresh()
def QPopConfigurator_ExecuteCode_OnClicked():
	Print("QPopConfigurator_ExecuteCode_OnClicked called", c.siVerbose)
	
	if PPG.Menus.Value != "":
		oSelectedItem = getQPopMenuByName(PPG.Menus.Value)
		if oSelectedItem != None:
			Language = oSelectedItem.language
			Code = oSelectedItem.code
			if Code != "":
				ArgList = list(); ArgList.append(oSelectedItem)
				try:
					App.ExecuteScriptCode(Code, Language,"QPopMenu_Eval",ArgList)
				except:
					Print("An Error occured executing QPop Menu's '" + oSelectedItem.name + "' script code, please see script editor for details!", c.siError)
				return
				
	if PPG.MenuItemList.Value != "":
		oSelectedItem = getQPopMenuItemByName(PPG.MenuItemList.Value)
		if oSelectedItem != None:
			App.QPopExecuteMenuItem(oSelectedItem )
			

def QPopConfigurator_ExecuteDisplayContextCode_OnClicked():
	Print("QPopConfigurator_ExecuteDisplayContextCode_OnClicked called", c.siVerbose)
	
	if PPG.MenuDisplayContexts.Value != "":
		oSelectedItem = getQPopMenuDisplayContextByName(PPG.MenuDisplayContexts.Value)
		if oSelectedItem != None:
			Code = oSelectedItem.code
			Language = oSelectedItem.language
			#DisplayMenu = (False,())
			try:
				DisplayMenu = App.ExecuteScriptCode( Code, Language, "QPopContext_Eval",[])
				if str(type(DisplayMenu[0])) == "<type 'bool'>":
					Print("QpopMenuDisplayContext '" + oSelectedItem.name + "' evaluates to: " + str(DisplayMenu[0]))
				else:
					Print("QpopMenuDisplayContext '" + oSelectedItem.name + "' evaluates to: " + str(DisplayMenu[0]) + ", which is not a boolean value!", c.siWarning)
			except:
				Print("An Error occurred executing the QPopMenuDiplayContext '" + oSelectedItem.name +"', please see script editor for details.", c.siError)

				
def QPopConfigurator_RemoveMenuItem_OnClicked():
	Print("QPopConfigurator_RemoveMenuItem_OnClicked called", c.siVerbose)
	SelectedMenuItemNumber = PPG.MenuItems.Value
	oSelectedMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	if oSelectedMenu != None:
		numItems = len(oSelectedMenu.items)
		MenuItemsEnumList = list(PPG.PPGLayout.Item("MenuItems").UIItems)

		#TODO: Make sure no duplicates are inserted (limitation of enums, they return the same number even if a different item is selected when items are named similarly :-( )

		if (SelectedMenuItemNumber > -1) and (oSelectedMenu != None):
			
			oSelectedMenu.removeMenuItemAtIndex (SelectedMenuItemNumber)
			RefreshMenuItems()
			
			if SelectedMenuItemNumber == 0: #Was the first item in the list selected and deleted?
				if numItems > 1: #Was there more than 1 item in the list?
					PPG.MenuItems.Value = 0 #Select the new first menu item in the list
				else:
					PPG.MenuItems.Value = -1 #It was the one and only menu item, select nothing
					#Print(PPG.MenuItems.Value)
			if SelectedMenuItemNumber > 0: #Some other than the first one was selected
				if SelectedMenuItemNumber == (numItems -1): #Was the last one selected?
					PPG.MenuItems.Value = (SelectedMenuItemNumber - 1) 
				else:
					PPG.MenuItems.Value = SelectedMenuItemNumber

			RefreshMenuSetDetailsWidgets()
			PPG.Refresh()
		
	
def QPopConfigurator_ItemUp_OnClicked():
	Print("QPopConfigurator_ItemUp_OnClicked called", c.siVerbose)
	oMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	MenuItemIndex = PPG.MenuItems.Value
	oMenuItem = oMenu.items[MenuItemIndex]

	if oMenu != None and oMenuItem != None:
		if MenuItemIndex > 0:
			oMenu.removeMenuItem(oMenuItem)
			oMenu.insertMenuItem(MenuItemIndex -1,oMenuItem)
			RefreshMenuItems()
			PPG.MenuItems.Value = MenuItemIndex -1
			RefreshMenuSetDetailsWidgets()
			PPG.Refresh()
			
			
def QPopConfigurator_ItemDown_OnClicked():
	Print("QPopConfigurator_ItemDown_OnClicked called", c.siVerbose)
	oMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	MenuItemIndex = PPG.MenuItems.Value
	oMenuItem = oMenu.items[MenuItemIndex]
	if oMenu != None and oMenuItem != None:
		
		if MenuItemIndex != ((len(oMenu.items))-1): #Is the last one not selected
			oMenu.removeMenuItem(oMenuItem)
			oMenu.insertMenuItem(MenuItemIndex + 1,oMenuItem)
			RefreshMenuItems()
			PPG.MenuItems.Value = MenuItemIndex +1
			RefreshMenuSetDetailsWidgets()
			PPG.Refresh()

def QPopConfigurator_FindItem_OnClicked():
	Print("QPopConfigurator_FindItem_OnClicked called", c.siVerbose)
	oSelectedMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	if oSelectedMenu != None:
		oSelectedItem = oSelectedMenu.items[PPG.MenuItems.Value]
		if oSelectedItem != None:
			if oSelectedItem.type != "Separator":
			
				if oSelectedItem.type == "Command":
					PPG.CommandCategory.Value = oSelectedItem.categories[0]
					RefreshCommandList()
					PPG.CommandList.Value = oSelectedItem.UID
					PPG.Menus.Value = ""
					PPG.MenuItemList.Value = ""
					RefreshMenuItemDetailsWidgets()
					
				if oSelectedItem.type == "QPopMenu":
					PPG.Menus.Value = oSelectedItem.name
					PPG.CommandList.Value = ""
					PPG.MenuItemList.Value = ""
					RefreshMenuItemDetailsWidgets()
					
				if oSelectedItem.type == "QPopMenuItem":
					PPG.MenuItem_Category.Value = oSelectedItem.category
					RefreshMenuItemList ( )
					PPG.MenuItemList.Value = oSelectedItem.name
					PPG.Menus.Value = ""
					PPG.CommandList.Value = ""
					RefreshMenuItemDetailsWidgets()

				PPG.Refresh()


def QPopConfigurator_CtxUp_OnClicked():
	Print("QPopConfigurator_CtxUp_OnClicked called", c.siVerbose)
	SelectedMenuSetName = PPG.MenuSets.Value
	SelectedContextName = PPG.ContextConfigurator.Value
	oMenuSet = getQPopMenuSetByName (SelectedMenuSetName)
	oContext = getQPopMenuDisplayContextByName (SelectedContextName)
	
	if ((oMenuSet != None) and (oContext != None)):

		if PPG.MenuSelector.Value == 0:
			Contexts = oMenuSet.AContexts
			Menus = oMenuSet.AMenus
			MenuList = ContextList = "A"
		if PPG.MenuSelector.Value == 1:
			Contexts = oMenuSet.BContexts
			Menus = oMenuSet.BMenus
			MenuList = ContextList = "B"
		if PPG.MenuSelector.Value == 2:
			Contexts = oMenuSet.CContexts
			Menus = oMenuSet.CMenus
			MenuList = ContextList = "C"
		if PPG.MenuSelector.Value == 3:
			Contexts = oMenuSet.DContexts
			Menus = oMenuSet.DMenus
			MenuList = ContextList = "D"
		
		ContextIndex = Contexts.index(oContext)
		if ContextIndex > 0:
			oMenu = Menus[ContextIndex]
			oMenuSet.removeContext (ContextIndex, ContextList)
			oMenuSet.insertContext (ContextIndex -1 , oContext, ContextList)
			oMenuSet.removeMenuAtIndex (ContextIndex, MenuList)
			oMenuSet.insertMenuAtIndex (ContextIndex -1, oMenu, MenuList)
			RefreshContextConfigurator()
			PPG.MenuContexts.Value = PPG.MenuContexts.Value -1
			RefreshMenuContexts()
			RefreshMenuSetDetailsWidgets()
			RefreshMenuItems()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()
			
def QPopConfigurator_CtxDown_OnClicked():
	Print("QPopConfigurator_CtxDown_OnClicked called", c.siVerbose)
	SelectedMenuSetName = PPG.MenuSets.Value
	SelectedContextName = PPG.ContextConfigurator.Value
	oMenuSet = getQPopMenuSetByName (SelectedMenuSetName)
	oContext = getQPopMenuDisplayContextByName (SelectedContextName)
	
	if ((oMenuSet != None) and (oContext != None)):
		if PPG.MenuSelector.Value == 1:
			Contexts = oMenuSet.AContexts
			Menus = oMenuSet.AMenus
			MenuList = ContextList = "A"
		if PPG.MenuSelector.Value == 1:
			Contexts = oMenuSet.BContexts
			Menus = oMenuSet.BMenus
			MenuList = ContextList = "B"
		if PPG.MenuSelector.Value == 2:
			Contexts = oMenuSet.CContexts
			Menus = oMenuSet.CMenus
			MenuList = ContextList = "C"
		if PPG.MenuSelector.Value == 3:
			Contexts = oMenuSet.DContexts
			Menus = oMenuSet.DMenus
			MenuList = ContextList = "D"
		
		ContextIndex = Contexts.index(oContext)
		if ContextIndex < (len(Contexts) -1):
			oMenu = Menus[ContextIndex]
			oMenuSet.removeContext (ContextIndex, ContextList)
			oMenuSet.insertContext (ContextIndex +1 , oContext, ContextList)
			oMenuSet.removeMenuAtIndex (ContextIndex, MenuList)
			oMenuSet.insertMenuAtIndex (ContextIndex +1, oMenu, MenuList)
			RefreshContextConfigurator()
			PPG.MenuContexts.Value = PPG.MenuContexts.Value +1
			RefreshMenuContexts()
			RefreshMenuSetDetailsWidgets()
			RefreshMenuItems()
			RefreshMenuItemDetailsWidgets()
			PPG.Refresh()


def QPopConfigurator_InsertSeparator_OnClicked():
	Print("QPopConfigurator_InsertSeparator_OnClicked called", c.siVerbose)
	oCurrentMenu = getQPopMenuByName(PPG.MenuChooser.Value)
	oGlobalSeparators = App.GetGlobal("globalQPopSeparators")
	oGlobalSeparator = oGlobalSeparators.items[0]
			
	if oCurrentMenu != None:
		CurrentMenuItemIndex = PPG.MenuItems.Value
		if CurrentMenuItemIndex < 0:
			CurrentMenuItemIndex  = 0
		
		oCurrentMenu.insertMenuItem (CurrentMenuItemIndex, oGlobalSeparator)		
			
		RefreshMenuItems()
		PPG.MenuItems.Value = CurrentMenuItemIndex
		RefreshMenuSetDetailsWidgets()
		PPG.Refresh()	
	
def QPopConfigurator_Refresh_OnClicked():
	initQPopGlobals(True)
	RefreshQPopConfigurator()
	App.Preferences.SetPreferenceValue("QPop.FirstStartup",False)
	PPG.Refresh()


def QPopConfigurator_AddDisplayEvent_OnClicked():
	Print("QPopConfigurator_AddDisplayEvent_OnClicked called", c.siVerbose)
	oGlobalQpopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")
	globalQPopDisplayEvents = oGlobalQpopDisplayEvents.items
	#Find the Display event with the highest number
	HighestNumber = (len(globalQPopDisplayEvents)) -1
	
	oNewDisplayEvent = App.CreateQPop("DisplayEvent")
	oGlobalQpopDisplayEvents.addEvent(oNewDisplayEvent)
	RefreshDisplayEvents()
	PPG.DisplayEvent.Value = HighestNumber +1
	RefreshDisplayEventsKeys()
	
	PPG.Refresh()
	
def QPopConfigurator_DeleteDisplayEvent_OnClicked():
	Print("QPopConfigurator_DeleteDisplayEvent_OnClicked called", c.siVerbose)
	globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")
	EventIndex = PPG.DisplayEvent.Value
	oDisplayEvent = None
	globalQPopDisplayEvents.deleteEvent(EventIndex)

	#Uncheck the record checkbox again
	PPG.DisplayEventKeys_Record.Value = False 
	App.Preferences.SetPreferenceValue("QPop.DisplayEventKeys_Record", False)
	
	RefreshDisplayEvents()

	if EventIndex == len(globalQPopDisplayEvents.items):
		PPG.DisplayEvent.Value = EventIndex -1
		RefreshDisplayEventsKeys()
	PPG.Refresh()
	
	
def QPopConfigurator_DisplayEvent_OnChanged():
	Print("QPopConfigurator_DisplayEvent_OnCanged", c.siVerbose)
	globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")

	if PPG.DisplayEvent.Value > -1:
		oSelectedEvent = globalQPopDisplayEvents.items[PPG.DisplayEvent.Value]
	
	#Uncheck the record checkbox again
	PPG.DisplayEventKeys_Record.Value = False 
	App.Preferences.SetPreferenceValue("QPop.DisplayEventKeys_Record", False)
	RefreshDisplayEventsKeys()
	

def QPopConfigurator_DisplayEventKey_OnChanged():
	Print("QPopConfigurator_DisplayEventKey_OnCanged", c.siVerbose)
	if (str(PPG.DisplayEventKey.Value) != None):
		#Print("Display event key code entered is: " + str(PPG.DisplayEventKey.Value))
		globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")
		try:
			oSelectedEvent = globalQPopDisplayEvents.items[PPG.DisplayEvent.Value]
		except:
			oSelectedEvent = None
		if oSelectedEvent != None:
			oSelectedEvent.key = PPG.DisplayEventKey.Value
	
	#Uncheck the record checkbox again
	PPG.DisplayEventKeys_Record.Value = False 
	App.Preferences.SetPreferenceValue("QPop.DisplayEventKeys_Record", False)
	RefreshDisplayEventsKeys()
	
def QPopConfigurator_DisplayEventKeyMask_OnChanged():
	Print("QPopConfigurator_DisplayEventKey_OnCanged", c.siVerbose)
	if (str(PPG.DisplayEventKey.Value) != None):
		globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")
		try:
			oSelectedEvent = globalQPopDisplayEvents.items[PPG.DisplayEvent.Value]
		except:
			oSelectedEvent = None
		if oSelectedEvent != None:
			oSelectedEvent.keyMask = PPG.DisplayEventKeyMask.Value

	#Uncheck the record checkbox again
	PPG.DisplayEventKeys_Record.Value = False 
	App.Preferences.SetPreferenceValue("QPop.DisplayEventKeys_Record", False)
	RefreshDisplayEventsKeys()
				
def QPopConfigurator_DisplayEvents_OnTab():
	Print ("QPopConfigurator_DisplayEvents_OnTab called",c.siVerbose)
	PPG.DisplayEventKeys_Record.Value = False
	PPG.RecordViewSignature.Value = False	

def QPopConfigurator_LowLevelSettings_OnTab():
	Print ("QPopConfigurator_LowLevelSettings_OnTab called",c.siVerbose)
	PPG.RecordViewSignature.Value = False
	PPG.DisplayEventKeys_Record.Value = False

def QPopConfigurator_DebugOptions_OnTab():
	Print ("QPopConfigurator_DebugOptions_OnTab called",c.siVerbose)
	PPG.RecordViewSignature.Value = False
	PPG.DisplayEventKeys_Record.Value = False

def QPopConfigurator_MainSettings_OnTab():
	Print ("QPopConfigurator_MeinSettings_OnTab called",c.siVerbose)
	PPG.RecordViewSignature.Value = False
	PPG.DisplayEventKeys_Record.Value = False
	
	
#=============== Misc. QPopConfigurator Functions ===============================

def RefreshMenuSetDetailsWidgets():
	Print ("Qpop: RefreshMenuSetDetailsWidgets called",c.siVerbose)

	#Disable all buttons first
	PPG.MenuSetChooser.SetCapabilityFlag(c.siReadOnly, True)

	#PPG.QPopMenuA.SetCapabilityFlag (c.siReadOnly,True)
	#PPG.QPopMenuB.SetCapabilityFlag (c.siReadOnly,True)
	#PPG.QPopMenuC.SetCapabilityFlag (c.siReadOnly,True)
	#PPG.QPopMenuD.SetCapabilityFlag (c.siReadOnly,True)

	PPG.PPGLayout.Item("AssignMenu").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("RemoveMenu").SetAttribute (c.siUIButtonDisable, True)
	
	PPG.PPGLayout.Item("ItemInsert").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("InsertSeparator").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("ItemUp").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("ItemDown").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("RemoveMenuItem").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("FindItem").SetAttribute (c.siUIButtonDisable, True)

	#Start re-enabling buttons
	#Check if a view was selected:
	if PPG.View.Value != "":
		PPG.MenuSetChooser.SetCapabilityFlag(c.siReadOnly, False)
	
		#Check if a Context was selected
		if PPG.MenuSetChooser.Value != "":
			oCurrentMenuSet = getQPopMenuSetByName(PPG.MenuSetChooser.Value)
			if oCurrentMenuSet != None:
		

				oMenu = None
				try:
					if PPG.MenuSelector.Value == 0: oMenu = oCurrentMenuSet.AMenus[PPG.MenuContexts.Value]
					if PPG.MenuSelector.Value == 1: oMenu = oCurrentMenuSet.BMenus[PPG.MenuContexts.Value]
					if PPG.MenuSelector.Value == 2: oMenu = oCurrentMenuSet.CMenus[PPG.MenuContexts.Value]
					if PPG.MenuSelector.Value == 3: oMenu = oCurrentMenuSet.DMenus[PPG.MenuContexts.Value]
					#Print("name of the menu is: " + str(oMenu.name))
				except:
					pass
					#Print("Qpop function 'RefreshMenuSetDetailsWidgets' says: Could not determine current menu!", c.siError)
				if oMenu != None: #Is a menu assigned to the selected context?
					PPG.PPGLayout.Item("RemoveMenu").SetAttribute (c.siUIButtonDisable, False)
					if PPG.AutoSelectMenu.Value == True:
						PPG.MenuChooser.Value = oMenu.name

				if PPG.MenuContexts.Value > -1:
					if PPG.Menus.Value != "": #Is a menu selected that could be assigned to the context?
						PPG.PPGLayout.Item("AssignMenu").SetAttribute (c.siUIButtonDisable, False) #Enable the button


		#A Menu's items are currently displayed?
		if PPG.MenuChooser.Value != "":
			oCurrentMenu = getQPopMenuByName(PPG.MenuChooser.Value)
			if oCurrentMenu != None:
				PPG.PPGLayout.Item("InsertSeparator").SetAttribute (c.siUIButtonDisable, False)
				if (PPG.Menus.Value != "") or (PPG.MenuItemList.Value != "") or (PPG.CommandList.Value != ""): #Is some assignable item selected in one of the combo boxes?
					PPG.PPGLayout.Item("ItemInsert").SetAttribute (c.siUIButtonDisable, False) #Enable the Insert Iem button again
			
			if PPG.MenuItems.Value > -1: #A menu item is currently selected?
				if oCurrentMenu != None:
					oCurrentMenuItem = oCurrentMenu.items[PPG.MenuItems.Value]
					if oCurrentMenuItem != None:
						PPG.PPGLayout.Item("ItemUp").SetAttribute (c.siUIButtonDisable, False)
						PPG.PPGLayout.Item("ItemDown").SetAttribute (c.siUIButtonDisable, False)
						PPG.PPGLayout.Item("RemoveMenuItem").SetAttribute (c.siUIButtonDisable, False)
						if oCurrentMenuItem.type != "Separator":
							PPG.PPGLayout.Item("FindItem").SetAttribute (c.siUIButtonDisable, False)
											
			
def RefreshMenuItemDetailsWidgets():
	Print("Qpop: RefreshMenuItemDetailsWidgets called", c.siVerbose)

#Disable all widgets first
	#PPG.MenuName.SetCapabilityFlag (c.siReadOnly,False)
	PPG.PPGLayout.Item("InspectCommand").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("ExecuteCode").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("ConvertCommandToMenuItem").SetAttribute (c.siUIButtonDisable, True)
	PPG.PPGLayout.Item("DeleteScriptItem").SetAttribute (c.siUIButtonDisable, True)		
	PPG.PPGLayout.Item("DeleteMenu").SetAttribute (c.siUIButtonDisable, True)		
	PPG.NewMenuItem_Category.SetCapabilityFlag (c.siReadOnly,True)
	PPG.MenuItem_CategoryChooser.SetCapabilityFlag (c.siReadOnly,True)
	PPG.MenuItem_Name.SetCapabilityFlag (c.siReadOnly,True)
	PPG.MenuItem_ScriptLanguage.SetCapabilityFlag (c.siReadOnly,True)
	PPG.MenuItem_Code.SetCapabilityFlag (c.siReadOnly,True)
	#PPG.Menus.SetCapabilityFlag (c.siReadOnly,True)
	
#Empty input fields
	PPG.MenuItem_Name.Value = ""
	PPG.NewMenuItem_Category.Value = ""
	PPG.MenuItem_CategoryChooser.Value = ""
	PPG.MenuItem_Code.Value = ""
	PPG.MenuItem_ScriptLanguage.Value = ""

					
#Check if a command was selected:
	if PPG.CommandList.Value != "":
		oItem = getCommandByUID(PPG.CommandList.Value)
		if oItem != None:
			ItemName = oItem.name
			PPG.PPGLayout.Item("InspectCommand").SetAttribute (c.siUIButtonDisable, False)
			PPG.PPGLayout.Item("ConvertCommandToMenuItem").SetAttribute (c.siUIButtonDisable, False)
			PPG.PPGLayout.Item("ExecuteCode").SetAttribute (c.siUIButtonDisable, False)
			
			PPG.NewMenuItem_Category.Value = ""
			PPG.MenuItem_CategoryChooser.Value = ""
			PPG.MenuItem_Code.Value =  ""
		
#Check if a script item was selected:		
	if PPG.MenuItemList.Value != "":
		ItemName = PPG.MenuItemList.Value
		oItem = getQPopMenuItemByName(ItemName)
		if oItem != None:
			#PPG.MemuItem_CategoryChooser.Value = 
			PPG.MenuItem_Name.Value = oItem.name
			PPG.NewMenuItem_Category.Value = oItem.category
			RefreshMenuItem_CategoryChooserList()
			PPG.MenuItem_CategoryChooser.Value = oItem.category
			PPG.MenuItem_Code.Value = oItem.code
			PPG.MenuItem_ScriptLanguage.Value = oItem.language
			
			PPG.PPGLayout.Item("ExecuteCode").SetAttribute (c.siUIButtonDisable, False)
			PPG.MenuItem_Name.SetCapabilityFlag (c.siReadOnly,False)
			PPG.NewMenuItem_Category.SetCapabilityFlag (c.siReadOnly,False)
			PPG.MenuItem_CategoryChooser.SetCapabilityFlag (c.siReadOnly,False)
			PPG.MenuItem_ScriptLanguage.SetCapabilityFlag (c.siReadOnly,False)
			PPG.MenuItem_Code.SetCapabilityFlag (c.siReadOnly,False)
			
			#PPG.PPGLayout.Item("CreateNewScriptItem").SetAttribute (c.siUIButtonDisable, False)
			PPG.PPGLayout.Item("DeleteScriptItem").SetAttribute (c.siUIButtonDisable, False)			

#Check if a menu was selected			
	if PPG.Menus.Value != "":
		ItemName = PPG.Menus.Value
		oItem = getQPopMenuByName(ItemName)
		if oItem != None:
			#PPG.PPGLayout.Item("CreateNewMenu").SetAttribute (c.siUIButtonDisable, True)
			PPG.PPGLayout.Item("DeleteMenu").SetAttribute (c.siUIButtonDisable, False)	
			PPG.MenuItem_Name.Value = oItem.name
			PPG.NewMenuItem_Category.Value = ""
			PPG.MenuItem_CategoryChooser.Value = ""
			PPG.MenuItem_ScriptLanguage.Value = ""
			PPG.MenuItem_ScriptLanguage.Value = oItem.language
			PPG.MenuItem_Code.Value = oItem.code
			
			PPG.PPGLayout.Item("DeleteMenu").SetAttribute (c.siUIButtonDisable, False)	
			PPG.PPGLayout.Item("ExecuteCode").SetAttribute (c.siUIButtonDisable, False)
			PPG.MenuItem_Name.SetCapabilityFlag (c.siReadOnly,False)
			PPG.MenuItem_ScriptLanguage.SetCapabilityFlag (c.siReadOnly,False)
			PPG.MenuItem_Code.SetCapabilityFlag (c.siReadOnly,False)


def ResetToDefaultValues():
	Print("Qpop: ResetToDefaultValues called", c.siVerbose)
	PPG.View.Value = ""
	PPG.CommandList.Value = "_ALL_"
	PPG.Menus.Value = ""
	PPG.MenuItem_Category.Value = "_ALL_"
	PPG.MenuItemList.Value = "_ALL_"
	PPG.MenuItem_Code = ""
	PPG.MenuSetChooser.Value = ""
	PPG.MenuSelector.Value = 0
	PPG.MenuContexts.Value = -1
	PPG.MenuChooser.Value = ""
	PPG.AutoSelectMenu.Value = True
	PPG.MenuItems.Value = -1
	PPG.MenuItem_Name = ""
	PPG.MenuItem_Category = ""
	PPG.MenuItem_CategoryChooser = ""
	PPG.MenuItem_ScriptLanguage = ""
	PPG.CommandList.Value = ""
	PPG.Menus.Value = ""
	PPG.MenuItemList.Value = ""
	PPG.DisplayEventKeys_Record.Value = 0
	PPG.DisplayEvent.Value = -1
	
def RefreshQPopConfigurator():
	Print("RefreshQpopConfigurator called", c.siVerbose)
	ResetToDefaultValues()
	RefreshMenuDisplayContextsList()
	RefreshMenuDisplayContextDetailsWidgets()
	RefreshMenuItem_CategoryList()
	RefreshMenuItemList()
	RefreshViewSelector()
	RefreshViewSignaturesList()
	RefreshViewDetailsWidgets()
	RefreshMenuSets()
	RefreshContextConfigurator()
	PPG.MenuSetName.Value = PPG.MenuSets.Value #TODO: Put this and others in a refresh function
	
	RefreshViewMenuSets()
	RefreshMenuSetChooser()
	RefreshMenuContexts()
	RefreshMenuChooser()
	RefreshMenus()
	
	RefreshCommandCategoryList()
	RefreshCommandList()
	RefreshMenuSetDetailsWidgets()
	RefreshMenuItems()
	RefreshMenuItemDetailsWidgets()
	RefreshDisplayEvents()
	RefreshDisplayEventsKeys()


def RefreshMenus():
	Print("Qpop: RefreshMenus called", c.siVerbose)
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	MenusEnum = list()
	
	for oMenu in globalQPopMenus.items:
		MenusEnum.append("(m) " + oMenu.name)
		MenusEnum.append(oMenu.name)
	
	PPG.PPGLayout.Item("Menus").UIItems = MenusEnum
	PPG.Refresh()

def RefreshMenuChooser():
	Print("Qpop: RefreshMenuChooser called", c.siVerbose)
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	MenusEnum = list()

	for oMenu in globalQPopMenus.items:
		MenusEnum.append(oMenu.name)
		MenusEnum.append(oMenu.name)
	
	PPG.PPGLayout.Item("MenuChooser").UIItems = MenusEnum
	
	#Find and select the appropriate menu name in the chooser..
	if PPG.AutoSelectMenu.Value == True:
		PPG.MenuChooser.SetCapabilityFlag (c.siReadOnly,True)
		oCurrentMenuSet = getQPopMenuSetByName(PPG.MenuSetChooser.Value)
		if oCurrentMenuSet != None:
			CurrentMenus = None
			
			if PPG.MenuSelector.Value == 0: CurrentMenus = oCurrentMenuSet.AMenus
			if PPG.MenuSelector.Value == 1: CurrentMenus = oCurrentMenuSet.BMenus
			if PPG.MenuSelector.Value == 2: CurrentMenus = oCurrentMenuSet.CMenus
			if PPG.MenuSelector.Value == 3: CurrentMenus = oCurrentMenuSet.DMenus
			if CurrentMenus != None:
				oCurrentMenu = None
				try:
					oCurrentMenu = CurrentMenus[PPG.MenuContexts.Value]
				except:
					pass
				
				if oCurrentMenu != None:
					PPG.MenuChooser.Value = oCurrentMenu.name
				else:
					PPG.MenuChooser.Value = -1
		else:
			PPG.MenuChooser.Value = -1

	
def RefreshMenuContexts():
	Print("Qpop: RefreshMenuContexts called", c.siVerbose)
	CurrentMenuSetName = str(PPG.MenuSetChooser.Value)
	oCurrentMenuSet = None
	CurrentContexts = None
	CurrentMenus = None
	CurrentContextsEnum = list()
	
	if CurrentMenuSetName != "":
		oCurrentMenuSet = getQPopMenuSetByName(CurrentMenuSetName)
		if oCurrentMenuSet != None:
			if PPG.MenuSelector.Value == 0: CurrentContexts = oCurrentMenuSet.AContexts; CurrentMenus = oCurrentMenuSet.AMenus
			if PPG.MenuSelector.Value == 1: CurrentContexts = oCurrentMenuSet.BContexts; CurrentMenus = oCurrentMenuSet.BMenus
			if PPG.MenuSelector.Value == 2: CurrentContexts = oCurrentMenuSet.CContexts; CurrentMenus = oCurrentMenuSet.CMenus
			if PPG.MenuSelector.Value == 3: CurrentContexts = oCurrentMenuSet.DContexts; CurrentMenus = oCurrentMenuSet.DMenus
		
			startrange = 0
			endrange = (len(CurrentContexts))
			
			if ((CurrentContexts != None) and (CurrentMenus != None)):
				for i in range(startrange , endrange):
					ContextString = str(CurrentContexts[i].name)
					MenuString = "NONE"
					if len(CurrentMenus) > 0:
						if CurrentMenus[i] != None:
							MenuString = str(CurrentMenus[i].name)
					
					ContextAndMenuString = ("(ctx) " + ContextString + " - " + "(m) " + MenuString)
					#Print(ContextAndMenuString)
					CurrentContextsEnum.append(ContextAndMenuString)
					#CurrentContextsEnum.append(ContextAndMenuString)
					CurrentContextsEnum.append(i)
	PPG.PPGLayout.Item ("MenuContexts").UIItems = CurrentContextsEnum

	try:
		PPG.MenuContexts.Value = 0
	except:
		DoNothing = True

		
def RefreshMenuSetChooser():
	Print("Qpop: RefreshMenuSetChooser called", c.siVerbose)
	CurrentChosenMenuSetName = str(PPG.MenuSetChooser.Value)
	CurrentViewName = str(PPG.View.Value)
	oCurrentViewSignature = None
	MenuSetChooserEnum = list()
	
	if CurrentViewName != "":
		globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
		for oViewSignature in globalQPopViewSignatures.items:
			if oViewSignature.name == CurrentViewName:
				oCurrentViewSignature = oViewSignature
		
		if oCurrentViewSignature != None:
			MenuSets = oCurrentViewSignature.menuSets
			for oMenuSet in MenuSets:
				MenuSetChooserEnum.append(oMenuSet.name)
				MenuSetChooserEnum.append(oMenuSet.name)

	PPG.PPGLayout.Item("MenuSetChooser").UIItems = MenuSetChooserEnum
	PPG.MenuSetChooser.Value = ""
	if CurrentChosenMenuSetName != "":
		if CurrentChosenMenuSetName in MenuSetChooserEnum:
			PPG.MenuSetChooser.Value = CurrentChosenMenuSetName
	if str(PPG.MenuSetChooser.Value) == "":
		if len(MenuSetChooserEnum) > 0:
			PPG.MenuSetChooser.Value = MenuSetChooserEnum[0]
				
				
	
def RefreshViewMenuSets():
	Print("Qpop: RefreshViewMenuSets called", c.siVerbose)
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	CurrentViewSignatureName = str(PPG.ViewSignatures.Value)
	oCurrentViewSignature = None
	CurrentViewMenuSets = list()
	CurrentViewMenuSetsEnum = list()
	
	if CurrentViewSignatureName == "":
		PPG.PPGLayout.Item("ViewMenuSets").UIItems = CurrentViewMenuSetsEnum
	
	if CurrentViewSignatureName != "":
		for oSignature in globalQPopViewSignatures.items:
			if oSignature.name == CurrentViewSignatureName:
				oCurrentViewSignature = oSignature
		if oCurrentViewSignature != None:
			CurrentViewMenuSets = oCurrentViewSignature.menuSets
		#if len(CurrentViewMenuSets) > 0:
		for oMenuSet in CurrentViewMenuSets:
			CurrentViewMenuSetsEnum.append("(ms) " + oMenuSet.name)
			CurrentViewMenuSetsEnum.append(oMenuSet.name)
		PPG.PPGLayout.Item("ViewMenuSets").UIItems = CurrentViewMenuSetsEnum
			
		
				
	
def RefreshMenuDisplayContextsList():
	Print("Qpop: RefreshMenuDisplayContextsList called", c.siVerbose)
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	DisplayContextList = list()
	DisplayContextEnum = list()
	for oDisplayContext in globalQPopMenuDisplayContexts.items:
		DisplayContextList.append(oDisplayContext.name)

	DisplayContextList.sort()
	
	for name in DisplayContextList:
		DisplayContextEnum.append("(ctx) " + name)
		DisplayContextEnum.append(name)
		
	PPG.PPGLayout.Item("MenuDisplayContexts").UIItems = DisplayContextEnum
	
	
	
def RefreshMenuDisplayContextDetailsWidgets():
	Print("Qpop: RefreshMenuDisplayContextDetailsWidgets called", c.siVerbose)
	CurrentMenuDisplayContextName = PPG.MenuDisplayContexts.Value
	oCurrentMenuDisplayContext = None
	oCurrentMenuDisplayContext = getQPopMenuDisplayContextByName (CurrentMenuDisplayContextName)
	PPG.MenuDisplayContext_Name.Value = ""
	PPG.MenuDisplayContext_Code.Value = ""
	
	if oCurrentMenuDisplayContext != None:
		PPG.MenuDisplayContext_Name.Value = oCurrentMenuDisplayContext.name
		PPG.MenuDisplayContext_Code.Value = oCurrentMenuDisplayContext.code
		PPG.MenuDisplayContext_ScriptLanguage.Value = oCurrentMenuDisplayContext.language
	

def RefreshContextConfigurator():
	Print("Qpop: RefreshContextConfigurator called", c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	
	oCurrentMenuSet = None
	CurrentContexts = None
	CurrentContextsEnum = list()
	currentMenuSetName = PPG.MenuSets.Value
	for oMenuSet in globalQPopMenuSets.items:
		if oMenuSet.name == currentMenuSetName:
			oCurrentMenuSet = oMenuSet
	
	if oCurrentMenuSet != None:
		if PPG.MenuSelector.Value == 0: CurrentContexts = oCurrentMenuSet.AContexts
		if PPG.MenuSelector.Value == 1: CurrentContexts = oCurrentMenuSet.BContexts
		if PPG.MenuSelector.Value == 2: CurrentContexts = oCurrentMenuSet.CContexts
		if PPG.MenuSelector.Value == 3: CurrentContexts = oCurrentMenuSet.DContexts
	
	if CurrentContexts != None:
		for oContext in CurrentContexts:
			CurrentContextsEnum.append("(ctx) " + oContext.name)
			CurrentContextsEnum.append(oContext.name)
	PPG.PPGLayout.Item ("ContextConfigurator").UIItems = CurrentContextsEnum
				
		
	
	
def RefreshViewSignaturesList():
	Print("Qpop: RefreshViewSignaturesList called", c.siVerbose)
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	viewSignatureNameListEnum = list()
	
	for signature in globalQPopViewSignatures.items:
		viewSignatureNameListEnum.append("(v) " + signature.name)
		viewSignatureNameListEnum.append(signature.name)
	
	
	PPG.PPGLayout.Item ("ViewSignatures").UIItems = viewSignatureNameListEnum
	if len(viewSignatureNameListEnum) == 0:
		PPG.ViewSignatures.Value = ""
	PPG.Refresh()

def RefreshViewDetailsWidgets():
	Print("Qpop: RefreshViewDetailsWidgets called", c.siVerbose)
	CurrentViewName = PPG.ViewSignatures.Value
	if CurrentViewName != "":
		oCurrentView = getQPopViewSignatureByName(CurrentViewName)
		if oCurrentView != None:
			PPG.ViewSignatureName.Value = oCurrentView.name
			PPG.ViewSignature.Value = oCurrentView.signature
	else:
		PPG.ViewSignatureName.Value = ""
		PPG.ViewSignature.Value = ""
		
def RefreshCommandCategoryList():
	Print("Qpop: RefreshCommandCategoryList called", c.siVerbose)
	CommandCategoriesSet = set() #Create a set for command categories (we don't want duplicates)
	CommandCategoriesList = list()
	CommandCategoriesEnum = list()

	for Command in App.Commands:
		for Category in Command.Categories:
			CommandCategoriesSet.add(Category)

	CommandCategoriesList = list(CommandCategoriesSet)
	CommandCategoriesList.sort()
	CommandCategoriesEnum.append("_ALL_")
	CommandCategoriesEnum.append("_ALL_")

	for Category in CommandCategoriesList:
		CommandCategoriesEnum.append(Category)
		CommandCategoriesEnum.append(Category)

	PPG.PPGLayout.Item ("CommandCategory").UIItems = CommandCategoriesEnum #Populate the ListControl with the known Command Categories 

	
def RefreshViewSelector():
	Print("Qpop: RefreshViewSelector called", c.siVerbose)

	CurrentViewName = PPG.View.Value
	CurrentViewSignature = ""
	oCurrentView = None
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	viewSelectorEnumList = list()
	KnownViews = globalQPopViewSignatures.items
	FirstKnownViewName = ""
	
	#Refresh the view selector list box
	for view in KnownViews:
		viewSelectorEnumList.append(view.name)
		viewSelectorEnumList.append(view.name)
	
	if len(KnownViews) > 0:
		FirstKnownViewName = str(KnownViews[0].name)

		PPG.PPGLayout.Item("View").UIItems = viewSelectorEnumList
		#PPG.ViewSignatureName.Value = CurrentViewName
		#PPG.ViewSignature.Value = CurrentViewSignature
		if str(CurrentViewName) == "":
			PPG.View.Value = str(FirstKnownViewName)
	else:
		PPG.PPGLayout.Item("View").UIItems = viewSelectorEnumList
		PPG.View.Value = ""
		
		

def RefreshMenuItem_CategoryList():
	Print("Qpop: RefreshMenuItem_CategoryList called",c.siVerbose)
	listMenuItemCategories = list()
	listMenuItemCategoriesEnum = list()
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	#Print ("globalQPopMenuItems knows those menuItems: " + str(globalQPopMenuItems.items))
	
	for menuItem in globalQPopMenuItems.items:
		listMenuItemCategories.append (menuItem.category)
	
	listMenuItemCategories = list(set(listMenuItemCategories))
	listMenuItemCategories.sort()

	listMenuItemCategoriesEnum.append("_ALL_")
	listMenuItemCategoriesEnum.append("_ALL_")

	for Category in listMenuItemCategories:
		listMenuItemCategoriesEnum.append(Category)
		listMenuItemCategoriesEnum.append(Category)

	PPG.PPGLayout.Item ("MenuItem_Category").UIItems = listMenuItemCategoriesEnum #Populate the ListControl with the known MenuItemCategories
	PPG.MenuItem_Category.Value = "_ALL_"

def RefreshMenuItem_CategoryChooserList(): #This refreshes the widget that lets you change a Qpop script items category
	Print("Qpop: RefreshMenuItem_CategoryChooserList called",c.siVerbose)
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	
	listMenuItemCategories = list()
	listMenuItemCategoriesEnum = list()

	for menuItem in globalQPopMenuItems.items:
		listMenuItemCategories.append (menuItem.category)
	
	listMenuItemCategories = list(set(listMenuItemCategories)) #get rid of duplicates
	listMenuItemCategories.sort()


	for Category in listMenuItemCategories:
		listMenuItemCategoriesEnum.append(Category)
		listMenuItemCategoriesEnum.append(Category)

	PPG.PPGLayout.Item ("MenuItem_CategoryChooser").UIItems = listMenuItemCategoriesEnum #Populate the ListControl with the known MenuItemCategories
		
def RefreshMenuItems():
	Print ("Qpop: RefreshMenuItems called",c.siVerbose)
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	CurrentMenuItemNumber= str(PPG.MenuItems.Value)
	CurrentMenuName = str(PPG.MenuChooser.Value)
	listMenuItemsEnum = list()
	oCurrentMenu = None
	oCurrentMenu = getQPopMenuByName(CurrentMenuName)
	
	if oCurrentMenu != None:
		listMenuItems = oCurrentMenu.items
		Counter = 0
		for oItem in listMenuItems:
			prefix = "      "
			if str(oItem.type) == "Command" or str(oItem.type) == "CommandPlaceholder":
				prefix = "(c)  "
			if str(oItem.type) == "QPopMenuItem":
				prefix = "(s)  "
			if str(oItem.type) == "QPopMenu":
				prefix = "(m) "
			MissingName = ("_DELETED ITEM_")
			if oItem.name == "":
				NameInList = (prefix + MissingName)
			else:
				NameInList = (prefix + oItem.name)
			if oItem.type == "QPopSeparator":
				NameInList = "------------------"

			while NameInList in listMenuItemsEnum:
				#Print(NameInList + " already exists, adding whitespace")
				NameInList = NameInList + " "
			listMenuItemsEnum.append (NameInList )
			listMenuItemsEnum.append (Counter)
			Counter += 1
				
		PPG.PPGLayout.Item("MenuItems").UIItems = listMenuItemsEnum
	else:
		PPG.PPGLayout.Item("MenuItems").UIItems = list()
	
	if not(CurrentMenuItemNumber in listMenuItemsEnum):
		PPG.MenuItems.Value = -1

def RefreshMenuSets():
	Print ("Qpop: RefreshMenuSets called",c.siVerbose)
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	MenuSetsNameList = list()
	MenuSetsNameListEnum = list()
	
	for oSet in globalQPopMenuSets.items:
		MenuSetsNameList.append(oSet.name)
	
	MenuSetsNameList.sort()
	
	for SetName in MenuSetsNameList:
		MenuSetsNameListEnum.append("(ms) " + SetName)
		MenuSetsNameListEnum.append(SetName)
	
	PPG.PPGLayout.Item ("MenuSets").UIItems = MenuSetsNameListEnum
		
		
	
def RefreshMenuItemList():
	Print("Qpop: RefreshMenuItemList called",c.siVerbose)
	#knownMenuItems = globalQPopMenuItems.items
	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	#Print("globalQPopMenuItems has " + str(len(globalQPopMenuItems.items)) + " menu items: "  )
	listKnownMenuItems = list(globalQPopMenuItems.items)
	#Print ("listKnownMenuItems is: " + str(listKnownMenuItems))
	listKnownMenuItem_Names = list()
	listMenuItem_Names = list()
	listMenuItem_NamesEnum = list()
	
	for menuItem in listKnownMenuItems:
		listKnownMenuItem_Names.append(menuItem.name)
	
	MenuItem_Category =  (PPG.MenuItem_Category.Value) #Get the currently selected menu item category value from the category selector in the PPG's UI
	#Print ("Selected MenuItem_Category is: " + str(MenuItem_Category ))

	if MenuItem_Category == "_ALL_":
		listMenuItem_Names = listKnownMenuItem_Names
	else:
		for menuItem in listKnownMenuItems:
			if menuItem.category == MenuItem_Category:
				listMenuItem_Names.append(menuItem.name)

	listMenuItem_Names.sort()

	for MenuItem_Name in listMenuItem_Names:
		listMenuItem_NamesEnum.append("(s) " + MenuItem_Name) #Add the name to the pulldown menu's UIItems enum
		listMenuItem_NamesEnum.append(MenuItem_Name) #Add the value to the pulldown menu's UIItems enum
	
	#Print ((str(listMenuItem_Names), c.siVerbose))
	PPG.PPGLayout.Item ("MenuItemList").UIItems = listMenuItem_NamesEnum

	
def RefreshCommandList():
	Print("Qpop: RefreshCommandList called",c.siVerbose)
	CommandListEnum = list()
	ComCatName = PPG.CommandCategory.Value
	OnlyHotkeyable = PPG.ShowHotkeyableOnly.Value
	ShowScriptingName = PPG.ShowScriptingNameInBrackets.Value
	CommandListStorage = list()
	
	if ComCatName == "_ALL_":
		for Command in App.Commands:
			if Command.Name != "":
				if OnlyHotkeyable == True: #Show only hotkeyable commands
					if Command.SupportsKeyAssignment == True:
						CommandEntry = Command.Name
						if ShowScriptingName == True:
							ScriptingNameString = " (" + Command.ScriptingName + ")"
							CommandEntry = CommandEntry  + ScriptingNameString
						CommandList = list()
						CommandList.append(CommandEntry)
						CommandList.append(Command.UID)
						CommandListStorage.append(CommandList)


				else: #Also show non-hotkeyable commands
					CommandEntry = Command.Name
					if ShowScriptingName == True:
						ScriptingNameString = " (" + Command.ScriptingName + ")"
						CommandEntry = CommandEntry  + ScriptingNameString
						
					CommandList = list()
					CommandList.append(CommandEntry)
					CommandList.append(Command.UID)
					CommandListStorage.append(CommandList)
				

	else: #We are listing commands of a specific category...
		FilteredCommands = App.Commands.Filter(ComCatName)
		#Print("Filtered commands found: " + str(len(FilteredCommands)))
		for Command in FilteredCommands:	
			if Command.Name != "":
				#CommandEntry = "None"
				if OnlyHotkeyable == True:
					if Command.SupportsKeyAssignment == True:
						CommandEntry = Command.Name
						if ShowScriptingName == True:
							ScriptingNameString = " (" + Command.ScriptingName + ")"
							CommandEntry = CommandEntry  + ScriptingNameString
						
						CommandList = list()
						CommandList.append(CommandEntry)
						CommandList.append(Command.UID)
						CommandListStorage.append(CommandList)
							
				else:
					CommandEntry = Command.Name
					if ShowScriptingName == True:
						ScriptingNameString = " (" + Command.ScriptingName + ")"
						CommandEntry = CommandEntry  + ScriptingNameString
							
					CommandList = list()
					CommandList.append(CommandEntry)
					CommandList.append(Command.UID)
					CommandListStorage.append(CommandList)

	CommandListStorage.sort()
	
	for oEntry in CommandListStorage:
		NameInList = oEntry[0]
		while NameInList in CommandListEnum: #Some softimage commands appear more than once with the same name, we need to make sure that the name is unique in the list, so we add spaces
				NameInList = NameInList + " "

		CommandListEnum.append("(c) " + NameInList)
		CommandListEnum.append(oEntry[1])
	PPG.PPGLayout.Item ("CommandList").UIItems = CommandListEnum
	
def QPopSaveConfiguration(fileName):
	Print("Qpop: QPopSaveConfiguration called", c.siVerbose)
	
	#Lets check if the path exists
	folderName = os.path.dirname (fileName) #.rsplit("\\")
	if os.path.exists(folderName):
		globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems").items
		globalQPopMenus = App.GetGlobal("globalQPopMenus").items
		globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets").items
		globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts").items
		globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures").items
		globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents").items
		

		oConfigDoc = DOM.Document()
		RootNode = oConfigDoc.createElement("QPopComponents") #Create Root level node
		oConfigDoc.appendChild(RootNode)

		MenuItemsNode = oConfigDoc.createElement("QPopMenuItems")
		RootNode.appendChild(MenuItemsNode)
		MenusNode = oConfigDoc.createElement("QPopMenus")
		RootNode.appendChild(MenusNode)
		MenuSetsNode = oConfigDoc.createElement("QPopMenuSets")
		RootNode.appendChild(MenuSetsNode)
		MenuDisplayContextsNode = oConfigDoc.createElement("QPopMenuDisplayContexts")
		RootNode.appendChild(MenuDisplayContextsNode)
		ViewsNode = oConfigDoc.createElement("QPopViewSignatures")
		RootNode.appendChild(ViewsNode)
		DisplayEventsNode = oConfigDoc.createElement("QPopDisplayEvents")
		RootNode.appendChild(DisplayEventsNode)

	# === Save Menu Items ===	
		for oMenuItem in globalQPopMenuItems:
			MenuItemNode = oConfigDoc.createElement("QPopMenuItem")
			MenuItemNode.setAttribute("UID", oMenuItem.UID)
			MenuItemNode.setAttribute("name", oMenuItem.name)
			MenuItemNode.setAttribute("type", oMenuItem.type)
			MenuItemNode.setAttribute("category", oMenuItem.category)
			MenuItemNode.setAttribute("language", oMenuItem.language)
			oMenuItemCode = oConfigDoc.createTextNode (oMenuItem.code)
			oMenuItemCode.nodeValue = str(oMenuItem.code)
			MenuItemNode.appendChild(oMenuItemCode)	
			MenuItemsNode.appendChild(MenuItemNode)	
		
	# === Save Menus ===
		for oMenu in globalQPopMenus:
			MenuNode = oConfigDoc.createElement("QPopMenu")
			MenuNode.setAttribute("name", str(oMenu.name))
			MenuNode.setAttribute("type", oMenu.type)
			MenuNode.setAttribute("language", oMenu.language)
			oMenuCode = oConfigDoc.createTextNode (oMenu.code)
			oMenuCode.nodeValue = str(oMenu.code)
			MenuNode.appendChild(oMenuCode)	
			
			MenuItems = getattr(oMenu, "items")
			NameList = list()
			for MenuItem in MenuItems:
				if MenuItem.type == "CommandPlaceholder":
					NameList.append("Command")
				else:
					NameList.append(str(MenuItem.type))
				NameList.append(str(MenuItem.name))
				NameList.append(str(MenuItem.UID))
			
			MenuItemsNames = ListToString(NameList)
			MenuNode.setAttribute("items", MenuItemsNames)
			MenusNode.appendChild(MenuNode)
		
	# === Save Menu Sets ===
		for oMenuSet in globalQPopMenuSets:
			MenuSetNode = oConfigDoc.createElement("QPopMenuSet")
			MenuSetNode.setAttribute("name", oMenuSet.name)
			MenuSetNode.setAttribute("type", oMenuSet.type)
			
			Attributes = ["AMenus","AContexts","BMenus","BContexts","CMenus","CContexts","DMenus","DContexts"]
			for Attr in Attributes:
				AttrList = list()
				oItems = getattr(oMenuSet, Attr)
				#Print(Attr + ": " + str(oItems))
				for oItem in oItems:
					if oItem != None:
						AttrList.append (str(oItem.name))
					else:
						AttrList.append("None")
				AttrString = ListToString(AttrList)
				#Print(AttrString)
				MenuSetNode.setAttribute(Attr, AttrString)
			MenuSetsNode.appendChild(MenuSetNode)
	
	# === Save Menu Contexts ===
		for oMenuContext in globalQPopMenuDisplayContexts:
			MenuContextNode = oConfigDoc.createElement("QPopMenuDisplayContext")
			MenuContextNode.setAttribute("name", str(oMenuContext.name))
			MenuContextNode.setAttribute("type", str(oMenuContext.type))
			MenuContextNode.setAttribute("language", str(oMenuContext.language))	
			#MenuContextNode.setAttribute("code", str(oMenuContext.code))	
			oMenuContextCode = oConfigDoc.createTextNode ("code")
			oMenuContextCode.nodeValue = str(oMenuContext.code)
			MenuContextNode.appendChild(oMenuContextCode)
			MenuDisplayContextsNode.appendChild(MenuContextNode)
		
	# === Save View Signatures ===
		for oSignature in globalQPopViewSignatures:
			ViewSignatureNode = oConfigDoc.createElement("QPopViewSignature")
			ViewSignatureNode.setAttribute("name",oSignature.name)
			ViewSignatureNode.setAttribute("type", oSignature.type)
			ViewSignatureNode.setAttribute("signature", str(oSignature.signature))
			MenuSetNames = list()
			for MenuSet in oSignature.menuSets:
				MenuSetNames.append(MenuSet.name)
			MenuSetNamesString = ListToString(MenuSetNames)
			
			ViewSignatureNode.setAttribute("menuSets", MenuSetNamesString)
			ViewsNode.appendChild(ViewSignatureNode)

	# === Save Display Events ===
		for oDisplayEvent in globalQPopDisplayEvents:
			#Print("Saving Display events")
			DisplayEventNode = oConfigDoc.createElement("QPopDisplayEvent")
			DisplayEventNode.setAttribute("number", str(oDisplayEvent.number))
			DisplayEventNode.setAttribute("type", oDisplayEvent.type)
			DisplayEventNode.setAttribute("key", str(oDisplayEvent.key))
			DisplayEventNode.setAttribute("keyMask", str(oDisplayEvent.keyMask))
			DisplayEventsNode.appendChild(DisplayEventNode)	
			#Print("\nDisplayeventsnode with number " + str(oDisplayEvent.number) + " saved\n")

		#Finally write out the whole configuration document as an xml file
		try:
			ConfigDocFile = open(fileName,"w")
			oConfigDoc.writexml(ConfigDocFile,indent = "",addindent = "", newl = "")
			ConfigDocFile.close()
			return True
		except:
			Print("Saving QPop Configuration to '" + fileName + "' failed! Please check write permissions and try again.",c.siError)
			return False
	else:
		Print("Saving QPop Configuration to '" + fileName + "' failed because the folder does not exist. Check the path and try again.", c.siError)
	
def QPopLoadConfiguration(fileName):
	Print("Qpop: QPopLoadConfiguration called", c.siVerbose)

	if fileName != "":
		if os.path.isfile(fileName) == True:
			QPopConfigFile = DOM.parse(fileName)
			#In case the file could be loaded and parsed we can destroy the existing configuration in memory and refill it with the new data from the file
			initQPopGlobals(True)
			globalQPopSeparators = App.GetGlobal("globalQPopSeparators")
			globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
			globalQPopMenus = App.GetGlobal("globalQPopMenus")
			globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
			globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
			globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
			globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents")
			
		#=== Start creating QPop objects from the file data ===
			Components = QPopConfigFile.getElementsByTagName("QPopComponents")

			for Component in Components[0].childNodes:
				if Component.localName == "QPopMenuItems":
					QPopMenuItems = Component.childNodes
					for MenuItem in QPopMenuItems:
						if str(MenuItem.localName) != "None":
							#Print("MenuItemLocalName is: " + MenuItem.localName)
							NewMenuItem = App.CreateQPop("MenuItem")
							NewMenuItem.name = MenuItem.getAttribute("name")
							NewMenuItem.category = MenuItem.getAttribute("category")
							NewMenuItem.language = MenuItem.getAttribute("language")
							CodeNode = MenuItem.childNodes[0]
							NewMenuItem.code = str(CodeNode.nodeValue)
							globalQPopMenuItems.addMenuItem(NewMenuItem)

			for Component in Components[0].childNodes:			
				if Component.localName == "QPopMenus":
					QPopMenus = Component.childNodes
					#Create all menus first to avoid a race condition (menus can contain other menus)
					for Menu in QPopMenus: 
						if str(Menu.localName) != "None":
							#Print("MenuLocalName is: " + Menu.localName)
							oNewMenu = App.CreateQPop("Menu")
							globalQPopMenus.addMenu(oNewMenu)
							oNewMenu.name = Menu.getAttribute("name")
							oNewMenu.language = Menu.getAttribute("language")
							CodeNode = Menu.childNodes[0]
							oNewMenu.code = str(CodeNode.nodeValue)
					
					#Then fill the menus with menu items, menus, commands and separators
					for Menu in QPopMenus: 
						if str(Menu.localName) != "None":
							oNewMenu = getQPopMenuByName(Menu.getAttribute("name"))
							MenuItemNames = str(Menu.getAttribute("items"))
							#Print ("MenuItems are:"  + str(MenuItemNames))
							MenuItemNamesList = MenuItemNames.split(";")
							i = 0
							while i < (len(MenuItemNamesList)-1):
								if MenuItemNamesList[i] == "QPopMenuItem":
									oMenuItem = getQPopMenuItemByName(MenuItemNamesList[i+1])
									if oMenuItem != None:
										oNewMenu.insertMenuItem (len(oNewMenu.items), oMenuItem)
								if MenuItemNamesList[i] == "QPopMenu":
									oMenuItem = getQPopMenuByName(MenuItemNamesList[i+1])
									if oMenuItem != None:
										oNewMenu.insertMenuItem (len(oNewMenu.items), oMenuItem)
								if MenuItemNamesList[i] == "Command":
									oMenuItem = App.Commands(MenuItemNamesList[i+1]) #Get Command by name
									#oMenuItem = getCommandByUID(MenuItemNamesList[i+2]) #Get Command by UID through a Python function, which is slower but safer
									#oMenuItem = App.GetCommandByUID(MenuItemNamesList[i+2]) #Get Command by UID through custom c++ command, which is much faster than Python but still slow
									
									if oMenuItem != None:
										oNewMenu.insertMenuItem (len(oNewMenu.items), oMenuItem)
									else: #Command could not be found? Insert Dummy command instead, it might become available at a later session
										#Print("A command named '" + str(MenuItemNamesList[i+1]) + "' could not be found!", c.siWarning)
										oDummyCmd = App.CreateQPop("CommandPlaceholder")
										oDummyCmd.name = (MenuItemNamesList[i+1])
										
										oDummyCmd.UID = (MenuItemNamesList[i+2])
										oNewMenu.insertMenuItem (len(oNewMenu.items), oDummyCmd)
										
								if MenuItemNamesList[i] == "QPopSeparator":
									oMenuItem = getQPopSeparatorByName(MenuItemNamesList[i+1])
									if oMenuItem != None:
										oNewMenu.insertMenuItem (len(oNewMenu.items), oMenuItem)
								i = i+3 #Increase counter by 3 to get to the next item (we save 3 properties per item: type, name, UID)
				
			for Component in Components[0].childNodes:
				if Component.localName == "QPopMenuDisplayContexts":
					QPopContexts = Component.childNodes
					for Context in QPopContexts:
						if str(Context.localName) == "QPopMenuDisplayContext":
							oNewContext = App.CreateQPop("MenuDisplayContext")
							oNewContext.name = Context.getAttribute("name")
							oNewContext.language = Context.getAttribute("language")
							CodeNode = Context.childNodes[0]
							oNewContext.code = str(CodeNode.nodeValue)
							result = globalQPopMenuDisplayContexts.addContext(oNewContext)

								
			for Component in Components[0].childNodes:
				if Component.localName == "QPopMenuSets":
					QPopMenuSets = Component.childNodes
					for Set in QPopMenuSets:
						if str(Set.localName) == ("QPopMenuSet"):
							oNewMenuSet = App.CreateQPop("MenuSet")
							oNewMenuSet.name = Set.getAttribute("name")
							
							AContextNames = ((Set.getAttribute("AContexts")).split(";"))
							AMenuNames = ((Set.getAttribute("AMenus")).split(";"))

							if len(AContextNames) == len(AMenuNames):
								for AContextName in AContextNames:
									oAContext = getQPopMenuDisplayContextByName(str(AContextName))
									if oAContext != None:
										ContextIndex = AContextNames.index(AContextName)
										AMenuName = AMenuNames[ContextIndex]
										oAMenu = getQPopMenuByName(AMenuName)
										oNewMenuSet.insertContext (len(oNewMenuSet.AContexts), oAContext, "A")
										oNewMenuSet.insertMenuAtIndex (len(oNewMenuSet.AMenus), oAMenu, "A")
							
							BContextNames = ((Set.getAttribute("BContexts")).split(";"))
							BMenuNames = ((Set.getAttribute("BMenus")).split(";"))

							if len(BContextNames) == len(BMenuNames):
								for BContextName in BContextNames:
									oBContext = getQPopMenuDisplayContextByName(str(BContextName))
									if oBContext != None:
										ContextIndex = BContextNames.index(BContextName)
										BMenuName = BMenuNames[ContextIndex]
										oBMenu = getQPopMenuByName(BMenuName)
										oNewMenuSet.insertContext (len(oNewMenuSet.BContexts), oBContext, "B")
										oNewMenuSet.insertMenuAtIndex (len(oNewMenuSet.BMenus), oBMenu, "B")
							
							CContextNames = ((Set.getAttribute("CContexts")).split(";"))
							CMenuNames = ((Set.getAttribute("CMenus")).split(";"))

							if len(CContextNames) == len(CMenuNames):
								for CContextName in CContextNames:
									oCContext = getQPopMenuDisplayContextByName(str(CContextName))
									if oCContext != None:
										ContextIndex = CContextNames.index(CContextName)
										CMenuName = CMenuNames[ContextIndex]
										oCMenu = getQPopMenuByName(CMenuName)
										oNewMenuSet.insertContext (len(oNewMenuSet.CContexts), oCContext, "C")
										oNewMenuSet.insertMenuAtIndex (len(oNewMenuSet.CMenus), oCMenu, "C")
										
							DContextNames = ((Set.getAttribute("DContexts")).split(";"))
							DMenuNames = ((Set.getAttribute("DMenus")).split(";"))

							if len(DContextNames) == len(DMenuNames):
								for DContextName in DContextNames:
									oDContext = getQPopMenuDisplayContextByName(str(DContextName))
									if oDContext != None:
										ContextIndex = DContextNames.index(DContextName)
										DMenuName = DMenuNames[ContextIndex]
										oDMenu = getQPopMenuByName(DMenuName)
										oNewMenuSet.insertContext (len(oNewMenuSet.DContexts), oDContext, "D")
										oNewMenuSet.insertMenuAtIndex (len(oNewMenuSet.DMenus), oDMenu, "D")
							globalQPopMenuSets.addSet(oNewMenuSet)

							
			for Component in Components[0].childNodes:
				if Component.localName == "QPopViewSignatures":
					QPopSignatures = Component.childNodes
					for Signature in QPopSignatures:
						if str(Signature.localName) == "QPopViewSignature":
							oNewSignature = App.CreateQPop("ViewSignature")
							oNewSignature.name = Signature.getAttribute("name")

							oNewSignature.signature = Signature.getAttribute("signature")

							MenuSets = Signature.getAttribute("menuSets").split(";")

							for MenuSet in MenuSets:
								oMenuSet = getQPopMenuSetByName(MenuSet)
								oNewSignature.insertMenuSet(len(oNewSignature.menuSets), oMenuSet)

							result = globalQPopViewSignatures.addSignature(oNewSignature)
								
			for Component in Components[0].childNodes:
				if Component.localName == "QPopDisplayEvents":
					QPopDisplayEvents = Component.childNodes
					for Event in QPopDisplayEvents:
						if str(Event.localName) == "QPopDisplayEvent":
							oNewDisplayEvent = App.CreateQPop("DisplayEvent")
							oNewDisplayEvent.number = int(Event.getAttribute("number"))
							#Print("\nFound Display Event Number " + str(oNewDisplayEvent.number))
							oNewDisplayEvent.key = int(Event.getAttribute("key"))
							oNewDisplayEvent.keyMask = int(Event.getAttribute("keyMask"))
							result = globalQPopDisplayEvents.addEvent(oNewDisplayEvent)
			return True
		else:
			Print("Could not load QPop Configuration from '" + str(fileName) + "' because the file could not be found!", c.siError)
			return False



def RefreshDisplayEventsKeys():
	Print("Qpop: RefreshDisplayEventsKeys called", c.siVerbose)
	globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents").items
	if len(globalQPopDisplayEvents) > 0:
		oSelectedEvent = globalQPopDisplayEvents[PPG.DisplayEvent.Value]
	else:
		#Print("An error occured trying to determine currently selected event...")
		oSelectedEvent = None
	
	if oSelectedEvent != None:
		#Print("Selected event is not None...")
		PPG.DisplayEventKey.Value = oSelectedEvent.key
		PPG.DisplayEventKeyMask.Value = oSelectedEvent.keyMask
		
		PPG.DisplayEventKey.SetCapabilityFlag (c.siReadOnly,False)
		PPG.DisplayEventKeyMask.SetCapabilityFlag (c.siReadOnly,False)
		PPG.DisplayEventKeys_Record.SetCapabilityFlag (c.siReadOnly,False)
				
	else:
		PPG.DisplayEventKey.Value = 0
		PPG.DisplayEventKeyMask = 0
		
		PPG.DisplayEventKey.SetCapabilityFlag (c.siReadOnly,True)
		PPG.DisplayEventKeyMask.SetCapabilityFlag (c.siReadOnly,True)
		PPG.DisplayEventKeys_Record.SetCapabilityFlag (c.siReadOnly,True)


def RefreshDisplayEvents():
	Print("Qpop: RefreshDisplayEvents called", c.siVerbose)
	globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents").items
	DisplayEventsEnumList = list()
	Counter = 0
	for oDisplayEvent in globalQPopDisplayEvents:
		DisplayEventsEnumList.append ("Display Qpop Menu Set " + str(Counter))
		DisplayEventsEnumList.append (Counter)
		Counter +=1
	
	PPG.PPGLayout.Item("DisplayEvent").UIItems = DisplayEventsEnumList
	if len(globalQPopDisplayEvents) == 0:
		PPG.DisplayEvent.Value = -1
		


#===================================== Plugin Command Callbacks ==========================================================

def DisplayMenuSet( MenuSetIndex ):
	#Print("DisplayQPopMenuSet_Execute called", c.siVerbose)
	#t1 = time.clock()
	ViewSignature = GetView()
	#t3 = time.clock()
	#Print ("Found View Signature under mouse: " + str(ViewSignature))
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")
	
	if globalQPopViewSignatures != None:
		oCurrentView = None
		for oView in globalQPopViewSignatures.items:
			if oView.signature == ViewSignature:
				oCurrentView = oView
				break
		
		oMenuSet = None
		if oCurrentView != None:
			try:
				oMenuSet = oCurrentView.menuSets[MenuSetIndex]
			except:
				Print("There is currently no QPop Menu Set " + str(MenuSetIndex) + " defined for view '" + oCurrentView.name + "!", c.siVerbose)
		
		if oMenuSet != None:
			
			oAMenu = None; #AMenuItemList = list()
			oBMenu = None; #BMenuItemList = list()
			oCMenu = None; #CMenuItemList = list()
			oDMenu = None; #DMenuItemList = list()
			oMenus = list()
			
			#Quadrants = ((oMenuSet.AContexts,oMenuSet.AMenus),(oMenuSet.BContexts,oMenuSet.BMenus),(oMenuSet.CContexts,oMenuSet.CMenus),(oMenuSet.DContexts,oMenuSet.DMenus))
			#Find menu A by evaluating all A-quadrant menu's context functions taking the first one that returns true
			
			for RuleIndex in range(0,len(oMenuSet.AContexts)):
				Code = oMenuSet.AContexts[RuleIndex].code + ("\nDisplayMenu = QPopContext_Eval()")
				#Language = oMenuSet.AContexts[RuleIndex].language
				DisplayMenu = False
				try:
					#DisplayMenu = App.ExecuteScriptCode( Code, Language, "QPopContext_Eval",[]) #This function returns a variant containing the result of the executed function and...something else we don't care about 
					exec (Code)
				except:
					Print("An Error occurred executing the QPop Diplay Context '" + oMenuSet.AContexts[RuleIndex].name +"'", c.siError)
					DisplayMenu = False
				if DisplayMenu == True:
					oAMenu = oMenuSet.AMenus[RuleIndex]
					break
			
			oMenus.append(oAMenu) #Add the found menu to the Menus list
			
			#Find menu B by evaluating all B-quadrant menu's context functions taking the first one that returns true
			for RuleIndex in range(0,len(oMenuSet.BContexts)):
				Code = oMenuSet.BContexts[RuleIndex].code + ("\nDisplayMenu = QPopContext_Eval()")
				#Language = oMenuSet.BContexts[RuleIndex].language
				DisplayMenu = False
				try:
				#DisplayMenu = App.ExecuteScriptCode( Code, Language, "QPopContext_Eval",[]) #This function returns a variant containing the result of the executed function and...something else we don't care about 
					exec (Code)
				except:
					Print("An Error occurred executing the QPop Diplay Context '" + oMenuSet.BContexts[RuleIndex].name +"'", c.siError)
					DisplayMenu = False
				if DisplayMenu == True:
					oBMenu = oMenuSet.BMenus[RuleIndex]
					break
			
			oMenus.append(oBMenu) #Add the found menu to the Menus list
			
			#Find menu C by evaluating all C-quadrant menu's context functions taking the first one that returns true
			for RuleIndex in range(0,len(oMenuSet.CContexts)):
				Code = oMenuSet.CContexts[RuleIndex].code + ("\nDisplayMenu = QPopContext_Eval()")
				#Language = oMenuSet.CContexts[RuleIndex].language
				DisplayMenu = False
				try:
				#DisplayMenu = App.ExecuteScriptCode( Code, Language, "QPopContext_Eval",[]) #This function returns a variant containing the result of the executed function and...something else we don't care about 
					exec (Code)
				except:
					Print("An Error occurred executing the QPop Diplay Context '" + oMenuSet.CContexts[RuleIndex].name +"'", c.siError)
					DisplayMenu = False
				if DisplayMenu == True:
					oCMenu = oMenuSet.CMenus[RuleIndex]
					break
			
			oMenus.append(oCMenu) #Add the found menu to the Menus list
			
			#Find menu D by evaluating all D-quadrant menu's context functions taking the first one that returns true
			for RuleIndex in range(0,len(oMenuSet.DContexts)):
				Code = oMenuSet.DContexts[RuleIndex].code + ("\nDisplayMenu = QPopContext_Eval()")
				#Language = oMenuSet.DContexts[RuleIndex].language
				DisplayMenu = False
				try:
				#DisplayMenu = App.ExecuteScriptCode( Code, Language, "QPopContext_Eval",[]) #This function returns a variant containing the result of the executed function and...something else we don't care about 
					exec (Code)
				except:
					Print("An Error occurred executing the QPop Diplay Context '" + oMenuSet.DContexts[RuleIndex].name +"'", c.siError)
					DisplayMenu = False
				if DisplayMenu == True:
					oDMenu = oMenuSet.DMenus[RuleIndex]
					break
			
			oMenus.append(oDMenu) #Add the found menu to the Menus list
			
			#t4 = time.clock()
						
			#Find Submenus
			NewMenuFound = True

			CheckedMenus = list()
			while NewMenuFound == True:
				NewMenuFound = False
				for oMenu in oMenus: #Search for submenus in  menus A to D, if any
					if oMenu != None and oMenu not in CheckedMenus:
						Language = oMenu.language
						Code = oMenu.code
						if Code != "":
							ArgList = list(); ArgList.append(oMenu) #QPopMenu_Eval function takes it's own menu as an argument 
							try:
								App.ExecuteScriptCode(Code, Language,"QPopMenu_Eval",ArgList) #Execute the menu's script code to give it the chance to fill itself with whatever items (maybe even more submenus)
							except:
								Print("An Error occured executing QPop Menu's '" + oMenu.name + "' script code, please see script editor for details!", c.siError)
												
						for oMenuItem in oMenu.items:
							if oMenuItem.type == "QPopMenu":
								if not (oMenuItem in oMenus):
									oMenus.append(oMenuItem)
									NewMenuFound = True

						
						for oMenuItem in oMenu.tempItems:
							if oMenuItem.type == "QPopMenu":
								if not (oMenuItem in oMenus):
									oMenus.append(oMenuItem)
									NewMenuFound = True

						
						CheckedMenus.append(oMenu)
			
			#============ Build the QPop Menu string from found menus and submenus	==========================
			QPopString = str()
			MenuCounter = 0
			MenuString = "" #Start the MenuSet string
			if oMenus != [None,None,None,None]:
				for oMenu in oMenus: 
					MenuString = MenuString + "[" #Start the menu string

					if oMenu != None:
						if len(oMenu.items) == 0:
							MenuString = MenuString + "[[Empty]" +  "[-1]" + "[3]" + "]"
						else:
							if MenuCounter == 2 or MenuCounter == 3: #Add the title at the beginning of the menu in case it's menu 2 or 3
								MenuString = MenuString + "[[" + oMenu.name + "]"  + "[-1]" + "[3]" + "]" 
							
							#Add regular menu items to the display string
							for oItem in oMenu.items:
								if oItem.type == "Command":
									MenuString = MenuString + "[[" + oItem.name + "]"  + "[-1]" + "[1]" + "]" 
								if oItem.type == "QPopMenuItem":
									MenuString = MenuString + "[[" + oItem.name + "]"  + "[-1]" + "[1]" + "]" 
								if oItem.type == "QPopMenu":
									try:
										MenuIndex = oMenus.index(oItem)
										MenuString = MenuString + "[[" + oItem.name + "]" + "[" + str(MenuIndex) + "]" + "[1]" + "]" 
									except:
										DoNothing = True
								if oItem.type == "QPopSeparator":
									MenuString = MenuString + "[]" 

							#Add temporary menu items to the display string
							for oItem in oMenu.tempItems:
								if oItem.type == "Command":
									MenuString = MenuString + "[[" + oItem.name + "]"  + "[-1]" + "[1]" + "]" 
								if oItem.type == "QPopMenuItem":
									MenuString = MenuString + "[[" + oItem.name + "]"  + "[-1]" + "[1]" + "]" 
								if oItem.type == "QPopMenu":
									try:
										MenuIndex = oMenus.index(oItem)
										MenuString = MenuString + "[[" + oItem.name + "]"  + "[" + str(MenuIndex) + "]" + "[1]" + "]" 
									except:
										DoNothing = True
								if oItem.type == "QPopSeparator":
									MenuString = MenuString + "[[]"  + "[-1]" + "[0]" + "]" 
							#Add the title at the end of the menu in case it's menu 0 or 1
							if MenuCounter == 0 or MenuCounter == 1:
								MenuString = MenuString + "[[" + oMenu.name + "]"  + "[-1]" + "[3]" + "]" 

							
					MenuString = MenuString + "]" #Close the menu string
					MenuCounter +=1
				
				"""
				if App.GetValue("Preferences.QPop.IncludeWindowHandle") == True:
					XSIWinHandle = getXSITopLevelWindow()
					MenuString = MenuString + "[" + str(XSIWinHandle) + "]"

				if App.GetValue("Preferences.QPop.ShowQpopMenuString") == True:
					Print(MenuString) #Debug option to actually print out the string that will be passed to the Qpop menu renderer
				
				
				#Finally Render the Quad Menu using the string we just built and wait for user to pick an item
				t2 = time.clock()
				
				Print("Time taken to get view signature was " + str(t3 - t1) + " seconds.")
				Print("Time taken to evaluate the 4 main menu's contexts was " + str(t4 - t1) + " seconds.")
				Print("Time taken to prepare whole menu string so far was " + str(t2 - t1) + " seconds.")
				"""
				
				MenuItemToExecute = App.QPop(MenuString)

				
				#===========  Find the clicked menu item from the returned value ===========
				oClickedMenuItem = None
				if ((MenuItemToExecute[0] != -1) and (MenuItemToExecute[1] != -1)):
					#Print("MenuItemToExecute is: " + str(MenuItemToExecute))
					oClickedMenu = oMenus[MenuItemToExecute[0]] #get the clicked QpopMenu object
					if oClickedMenu != None:
						
						#Was one of the lower two menus selected?
						if MenuItemToExecute[0] == 2 or MenuItemToExecute[0] == 3: 
							if MenuItemToExecute[1] == 0: #Was the menu Title selected?
								globalQPopLastUsedItem = App.GetGlobal("globalQPopLastUsedItem")
								oClickedMenuItem = globalQPopLastUsedItem.item 
							else:
								#Was one of the temp menu items clicked on?
								if MenuItemToExecute[1] > (len(oClickedMenu.items)): 
									oClickedMenuItem = oClickedMenu.tempItems[MenuItemToExecute[1]-(len(oClickedMenu.items)+1)] #get the clicked temp menu item
								else:
									oClickedMenuItem = oClickedMenu.items[MenuItemToExecute[1]-1] #Subtract the menu title entry 
							#if oClickedMenuItem.type == "Command" or oClickedMenuItem.type == "QPopMenuItem":
								#return oClickedMenuItem
							
						#Was one of the upper two menus selected?
						if MenuItemToExecute[0] == 0 or MenuItemToExecute[0] == 1: 
							if MenuItemToExecute[1] == (len(oClickedMenu.items) ): #Was the menu Title selected?
								globalQPopLastUsedItem = App.GetGlobal("globalQPopLastUsedItem")
								oClickedMenuItem = globalQPopLastUsedItem.item #When clicking on any of the Menu Titles repeat the last command
							else:
								#Was one of the temp menu items clicked on?
								if MenuItemToExecute[1] > (len(oClickedMenu.items)-1): 
									oClickedMenuItem = oClickedMenu.tempItems[MenuItemToExecute[1]-(len(oClickedMenu.items))]
								else:
									oClickedMenuItem = oClickedMenu.items[MenuItemToExecute[1]]
						
						#Was any of the sub-menus selected?
						if MenuItemToExecute[0] > 3:
							if len(oClickedMenu.items) > 0: #Are there any menu items to check for in the first place?
								if MenuItemToExecute[1] > (len(oClickedMenu.items)-1): #Was one of the temp menu items clicked on?
									oClickedMenuItem = oClickedMenu.tempItems[MenuItemToExecute[1]-(len(oClickedMenu.items))]
								else:
									oClickedMenuItem = oClickedMenu.items[MenuItemToExecute[1]]
							elif len(oClickedMenu.tempItems) > 0: #No Menu items, but maybe there are temp menu items..
								oClickedMenuItem = oClickedMenu.tempItems[MenuItemToExecute[1]]
				
				if oClickedMenuItem != None:
					#if (oClickedMenuItem.type == "Command") or (oClickedMenuItem.type =="QPopMenuItem"):
					#Print("Clicked Menu Item is of type: " + oClickedMenuItem.type)
					return oClickedMenuItem
				else:
					return None

def QPopRepeatLastCommand_Init(in_Ctxt):
	oCmd = in_Ctxt.Source
	oCmd.SetFlag(c.siSupportsKeyAssignment,  True)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, False)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True	

def QPopRepeatLastCommand_Execute():
	Print("QPopRepeatLastCommand_Execute called", c.siVerbose)
	globalQPopLastUsedItem = App.GetGlobal("globalQPopLastUsedItem")
	oQPopMenuItem = globalQPopLastUsedItem.item
	if oQPopMenuItem != None:
		if str(type(oQPopMenuItem)) == "<type 'str'>":
			oQPopMenuItem = App.Commands(oQPopMenuItem)
	
	if oQPopMenuItem != None:		
		App.QPopExecuteMenuItem ( oQPopMenuItem )

def QPopDisplayMenuSet_0_Init( in_Ctxt ):
	oCmd = in_Ctxt.Source
	oCmd.SetFlag(c.siSupportsKeyAssignment, True)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True				

def QPopDisplayMenuSet_0_Execute():
	Print("QPopDisplayMenuSet_0_Execute called", c.siVerbose)
	if App.GetValue("Preferences.QPop.QPopEnabled") == true:
		oQPopMenuItem = DisplayMenuSet(0)
		if oQPopMenuItem != None:
			App.QPopExecuteMenuItem(oQPopMenuItem)
				

def QPopDisplayMenuSet_1_Init( in_Ctxt ):
	oCmd = in_Ctxt.Source
	oCmd.SetFlag(c.siSupportsKeyAssignment, True)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True				

def QPopDisplayMenuSet_1_Execute():
	Print("QPopDisplayMenuSet_1_Execute called", c.siVerbose)
	if App.GetValue("Preferences.QPop.QPopEnabled") == true:
		oQPopMenuItem = DisplayMenuSet(1)
		if oQPopMenuItem != None:
			App.QPopExecuteMenuItem ( oQPopMenuItem )

def QPopDisplayMenuSet_2_Init( in_Ctxt ):
	oCmd = in_Ctxt.Source
	oCmd.SetFlag(c.siSupportsKeyAssignment, True)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True				

def QPopDisplayMenuSet_2_Execute():
	Print("QPopDisplayMenuSet_1_Execute called", c.siVerbose)
	if App.GetValue("Preferences.QPop.QPopEnabled") == true:
		oQPopMenuItem = DisplayMenuSet(2)
		if oQPopMenuItem != None:
			App.QPopExecuteMenuItem ( oQPopMenuItem )

def QPopDisplayMenuSet_3_Init( in_Ctxt ):
	oCmd = in_Ctxt.Source
	oCmd.SetFlag(c.siSupportsKeyAssignment, True)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True				

def QPopDisplayMenuSet_3_Execute():
	Print("QPopDisplayMenuSet_1_Execute called", c.siVerbose)
	if App.GetValue("Preferences.QPop.QPopEnabled") == true:
		oQPopMenuItem = DisplayMenuSet(3)
		if oQPopMenuItem != None:
			App.QPopExecuteMenuItem ( oQPopMenuItem )	

def QPopExecuteMenuItem_Init( in_ctxt ):
	oCmd = in_ctxt.Source
	oCmd.ReturnValue = True
	oArgs = oCmd.Arguments
	oArgs.Add("oQPopMenuItem")
	oCmd.SetFlag(c.siSupportsKeyAssignment, False)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	oCmd.SetFlag(c.siAllowNotifications, False) #It's important this is false otherwise XSI becomes unstable when undoing the command (forgets about existing commands, but not always about the last executed one)
	return True
	
def QPopExecuteMenuItem_Execute ( oQPopMenuItem ):
	Print("QPopExecuteMenuItem_Execute called", c.siVerbose)
	globalQPopLastUsedItem = App.GetGlobal("globalQPopLastUsedItem")

	if oQPopMenuItem != None:
		SucessfullyExecuted = False
		#Instead of the actual command only it's name is given because Softimage has the tendency to forget commands (not always the
		#same command that was referenced) after undoing it when the command is referenced by a python object (e.g. a list or custom ActiveX class). 
		#Therefore we only work with command names instead and look up the command for execution again,
		#which imposes a neglectable speed penalty.

		if str(type(oQPopMenuItem)) == "<type 'unicode'>":
			oQPopMenuItem = App.Commands(oQPopMenuItem)

		if oQPopMenuItem.type == "Command":
			#oQPopMenuItemNew = App.Commands(oQPopMenuItem.name) #To prevent the command from operating in the previous objects context we get the original command object from Softimage again
			try:
				#oQPopMenuItemNew.Execute()
				oQPopMenuItem.Execute()
				SucessfullyExecuted = True	
				globalQPopLastUsedItem.set(oQPopMenuItem.name) #Just set the name of commands for safety
			except:
				SucessfullyExecuted = False
				raise
				
			
		if oQPopMenuItem.type == "QPopMenuItem":
			Code = (oQPopMenuItem.code)
			if Code != "":
				Language = (oQPopMenuItem.language)
				#TODO: ExecuteScriptCode should execute a specific function that can return objects to inspect
				try:
					App.ExecuteScriptCode( Code, Language) #, [ProcName], [Params] )
					globalQPopLastUsedItem.set(oQPopMenuItem)
					SucessfullyExecuted = True
				except:
					SucessfullyExecuted = False
					raise
			else:
				Print("QPop Menu item '" + oQPopMenuItem.name + "' has no code to execute!",c.siWarning)
		
		
		if SucessfullyExecuted == True:
			#globalQPopLastUsedItem.set(oQPopMenuItem) #Is this problematic with commands? (cannot be found after Undo?)
			return True
		else:	
			Print("An error occured executing QPop menu item '" + oQPopMenuItem.name + "! Please see scripteditor for details.", c.siError)
			return False
	
def CreateQPop_Init( io_Context ):
	oCmd = io_Context.Source
	oCmd.ReturnValue = true
	oArgs = oCmd.Arguments
	oArgs.Add("QPopType", c.siArgumentInput, "MenuItem")
	oCmd.SetFlag(c.siSupportsKeyAssignment, False)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	return True

def CreateQPop_Execute( QPopType ):
	QPopElement = None
	if QPopType == "LastUsedItem":
		QPopElement = QPopLastUsedItem()
	if QPopType == "MenuItem":
		QPopElement = QPopMenuItem()
	if QPopType == "MenuItems":
		QPopElement = QPopMenuItems()	
	if QPopType == "Menu":
		QPopElement = QPopMenu()
	if QPopType == "Menus":
		QPopElement = QPopMenus()
	if QPopType == "MenuSet":
		QPopElement = QPopMenuSet()		
	if QPopType == "MenuSets":
		QPopElement = QPopMenuSets()
	if QPopType == "MenuDisplayContext":
		QPopElement = QPopMenuDisplayContext()
	if QPopType == "MenuDisplayContexts":
		QPopElement = QPopMenuDisplayContexts()
	if QPopType == "DisplayEvent":
		QPopElement = QPopDisplayEvent()
	if QPopType == "DisplayEvents":
		QPopElement = QPopDisplayEvents()
	if QPopType == "ViewSignature":
		QPopElement = QPopViewSignature()
	if QPopType == "ViewSignatures":
		QPopElement = QPopViewSignatures()
	if QPopType == "ConfigStatus":
		QPopElement = QPopConfigStatus()
	if QPopType == "Separator":
		QPopElement = QPopSeparator()
	if QPopType == "Separators":
		QPopElement = QPopSeparators()
	if QPopType == "CommandPlaceholder":
		QPopElement = QPopCommandPlaceholder()
	
	# Class MUST be wrapped before being returned:
	if QPopElement != None:
		return win32com.server.util.wrap(QPopElement)
	else:
		return None
 
def QPopConfiguratorCreate_Init( in_ctxt ):
	oCmd = in_ctxt.Source
	oCmd.Description = "Create QPopConfigurator custom property at scene root level"
	oCmd.Tooltip = "Create QPopConfiguratorCreate custom property at scene root level"
	oCmd.ReturnValue = true
	oArgs = oCmd.Arguments
	oCmd.SetFlag(c.siSupportsKeyAssignment, False)
	oCmd.SetFlag(c.siCannotBeUsedInBatch, True)
	oCmd.SetFlag(c.siNoLogging, True)
	return true
    
def QPopConfiguratorCreate_Execute(bCheckSingle = true): 
    Print("QPopConfiguratorCreate_Execute called",c.siVerbose)
    boolTest = false
    
    if bCheckSingle == true:
        colGrannyGlobals = XSIFactory.CreateActiveXObject( "XSI.Collection" )
        A = App.FindObjects( "", "{76332571-D242-11d0-B69C-00AA003B3EA6}" ) #Find all Custom Properties
        
        for o in A:
            if o.Type == ("QPopConfigurator"): #Find all Custom Properties of Type "GrannyGlobals"
                colGrannyGlobals.Add (o) #And store them in a Collection
        if colGrannyGlobals.Count > 0: boolTest = true
                
    if boolTest == false:
        a = App.AddProp( "QPopConfigurator", App.ActiveSceneRoot, 0, "QPopConfigurator", "" )
        #Add the Custom property to the scene root. AddProp returns a ISIVTCollection that contains
        # 2 elements: The created Custom Property type and the Created Custom Properties as an XSICollection
        #This is not documented in the AddProp command help page, but in a separate page called
        #"Python Example: Working with the ISIVTCollection returned from a Command". Yuk!
        return a
    
    if boolTest == true:
        Print("QPopConfigurator Property already defined - Inspecting existing Property instead of creating a new one", c.siWarning)
        App.InspectObj (colGrannyGlobals(0))
        return false
		



# =================================== Plugin Event Callbacks =============================================

def QPopCheckDisplayEvents_OnEvent( in_ctxt ):  
	Print("QPopCheckDisplayEvents_OnEvent called",c.siVerbose)
 	KeyPressed = in_ctxt.GetAttribute("KeyCode")
	KeyMask = in_ctxt.GetAttribute("ShiftMask")

	globalQPopDisplayEvents = App.GetGlobal("globalQPopDisplayEvents").items
	Consumed = False
	
	#try:
	if App.Preferences.GetPreferenceValue("QPop.RecordViewSignature") == True:
		ViewSignature = GetView(True)
		App.SetValue("preferences.QPop.ViewSignature", ViewSignature, "")
		#App.Preferences.SetPreferenceValue("QPop.RecordViewSignature",0)
		App.SetValue("preferences.QPop.RecordViewSignature", False, "")
		Print("QPop View Signature of picked window: " + str(ViewSignature), c.siVerbose)
		Consumed = True
	#except:
		
	if App.Preferences.GetPreferenceValue("QPop.DisplayEventKeys_Record") == True:
		#if App.GetValue("preferences.QPop.DisplayEventKeys_Record") == True and Consumed == False: #Is user currently recording key events? We must query this from the PPG rather than from Preferences because the preference might not be known yet
		oSelectedEvent = globalQPopDisplayEvents[App.Preferences.GetPreferenceValue("QPop.DisplayEvent")] #Get the currently selected event in the list
		oSelectedEvent.key = KeyPressed
		oSelectedEvent.keyMask = KeyMask
		
		App.SetValue("preferences.QPop.DisplayEventKeys_Record",False)
		App.SetValue("preferences.QPop.DisplayEventKey", KeyPressed)
		App.SetValue("preferences.QPop.DisplayEventKeyMask", KeyMask)
		#Consumed = True
	#except:
		#Print("Something happened")
	
	try:
		if (App.Preferences.GetPreferenceValue("QPop.QPopEnabled") == True) and (Consumed == False): #Is Qpop enabled and the event has't been consumed yet?
			#Check known display events whether there is one that should react to the currently pressed key(s)
			for oDispEvent in globalQPopDisplayEvents:
				if ((oDispEvent.key == KeyPressed) and (oDispEvent.keyMask == KeyMask )):
					Consumed = True
					
					#Finally display the corresponding menu set associated with the display event and get the users input
					oChosenMenuItem = DisplayMenuSet( oDispEvent.number)
					
					if oChosenMenuItem != None:
						#Execute the menu item chosen by the user
						App.QPopExecuteMenuItem(oChosenMenuItem)
				break #We only care for the first found display event assuming there are no duplicates
	except:
		Print("An error occured in QPopCheckDisplayEvents while trying to display a menu!", c.siError)
			
	# Tell Softimage that the event has been consumed
	in_ctxt.SetAttribute("Consumed",Consumed)



def InitQPop_OnEvent (in_ctxt):
	Print ("QPop Startup event called",c.siVerbose)
	initQPopGlobals(True)
	
	#Load the QPop Config File
	QPopConfigFile = ""
	try:
		QPopConfigFile = App.Preferences.GetPreferenceValue("QPop.QPopConfigurationFile")
	except:
		Print("Could not retrieve QpopConfigFile from Preferences, must be first startup -> using Munchausen function to find it",c.siVerbose)
		QPopConfigFile = GetDefaultConfigFilePath()
		#Print("GetDefaultConfigFilePath returned: " + str(QPopConfigFile))
	if QPopConfigFile != "":
		Print("QPopConfigFile is: " + str(QPopConfigFile), c.siVerbose)
		try:
			Print("Attempting to load QPop Configuration from " + str(QPopConfigFile), c.siVerbose)
			result = QPopLoadConfiguration(QPopConfigFile)
			if result == True:
				Print("Loading QPop Configuration from " + str(QPopConfigFile) + " succeeded.", c.siVerbose)
		except:
			Print("Loading QPop Configuration from " + str(QPopConfigFile) + " failed!", c.siError)

	#Print("QPop First call!")
	#App.QPop()
	
def DestroyQPop_OnEvent (in_ctxt): 
	globalQPopConfigStatus = App.GetGlobal("globalQPopConfigStatus")
	if globalQPopConfigStatus.changed == True:
		Message = ("The QPop configuration has been changed - would you like to save it?")
		Caption = ("Save QPop Configuration?")
		DoSaveFile = XSIUIToolkit.MsgBox( Message, 36, Caption )
		if DoSaveFile == True:
			QPopConfigFile = App.Preferences.GetPreferenceValue("QPop.QPopConfigurationFile")
			Result = QPopSaveConfiguration(QPopConfigFile)
			if Result == False:  #Something went wrong
				Message = ("The QPop configuration file could not be written - would you like to save to the dafaule backup file?")
				Caption = ("Saving failed, save a QPop Configuration backup file?")
				#TODO: Add backup function that saves file to a default position in case the previous save attempt failed

	
	

#===================================== Custom Property Menu callbacks  ============================================================

def QPopConfigurator_Init( in_ctxt ):
    oMenu = in_ctxt.Source
    oMenu.AddCallbackItem("Edit QPop Menus","QPopConfiguratorMenuClicked")
    #oMenu.AddSeparatorItem()
    return true


def QPopConfiguratorMenuClicked( in_ctxt ):
    App.QPopConfiguratorCreate()
    return true



#===================================== Helper functions ============================================================

def GetView( Silent = False):
	CursorPos = win32gui.GetCursorPos()
	#Print ("Cursor Position is " + str(CursorPos))
	WinUnderMouse = win32gui.WindowFromPoint (CursorPos)
	WindowSignature = getDS_ChildName(WinUnderMouse)
	WindowSignatureString = str()
	for sig in WindowSignature:
		WindowSignatureString = (WindowSignatureString + sig + ";")
	if Silent != True:
		Print ("Picked Window has the following QPop View Signature: " + str(WindowSignatureString), c.siVerbose)
	return WindowSignatureString
def GetDefaultConfigFilePath():
	DefaultConfigFile = ""
	for plug in App.Plugins:
		if plug.Name == ("QPopConfigurator"):
			DefaultConfigFolder = (plug.OriginPath.rsplit("\\",3)[0] + "\\Data\\Preferences\\")#Get the left side of the path before "Data"
			DefaultConfigFile =  (DefaultConfigFolder + "QPopConfiguration_Default.xml")
			return DefaultConfigFile

def GetCustomGFXFilesPath():
	CustomGFXFolder = ""
	for plug in App.Plugins:
		if plug.Name == ("QPopConfigurator"):
			CustomGFXFolder = (plug.OriginPath.rsplit("\\",3)[0] + "\\Data\\Images\\")#Get the left side of the path before "Data"
			return CustomGFXFolder

def initQPopGlobals(force = False):
	Print("Qpop: initQPopGlobals called", c.siVerbose)
	if force == False:
		if App.GetGlobal ("globalQPopLastUsedItem") == None:
			App.SetGlobalObject ("globalQPopLastUsedItem", App.CreateQPop("LastUsedItem"))

		if App.GetGlobal ("globalQPopSeparators") == None:
			App.SetGlobalObject ("globalQPopSeparator",App.CreateQPop("Separators"))
			oGlobalSeparators = App.GetGlobal("globalQPopSeparators")
			oGlobalSeparators.addSeparator(App.CreateQPop("Separator"))
			
			
		if (App.GetGlobal ("globalQPopMenuItems") == None):
			App.SetGlobalObject ("globalQPopMenuItems", App.CreateQPop("MenuItems"))	

		if (App.GetGlobal ("globalQPopMenus") == None):
			App.SetGlobalObject ("globalQPopMenus", App.CreateQPop("Menus"))	

		if (App.GetGlobal ("globalQPopMenuSets") == None):
			App.SetGlobalObject ("globalQPopMenuSets", App.CreateQPop("MenuSets"))
			
		if (App.GetGlobal ("globalQPopMenuDisplayContexts") == None):
			App.SetGlobalObject ("globalQPopMenuDisplayContexts", App.CreateQPop("MenuDisplayContexts"))
			
		if (App.GetGlobal ("globalQPopViewSignatures") == None):
			App.SetGlobalObject ("globalQPopViewSignatures", App.CreateQPop("ViewSignatures"))
			
		if (App.GetGlobal ("globalQPopDisplayEvents") == None):
			App.SetGlobalObject ("globalQPopDisplayEvents", App.CreateQPop("DisplayEvents"))

		if (App.GetGlobal ("globalQPopConfigStatus") == None):
			App.SetGlobalObject ("globalQPopConfigStatus", App.CreateQPop("ConfigStatus"))
			
	
	if force == True:
		App.SetGlobalObject ("globalQPopLastUsedItem", App.CreateQPop("LastUsedItem"))
		
		App.SetGlobalObject ("globalQPopSeparators",App.CreateQPop("Separators"))
		oGlobalSeparators = App.GetGlobal("globalQPopSeparators")
		oGlobalSeparators.addSeparator(App.CreateQPop("Separator"))	
		
		App.SetGlobalObject ("globalQPopMenuItems", App.CreateQPop("MenuItems"))	
		App.SetGlobalObject ("globalQPopMenus", App.CreateQPop("Menus"))	
		App.SetGlobalObject ("globalQPopMenuSets", App.CreateQPop("MenuSets"))
		App.SetGlobalObject ("globalQPopMenuDisplayContexts", App.CreateQPop("MenuDisplayContexts"))
		App.SetGlobalObject ("globalQPopViewSignatures", App.CreateQPop("ViewSignatures"))
		App.SetGlobalObject ("globalQPopDisplayEvents", App.CreateQPop("DisplayEvents"))
		App.SetGlobalObject ("globalQPopConfigStatus", App.CreateQPop("ConfigStatus"))

def deleteQPopMenu(MenuName):
	if MenuName != "":
		globalQPopMenus = App.GetGlobal("globalQPopMenus")
		oMenuToDelete = getQPopMenuByName(MenuName)
		
		#Delete Menu from global QPop menus
		for oMenu in globalQPopMenus.items:
			if oMenu == oMenuToDelete:
				globalQPopMenus.deleteMenu(oMenu)
			
		
		#Delete Menu from global QPop menu Sets too (Python does not allow for global object destruction :-( )
		globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets").items
		for oMenuSet in globalQPopMenuSets:
			for oMenu in oMenuSet.AMenus:
				if oMenu == oMenuToDelete:
					try:
						MenuIndex = oMenuSet.AMenus.index(oMenu)
						oMenuSet.removeMenuAtIndex (MenuIndex,"A")
					except:
						DoNothin = True
			for oMenu in oMenuSet.BMenus:
				if oMenu == oMenuToDelete:
					try:
						MenuIndex = oMenuSet.BMenus.index(oMenu)
						oMenuSet.removeMenuAtIndex (MenuIndex,"B")
					except:
						DoNothin = True
			for oMenu in oMenuSet.CMenus:
				if oMenu == oMenuToDelete:
					try:
						MenuIndex = oMenuSet.AMenus.index(oMenu)
						oMenuSet.removeMenuAtIndex (MenuIndex, "C")
					except:
						DoNothin = True
			for oMenu in oMenuSet.DMenus:
				if oMenu == oMenuToDelete:
					try:
						MenuIndex = oMenuSet.AMenus.index(oMenu)
						oMenuSet.removeMenuAtIndex (MenuIndex, "D")
					except:
						DoNothin = True
						
		for oMenu in globalQPopMenus.items:
			for oItem in oMenu.items:
				if oItem == oMenuToDelete:
					oMenu.removeMenuItem(oMenuToDelete)
				
				
				

def deleteQPopMenuItem(MenuItemName):				
	Print ("Qpop: deleteQPopMenuItem called",c.siVerbose)

	globalQPopMenuItems = App.GetGlobal("globalQPopMenuItems")
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	
	for oMenuItem in globalQPopMenuItems.items:
		if oMenuItem.name == MenuItemName:
			globalQPopMenuItems.deleteMenuItem(oMenuItem)
	
	for oMenu in globalQPopMenus.items:
		for oMenuItem in oMenu.items:
			if oMenuItem.name == MenuItemName:
				oMenu.removeMenuItem (oMenuItem)

				
				
		
def ListToString(List):
	String = ""
	for i in range (0,len(List)):
		String += str(List[i])
		if i < (len(List)-1):
			String += ";"
	return String


def getDS_ChildName( hwnd):
	Signature = list()
	finished = False
	while finished == false:
		WindowTitle = win32gui.GetWindowText(hwnd)
		if WindowTitle.find ("SOFTIMAGE") == -1 and WindowTitle.find ("Softimage") == -1:  #Check if we haven'te clicked on or reached the top level window
			if WindowTitle != "":
				cleanWindowTitle = ""
				for char in WindowTitle:
					if not char.isdigit():
						if char != " ":
							cleanWindowTitle += char
				Signature.append (cleanWindowTitle)
			hwnd = win32gui.GetParent(hwnd)
		else:
			finished = True
	return Signature

def fGetSelection():
    sel = XSIFactory.CreateActiveXObject( "XSI.Collection" )
    for o in App.Selection:
        sel.Add(o)
    return sel

def fGetChildren (colObjects):
    colChildren = XSIFactory.CreateActiveXObject( "XSI.Collection" )
    for o in objs:
        for child in o.Children: colChildren.Add (child)
    fGetChildren (colChildren)
    return colChildren
        
def splitAlphaNum(name):
	name = str(name)
	namelength = (len(name))
	Counter = 1
	Continue = True
	finaldigipart = ""
	finalalphapart = ""

	while Continue  ==  True:
		digipart = name[(namelength - Counter):namelength]
		if digipart.isdigit() ==  True:
			alphapart = name[0:(namelength - (Counter))]
			#App.LogMessage("alphapart after slicing is: " + alphapart)
			#App.LogMessage("digipart after slicing is: " + digipart)
			Counter +=1
			newdigipart = name[(namelength - Counter):namelength]
			if newdigipart.isdigit() ==  False:
				finaldigipart = digipart
				finalalphapart = alphapart
				Continue = False
			else:
				Continue = True
		else:
			Continue = False
			finalalphapart = name
			finaldigipart = 0
			
	returnVal = list()
	returnVal.append(finalalphapart)
	returnVal.append(int(finaldigipart))
	return returnVal
			
def getUniqueName (name, listOfNames):
	listOfNames = list(listOfNames)
	uniqueName = name.replace(";","_")
	unique = False #Lets assume the name is not unique for now

	if len(listOfNames) > 0:
		while unique == False:
			foundit = False
			for i in range (0, len(listOfNames)):
				if listOfNames[i] == uniqueName:
					foundit = True
			if foundit == True:
				number =  (splitAlphaNum(uniqueName)[1])
				number = ((int(number))+1)
				namepart = splitAlphaNum(uniqueName)[0]
				uniqueName = (namepart + str(number))
				unique = False
			if foundit == False:
				unique = True
	else:
		Print ("Qpop: getUniqueName - Given list of names is empty!",c.siVerbose)
		unique = True
	if unique == True:
		return uniqueName

def getUniqueSpacedName (name, listOfNames):
	listOfNames = list(listOfNames)
	uniqueName = name.replace(";","_")
	unique = False #Lets assume the name is not unique for now

	if len(listOfNames) > 0:
		while unique == False:
			foundit = False
			for i in range (0, len(listOfNames)):
				if listOfNames[i] == uniqueName:
					foundit = True
			if foundit == True:
				uniqueName = uniqueName + " "
				unique = False
			if foundit == False:
				unique = True
	else:
		Print ("Qpop: getUniqueName - Given list of names is empty!",c.siVerbose)
		unique = True
	
	if unique == True:
		return uniqueName

		
		
def CollectHandles( handle , winList ):
	winList.append(handle)
	return True
 
   
def getXSITopLevelWindow():
	#Returns the handle to the XSI top-level window
	wins = []
	win32gui.EnumWindows(CollectHandles, wins) 
	currentId = os.getpid()
	for handle in wins:
		tid, pid = win32process.GetWindowThreadProcessId(handle)
		if pid == currentId:
			title = win32gui.GetWindowText(handle)
			if title.startswith('SOFTIMAGE') or title.startswith('Autodesk Softimage'):
				#Print("Softimage window found!")
				#win32gui.SetWindowText(handle,Windowtext)
				return handle
	return None	


def getQPopMenuByName (menuName):
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	for menu in globalQPopMenus.items:
		if menu.name == menuName:
			return menu
def getQPopMenuByUID (menuUID):
	globalQPopMenus = App.GetGlobal("globalQPopMenus")
	for menu in globalQPopMenus.items:
		if menu.UID == menuUID:
			return menu
def getQPopMenuSetByName (menuSetName):
	globalQPopMenuSets = App.GetGlobal("globalQPopMenuSets")
	for oMenuSet in globalQPopMenuSets.items:
		if oMenuSet.name == menuSetName:
			return oMenuSet
def getQPopMenuDisplayContextByName (menuDisplayContextName):
	globalQPopMenuDisplayContexts = App.GetGlobal("globalQPopMenuDisplayContexts")
	for oContext in globalQPopMenuDisplayContexts.items:
		if oContext.name == menuDisplayContextName:
			return oContext
			
def getQPopMenuItemByName (menuItemName):
	globalQPopMenus = App.GetGlobal("globalQPopMenuItems")
	for menuItem in globalQPopMenus.items:
		if menuItem.name == menuItemName:
			return menuItem

def getQPopSeparatorByName (separatorName):
	globalQPopSeparators = App.GetGlobal("globalQPopSeparators")
	for oItem in globalQPopSeparators.items:
		if oItem.name == separatorName:
			return oItem
			
			
def getQPopViewSignatureByName(signatureName):
	globalQPopViewSignatures = App.GetGlobal("globalQPopViewSignatures")	
	for oSignature in globalQPopViewSignatures.items:
		if oSignature.name == signatureName:
			return oSignature

def getCommandByUID(UID):
	for Cmd in App.Commands:
		if Cmd.UID == UID:
			#Print("Command matching UI is: " + (Cmd))
			return Cmd
	return None

#====================== Old and experimental Stuff ==============================