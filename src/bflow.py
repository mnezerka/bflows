############################################################
# BFlows - Callflow Diagrams Generator 
#
# Copyright (c) 2010, michal.nezerka(at)gmail.com 
#
# Tool for generating sequence diagrams from XML source
#
############################################################

from xml.dom import minidom
import logging
		
class BFlowStyle:
	"""Class represents visual style that could be applied to various diagram items"""

	PARAM_OUTLINE_COLOR = 'outline-color' 
	PARAM_FILL_COLOR = 'fill-color' 
	PARAM_TEXT_COLOR = 'text-color' 
	
	def __init__(self, name):
		self.__params = {} 
		self.__name = name
		self.set(BFlowStyle.PARAM_OUTLINE_COLOR, "#000000")
		self.set(BFlowStyle.PARAM_FILL_COLOR, "#ffffff")
		self.set(BFlowStyle.PARAM_TEXT_COLOR, "#000000")

	def getName(self):
		return self.__name

	def set(self, key, value):
		self.__params[key] = value	

	def get(self, key):
		result = None
		
		if key in self.__params:
			result = self.__params[key]

		return result

class BFlowItem:
	"""Class represents abstract item for all items that can be placed to diagram"""
	def __init__(self, diagram, id, name):
		self.__diagram = diagram
		self.__id = id
		self.__name = name
		self.__desc = ""  
		# assign default style
		self.__style = diagram.getStyleByName(None)

	def getDiagram(self):
		return self.__diagram

	def getId(self):
		return self.__id

	def getName(self):
		return self.__name

	def getStyle(self):
		return self.__style

	def setStyle(self, styleName):
		self.__style = self.getDiagram().getStyleByName(styleName)

	def getDesc(self):
		return self.__desc

	def setDesc(self, text):
		self.__desc = text

	def getHeight(self):
		"""Get height of the item (in pixels)"""
		return 0


class BFlowObject(BFlowItem):
	"""Class represents one object (object-lifetime)."""

	def __init__(self, dia, id, pos, name):
		BFlowItem.__init__(self, dia, id, name)
		self.__pos = pos; 
		self.__drawPosY = 0

	def getPos(self):
		return self.__pos

	def getDrawPos(self):
		return self.__drawPosY

class BFlowGroup(BFlowItem):
	"""Class represents one group of objects"""
	def __init__(self, diagram, id, name):
		BFlowItem.__init__(self, diagram, id, name)
		self.__items = [] 

	def add(self, item):
		if not item is None:
			self.__items.append(item)

	def draw(self, draw):

		minPosObj = None
		maxPosObj = None	
		for obj in self.__items:
			if minPosObj is None or obj.getPos() < minPosObj.getPos():
				minPosObj = obj
			if maxPosObj is None or obj.getPos() > maxPosObj.getPos():
				maxPosObj = obj

		minPosX = self.getDiagram().getObjectX(minPosObj)
		maxPosX = self.getDiagram().getObjectX(maxPosObj)
		baseY = self.getDiagram().getParam(Dia.PARAM_OFFSET_Y)
		colWidth = self.getDiagram().getParam(Dia.PARAM_COL_WIDTH)
		recOffsetX = colWidth / 2 - 5

		# group shape 
		draw.rectangle(
			(minPosX - recOffsetX, baseY - 45 , maxPosX + recOffsetX, baseY - 25), 
			outline=self.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR),
			fill=self.getStyle().get(BFlowStyle.PARAM_FILL_COLOR))

		# group title
		textSize = draw.textsize(self.getName())
		middleX = minPosX + (maxPosX - minPosX) / 2
		textX = middleX - (textSize[0] / 2)
		textY = baseY - 45 +  textSize[1] / 2;  
		draw.text((textX, textY), self.getName(),
		fill=self.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR))


