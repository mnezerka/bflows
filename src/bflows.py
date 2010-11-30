############################################################
# BFlows - Callflow Diagrams Generator 
#
# Copyright (c) 2010, michal.nezerka(at)gmail.com 
#
# Tool for generating sequence diagrams from XML source
#
############################################################

from xml.dom import minidom
import sys
import Image
import ImageDraw
import ImageFont
		
class DiaDataSource:

	def __init__(self):
		# create instance of default style 
		self.__diagrams = [] 
		self.__styles = [] 
		self.__styleDefault = DiaStyle('default')

	def addStyle(self, style):
		if style.getName() == "default":
			self.__styleDefault = style
		else:
			self.__styles.append(style);

	def getStyleByName(self, styleName):

		result = self.__styleDefault 
		
		# look for type in local list of types
		for style in self.__styles:
			if styleName == style.getName():
				result = style 
		return result

	def readFile(self, path):
		try:
			xmldoc = minidom.parse(path)
		except Exception: #as inst:
			print "Error: processing file failed:", path
			#print inst
			return

		print "Reading file", path
		# we are interested in bflow sections
		bflows = xmldoc.getElementsByTagName("bflow")
		for bflow in bflows:
			self.parse(bflow)

		return

						
	def parse(self, xmlDoc):

		for el in xmlDoc.childNodes:

			if not el.nodeType == el.ELEMENT_NODE:
				continue

			# callflow type
			if el.tagName == "callflow":
				self.parseCallflow(el)
			
			# style 
			elif el.tagName == "style":
				style = self.parseStyle(el)
				self.addStyle(style)

			# parameter 
			elif el.tagName == "param":
				self.parseParam(el)
	
			else:
				print el.tagName


	def parseCallflow(self, callflowElement):

		if not callflowElement.hasAttribute("name"):
			print "missing callflow name"
			return	

		dia = Dia(self, callflowElement.getAttribute("name"))
		self.__diagrams.append(dia)

		for el in callflowElement.childNodes:

			# we are interested only in element nodes 
			if not el.nodeType == el.ELEMENT_NODE:
				continue	

			#read objects 
			if el.tagName == "object":
		
				object = self.parseObject(dia, el)
				if not object is None:
					dia.addObject(object)

			#read groups 
			elif el.tagName == "group":
				group = self.parseGroup(dia, el)
				if not group is None:
					dia.addGroup(group)

			#read messages 
			elif el.tagName == "message" or el.tagName == "communication" or el.tagName == "caption":

				msg = self.parseMessage(dia, el)
				if not msg is None:
					dia.addEvent(msg)

			#read sync 
			elif el.tagName == "sync":

				if not el.hasAttribute("src") or not el.hasAttribute("dst"):
					
					dia.sync()
				else:

					srcObj = dia.getObjectById(el.getAttribute("src"))
					if srcObj is None:
						print "Warning: sync source object not found"
						continue

					dstObj = dia.getObjectById(el.getAttribute("dst"))
					if srcObj is None:
						print "Warning: sync destination object not found"
						continue

					dia.sync(srcObj, dstObj)

			#read style 
			elif el.tagName == "style":
				if not el.hasAttribute("name"):
					print "Warning: style must have name"
					continue

				style = self.parseStyle(el)
				dia.addStyle(style)

			# else skip unknown elements

	def parseObject(self, dia, el):

		result = None

		if not el.hasAttribute("id") or not el.hasAttribute("name"):
			print "Warning: missing object id or name" 
			return result	

		if el.hasAttribute("pos"):
			pos = el.getAttribute("pos")
		else:
			pos = dia.getFreePos()

		result = DiaObject(dia, el.getAttribute("id"), pos, el.getAttribute("name"))

		if el.hasAttribute("group"):
			group = dia.getGroupById(el.getAttribute("group"))
			if not group is None:
				group.add(result)

		if el.hasAttribute("style"):
			result.setStyle(el.getAttribute("style"))
		
		return result 

	def parseMessage(self, dia, el):
		msgId = "n/a" 
		msgName = "n/a" 
		msgDesc = ""
		result = None 

		if not el.hasAttribute("src") or not el.hasAttribute("dst") or not el.hasAttribute("name"):
			print "Warning: missing messsage src, dst or name(element:", el.tagName, ")"
			return result	

		if el.hasAttribute("id"):
			msgId = el.getAttribute("id")		

		srcObj = dia.getObjectById(el.getAttribute("src"))
		if srcObj is  None:
			print "Warning: source object not found"
			return result

		dstObj = dia.getObjectById(el.getAttribute("dst"))
		if srcObj is None:
			print "Warning: destination object not found"
			return result

		for node in el.childNodes:
			if node.nodeType == node.TEXT_NODE:
				msgDesc = node.data

		if el.tagName == "message":
			diaObj = DiaMessage(dia, msgId, srcObj, dstObj, el.getAttribute("name"))
		elif el.tagName == "communication":
			diaObj = DiaCommunication(dia, msgId, srcObj, dstObj, el.getAttribute("name"))
		elif el.tagName == "caption":
			diaObj = DiaCaption(dia, msgId, srcObj, dstObj, el.getAttribute("name"))

		if el.hasAttribute("style"):
			diaObj.setStyle(el.getAttribute("style"))
					
		diaObj.setDesc(msgDesc)
		dia.addEvent(diaObj)

	def parseStyle(self, styleElement):

		if not styleElement.hasAttribute("name"):
			print "Warning: type must have name"
			return	

		style = DiaStyle(styleElement.getAttribute("name"))
		params = styleElement.getElementsByTagName("param")
		for param in params:
			paramData = self.parseParam(param)
			style.set(paramData[0], paramData[1])

		return style 

	def parseGroup(self, dia, el):

		result = None
		if not el.hasAttribute("id") or not el.hasAttribute("name"):
			print "Warning: missing group id or name" 
			return result

		result = DiaGroup(dia, el.getAttribute("id"), el.getAttribute("name"))

		if el.hasAttribute("style"):
			result.setStyle(el.getAttribute("style"))
	
		return result 

	def parseParam(self, paramElement):
		if not paramElement.hasAttribute("name") or not paramElement.hasAttribute("value"):
			print "Warning: param must have both name and value"
			return	
		return (paramElement.getAttribute("name"), paramElement.getAttribute("value"))

			
	def generate(self):
		for dia in self.__diagrams:
			dia.gen()