class BFlowMessage(BFlowItem):
	"""Message between two objects"""

	def __init__(self, diagram, id, objSrc, objDst, name):
		BFlowItem.__init__(self, diagram, id, name)
		self.__objSrc = objSrc
		self.__objDst = objDst
		self.objSrc = objSrc
		self.objDst = objDst


	def getSrc(self):
		return self.__objSrc

	def getDst(self):
		return self.__objDst

	def draw(self, draw):

		# get X coordinates of begin and end points
		srcX = self.getDiagram().getObjectX(self.__objSrc)
		dstX = self.getDiagram().getObjectX(self.__objDst)

		# get Y coordinate
		msgY = 0 
		l2r = srcX < dstX;

		# arrow
		arrowOffsetX = -10;
		if (not l2r):
			arrowOffsetX = 10;

		draw.line((srcX, msgY, dstX, msgY), fill=self.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR))
		draw.polygon(((dstX, msgY), (dstX + arrowOffsetX, msgY - 3), (dstX + arrowOffsetX, msgY + 3)), fill=self.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR))

		# title
		textSize = draw.textsize(self.getName())
		gapPos = (self.getDiagram().getColWidth() - textSize[0]) / 2;
		textX = srcX + gapPos; 
		if (not l2r):
			textX = textX - self.getDiagram().getColWidth()
		textY = msgY - textSize[1] - 2;
		draw.text((textX, textY), self.getName(), fill=self.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR))

		# description
		descSize = draw.textsize(self.getDesc())
		gapPos = (self.getDiagram().getColWidth() - descSize[0]) / 2;
		descX = srcX + gapPos; 
		if (not l2r):
			descX = descX - self.getDiagram().getColWidth()
		descY = msgY + 2;
		draw.text((descX, descY), self.getDesc(), fill=self.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR))

	def getHeight(self, draw):
		result = 0

		# get height of arrow (10 pixels)
		result += 10

		# get height of title
		textSize = draw.textsize(self.getName())
		result += textSize[1];
	
		# get height of description
		#textSize = draw.textsize(self.getDesc())
		#result += textSize[1];

		return result