class DiaStyle:
	"""Class represents visual style that could be applied to various diagram items"""

	PARAM_OUTLINE_COLOR = 'outline-color' 
	PARAM_FILL_COLOR = 'fill-color' 
	PARAM_TEXT_COLOR = 'text-color' 
	
	def __init__(self, name):
		self.__params = {} 
		self.__name = name
		self.set(DiaStyle.PARAM_OUTLINE_COLOR, "#000000")
		self.set(DiaStyle.PARAM_FILL_COLOR, "#ffffff")
		self.set(DiaStyle.PARAM_TEXT_COLOR, "#000000")

	def getName(self):
		return self.__name

	def set(self, key, value):
		self.__params[key] = value	

	def get(self, key):
		result = None
		
		if key in self.__params:
			result = self.__params[key]

		return result

class DiaItem:
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



class DiaObject(DiaItem):
	"""Class represents one object/object-lifetime."""

	def __init__(self, dia, id, pos, name):
		DiaItem.__init__(self, dia, id, name)
		self.__pos = pos; 
		self.__timeSlotFree = 1

	def getPos(self):
		return self.__pos

	def getTimeSlot(self):
		return self.__timeSlotFree

	def setTimeSlot(self, val):
		self.__timeSlotFree = val

	def occupyTimeSlot(self, ix, size = 1):
		self.__timeSlotFree = ix + size 

class DiaGroup(DiaItem):
	"""Class represents one group of objects"""
	def __init__(self, diagram, id, name):
		DiaItem.__init__(self, diagram, id, name)
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
			outline=self.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR),
			fill=self.getStyle().get(DiaStyle.PARAM_FILL_COLOR))

		# group title
		textSize = draw.textsize(self.getName())
		middleX = minPosX + (maxPosX - minPosX) / 2
		textX = middleX - (textSize[0] / 2)
		textY = baseY - 45 +  textSize[1] / 2;  
		draw.text((textX, textY), self.getName(),
		fill=self.getStyle().get(DiaStyle.PARAM_TEXT_COLOR))


		