class BFlow:
	"""Class represents set of diagrams and methods for output to various formats

	Time slot is a one specific moment in time. Its visual representation is a level
	in diagram - all objects at this level happen in same time. Events are usualy alligned to time
	slots - arrows are drawn horizontally.
	"""

	PARAM_OFFSET_X = "offsetx"
	PARAM_OFFSET_Y = "offsety"
	PARAM_COL_WIDTH = "colwidth"

	def __init__(self, parent, name):

		'''objects are instancies for '''
		self.__objects = []

		'''group is a collection of objects, drawn above the object titles (boxes)'''
		self.__groups = []

		'''event is some kind of relation between two objects (e.g. message)'''
		self.__events = []

		'''style is a definition of graphic representation'''
		self.__styles = [] 

		self.__timeSlotMax = 1
		self.__timeSlotHeight = 20
		self.__colWidth = 100

		'''page left offset'''
		self.__offsetX = 70

		'''page top offset'''
		self.__offsetY = 70

		'''name of the diagram'''
		self.__name = name 

		self.__parent = parent

		self.__styleDefault = None

		self.__height = None 

	def getParam(self, paramId):
		if paramId == self.PARAM_OFFSET_X:
			return self.__offsetX
		elif paramId == self.PARAM_OFFSET_Y:
			return self.__offsetY
		elif paramId == self.PARAM_COL_WIDTH:
			return self.__colWidth

		return None

	# find time slot for range of objects between objA and objB (both are included) 
	def getTimeSlotForRange(self, objA, objB):

		# default value is set according to range border objects
		result = max(objA.getTimeSlot(), objB.getTimeSlot())

		# get objects from range
		objSet = self.getObjectsFromRange(objA, objB) 

		# find maximal time slot
		for obj in objSet:
			if  obj.getTimeSlot() > result:
				result = obj.getTimeSlot()

		return result

	def getName(self):
		return self.__name

	def addObject(self, object):
		self.__objects.append(object);

	def getObjects(self):
		return self.__objects

	def addGroup(self, group):
		self.__groups.append(group);

	def addEvent(self, event):
		self.__events.append(event);

	def getEvents(self):
		return self.__events

	def addStyle(self, style):
		if style.getName() == "default":
			self.__styleDefault = style
		else:
			self.__styles.append(style);

	def getObjectsFromRange(self, objA, objB):
		result = []
		rangeL = min(objA.getPos(), objB.getPos())
		rangeR = max(objA.getPos(), objB.getPos())
		for obj in self.__objects:
			if obj.getPos() >= rangeL and obj.getPos() <= rangeR:
				result.append(obj)
		return result 

	def getLastPos(self):
		"""Finds last position in objects slots (columns)"""
		result = 0 
		for object in self.__objects:
			if object.getPos() > result:
				result = object.getPos()
		return result

	def getFreePos(self):
		"""Finds first free position in objects slots (columns)"""
		result = 0
		for object in self.__objects:
			if object.getPos() >= result:
				result = object.getPos() + 1
		return result

	def sync(self, objA = None, objB = None):

		if (not objA is None and not objB is None):
			objSet = self.getObjectsFromRange(objA, objB)
		else:
			objSet = self.__objects
		# TODO:	
			
	def getWidth(self):
		result = 2 * self.__offsetX  + (len(self.__objects) - 1) * self.__colWidth
		return result
			
	def getHeight(self):

		if self.__height is None:
			self.computeHeight()

		return self.__height

	def computeHeight(self):
		"""Get height of the diagram"""

		logger = logging.getLogger()
		logger.debug('BFlow(' + self.getName() + ')::computeHeight() ' + 'ENTER');

		# create empty small image just for measuring and calculations 
		# it should be of same type as final image
		imgTmp = Image.new("RGB", (1, 1), "#ffffff")
		drawTmp = ImageDraw.Draw(imgTmp)

		# top offset and bottom offset for nice ending at the top and bottom
		self.__height = self.__offsetY * 2

		# compute height of groups part
		#for group in self.__groups:
		#	group.draw(draw)

		# compute height of objects part
		# compute maximal height of object lifetimes
		for event in self.__events:
			logger.debug("event: %s, height: %d", event.getName(), event.getHeight(drawTmp))

		# include some empty time slots for nice ending at the bottom
		#result = self.__offsetY * 2 + (self.__timeSlotMax + 2) * self.__timeSlotHeight

		logger.debug('BFlow(' + self.getName() + ')::computeHeight() ' + 'LEAVE');

	def getColWidth(self):
		return self.__colWidth

	def getBaseLineY(self):
		result = self.__offsetY

		#for group in groups:
		#	group.getHeight()	

		return result 

	def getObjectX(self, obj):
		result = self.__offsetX + obj.getPos() * self.__colWidth
		return result

	def getObjectById(self, id):
		result = None;
		for obj in self.__objects:
			if obj.getId() == id:
				result = obj
				break;
		return result

	def getFont(self):
		#return ImageFont.truetype("arial.ttf", 14)
		return ImageFont.load_default()

	def getStyleByName(self, styleName):
		result = None
		
		# first, try to find style in diagram
		for style in self.__styles:
			if styleName == style.getName():
				result = style 

		# second check if there is a default style for this diagram
		if result is None and not self.__styleDefault is None:
			result = self.__styleDefault

		# if not found in diagram, try it in data source (parent object)
		if result is None:
			result = self.__parent.getStyleByName(styleName)

		return result

	def getGroupById(self, groupId):
		result = None
	
		for group in self.__groups:
			if groupId == group.getId():
				result = group 

		return result

	def gen(self):

		logger = logging.getLogger()
		logger.debug('BFlow(' + self.getName() + ')::generate() ' + 'ENTER');


		logger.debug('Creating canvas of size: %dx%d', self.getWidth(), self.getHeight())

		# create empty image
		img = Image.new("RGB", (self.getWidth(), self.getHeight()), "#ffffff")

		draw = ImageDraw.Draw(img)

		print "Generating Diagram", self.getName()

		# draw node lifetimes
		lastGroupId = None
		lastGroupX = None
		lastGroup = None
		for obj in self.__objects:

			objX = self.getObjectX(obj)

			# lifetime line
			draw.line((objX, self.__offsetY, objX, self.getHeight() - self.__offsetY), fill="#000000")

			# rectangle
			recOffset = self.getColWidth() / 2 - 5
			draw.rectangle(
				(objX - recOffset, self.__offsetY, objX + recOffset, self.__offsetY - 20),
				outline=obj.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR),
				fill=obj.getStyle().get(BFlowStyle.PARAM_FILL_COLOR))

			# title
			textSize = draw.textsize(obj.getName())
			textX = objX - (textSize[0] / 2)
			textY = self.__offsetY  - textSize[1] - 5;  
			draw.text((textX, textY), obj.getName(),
				fill=obj.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR), font=self.getFont())


		# draw calls 
		for event in self.__events:
			event.draw(draw)

		# draw groups 
		for group in self.__groups:
			group.draw(draw)

		del draw 

		img.save(self.getName() + ".png", "PNG")

		logger.debug('BFlow::generate() ' + 'LEAVE')

class BFlowWriter:

	def generate(self):	
		print "Empty"