# abstract class for all events
class DiaEvent(DiaItem):

	def __init__(self, diagram, id, name):
		DiaItem.__init__(self, diagram, id, name)
		self.__timeSlot = -1

	def getTimeSlot(self):
		return self.__timeSlot

	def setTimeSlot(self, val):
		self.__timeSlot = val

	def getTimeSlotRequiredSize(self):
		return 1

	def draw(self, draw):
		return "ok"		


# concrete event: message 
class DiaMessage(DiaEvent):

	def __init__(self, diagram, id, objSrc, objDst, name):
		DiaEvent.__init__(self, diagram, id, name)
		self.__objSrc = objSrc
		self.__objDst = objDst

		# compute time slot for this new event
		self.setTimeSlot(self.getDiagram().getTimeSlotForRange(objSrc, objDst))

		#self.setTimeSlot(max(self.__objSrc.getTimeSlot(), self.__objDst.getTimeSlot()))
		self.__objSrc.occupyTimeSlot(self.getTimeSlot(), self.getTimeSlotRequiredSize())
		self.__objDst.occupyTimeSlot(self.getTimeSlot(), self.getTimeSlotRequiredSize())

	def getSrc(self):
		return self.__objSrc

	def getDst(self):
		return self.__objDst

	def draw(self, draw):

		srcX = self.getDiagram().getObjectX(self.__objSrc)
		dstX = self.getDiagram().getObjectX(self.__objDst)
		msgY = self.getDiagram().getTimeSlotY(self.getTimeSlot())
		l2r = srcX < dstX;

		# arrow
		arrowOffsetX = -10;
		if (not l2r):
			arrowOffsetX = 10;

		draw.line((srcX, msgY, dstX, msgY), fill=self.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR))
		draw.polygon(((dstX, msgY), (dstX + arrowOffsetX, msgY - 3), (dstX + arrowOffsetX, msgY + 3)), fill=self.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR))

		# title
		textSize = draw.textsize(self.getName())
		gapPos = (self.getDiagram().getColWidth() - textSize[0]) / 2;
		textX = srcX + gapPos; 
		if (not l2r):
			textX = textX - self.getDiagram().getColWidth()
		textY = msgY - textSize[1] - 2;
		draw.text((textX, textY), self.getName(), fill=self.getStyle().get(DiaStyle.PARAM_TEXT_COLOR))

		# description
		descSize = draw.textsize(self.getDesc())
		gapPos = (self.getDiagram().getColWidth() - descSize[0]) / 2;
		descX = srcX + gapPos; 
		if (not l2r):
			descX = descX - self.getDiagram().getColWidth()
		descY = msgY + 2;
		draw.text((descX, descY), self.getDesc(), fill=self.getStyle().get(DiaStyle.PARAM_TEXT_COLOR))


class DiaCommunication(DiaMessage):

	def getTimeSlotRequiredSize(self):
		return 3

	def draw(self, draw):

		srcX = self.getDiagram().getObjectX(self.getSrc())
		dstX = self.getDiagram().getObjectX(self.getDst())
		baseY = self.getDiagram().getTimeSlotY(self.getTimeSlot() + 1)
		l2r = srcX < dstX;

		# arrow
		arrowOffsetX = -10;
		if (not l2r):
			arrowOffsetX = 10;

		draw.polygon(
			(
				(srcX, baseY),
				(srcX - arrowOffsetX, baseY - 16),
				(srcX - arrowOffsetX, baseY - 8),
				(dstX + arrowOffsetX, baseY - 8),
				(dstX + arrowOffsetX, baseY - 16),
				(dstX, baseY),
				(dstX + arrowOffsetX, baseY + 16),
				(dstX + arrowOffsetX, baseY + 8),
				(srcX - arrowOffsetX, baseY + 8),
				(srcX - arrowOffsetX, baseY + 16),
				(srcX, baseY)),
				outline=self.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR),
				fill=self.getStyle().get(DiaStyle.PARAM_FILL_COLOR))

		# title
		textSize = draw.textsize(self.getName())
		gapPos = abs(srcX - dstX) / 2 - textSize[0] / 2
		textX = srcX + gapPos; 
		if (not l2r):
			textX = dstX + gapPos

		textY = baseY - textSize[1] / 2;
		draw.text((textX, textY), self.getName(), fill=self.getStyle().get(DiaStyle.PARAM_TEXT_COLOR))

# concrete event: message 
class DiaCaption(DiaMessage):

	def getTimeSlotRequiredSize(self):

		# size depends on placement, top captions don't need so much space 
		result = 3
		return result 

	def draw(self, draw):
		srcX = self.getDiagram().getObjectX(self.getSrc())
		dstX = self.getDiagram().getObjectX(self.getDst())
		# position depends on placement, top captions don't need so much space 
		offsetY = 1 
		baseY = self.getDiagram().getTimeSlotY(self.getTimeSlot() + offsetY)
		l2r = srcX < dstX;

		# rectangle
		recOffsetX = 10;
		if (not l2r):
			recOffsetX = - 10;

		draw.rectangle(
			(srcX - recOffsetX, baseY - 10, dstX + recOffsetX, baseY + 10), 
			outline=self.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR),
			fill=self.getStyle().get(DiaStyle.PARAM_FILL_COLOR))

		# title
		textSize = draw.textsize(self.getName())
		gapPos = abs(srcX - dstX) / 2 - textSize[0] / 2
		textX = srcX + gapPos; 
		if (not l2r):
			textX = dstX + gapPos
		textY = baseY - (textSize[1] / 2);
		draw.text(
			(textX, textY),
			self.getName(),
			fill=self.getStyle().get(DiaStyle.PARAM_TEXT_COLOR),
			font=self.getDiagram().getFont())

class Dia:
	"""Class represents set of diagrams and methods for output to various formats"""

	PARAM_OFFSET_X = "offsetx"
	PARAM_OFFSET_Y = "offsety"
	PARAM_COL_WIDTH = "colwidth"

	def __init__(self, parent, name):
		self.__objects = []
		self.__groups = []
		self.__events = []
		self.__styles = [] 
		self.__timeSlotMax = 1
		self.__timeSlotHeight = 20
		self.__colWidth = 100
		self.__offsetX = 70
		self.__offsetY = 70
		self.__name = name 
		self.__parent = parent
		self.__styleDefault = None

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

	def addGroup(self, group):
		self.__groups.append(group);

	def addEvent(self, event):
		self.__timeSlotMax = max(self.__timeSlotMax, event.getTimeSlot())
		self.__events.append(event);

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

		# find maximal timeslot for all objects in range
		ts = -1 
		for obj in objSet:
			if obj.getTimeSlot() > ts:
				ts = obj.getTimeSlot()
		# synchronize timeslot of all objects in range
		for obj in objSet:
			obj.setTimeSlot(ts)
			
	def getWidth(self):
		result = 2 * self.__offsetX  + (len(self.__objects) - 1) * self.__colWidth
		return result
			
	def getHeight(self):
		# include some empty time slots for nice ending at the bottom
		result = self.__offsetY * 2 + (self.__timeSlotMax + 2) * self.__timeSlotHeight
		return result

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

	def getTimeSlotY(self, id):
		result = self.__offsetY + id * self.__timeSlotHeight
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
				outline=obj.getStyle().get(DiaStyle.PARAM_OUTLINE_COLOR),
				fill=obj.getStyle().get(DiaStyle.PARAM_FILL_COLOR))

			# title
			textSize = draw.textsize(obj.getName())
			textX = objX - (textSize[0] / 2)
			textY = self.__offsetY  - textSize[1] - 5;  
			draw.text((textX, textY), obj.getName(),
				fill=obj.getStyle().get(DiaStyle.PARAM_TEXT_COLOR), font=self.getFont())


		# draw calls 
		for event in self.__events:
			event.draw(draw)

		# draw groups 
		for group in self.__groups:
			group.draw(draw)

		del draw 

		img.save(self.getName() + ".png", "PNG")

############# MAIN #########################


# check arguments
if (len(sys.argv) < 2):
	print "Usage", sys.argv[0], "xmlfile1 [xmlfile2, ...]"
	exit(1)

# create instance of diagram data source
ds = DiaDataSource()

# process all files specified as parameters on command line
for xmlFileName in sys.argv[1:]:
	ds.readFile(xmlFileName)

# generate all diagrams
ds.generate()

