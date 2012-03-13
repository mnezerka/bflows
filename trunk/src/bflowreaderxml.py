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
import logging
from bflow import *		

class BFlowReaderXml:

	def __init__(self):
		# create instance of default style 
		self.__diagrams = [] 
		self.__styles = [] 
		self.__styleDefault = BFlowStyle('default')

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
		logger = logging.getLogger()
		logger.debug('readFile() ' + 'ENTER' + ' path: ' + path)

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

		logger.debug('readFile() ' + 'LEAVE')

		return self.__diagrams

						
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

		dia = BFlow(self, callflowElement.getAttribute("name"))
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

		result = BFlowObject(dia, el.getAttribute("id"), pos, el.getAttribute("name"))

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
				msgDesc += node.data
			elif node.tagName == "br":
				msgDesc += "\n"

		if el.tagName == "message":
			diaObj = BFlowMessage(dia, msgId, srcObj, dstObj, el.getAttribute("name"))
		elif el.tagName == "communication":
			diaObj = BFlowCommunication(dia, msgId, srcObj, dstObj, el.getAttribute("name"))
		elif el.tagName == "caption":
			diaObj = BFlowCaption(dia, msgId, srcObj, dstObj, el.getAttribute("name"))

		if el.hasAttribute("style"):
			diaObj.setStyle(el.getAttribute("style"))
					
		diaObj.setDesc(msgDesc)
		dia.addEvent(diaObj)

	def parseStyle(self, styleElement):

		if not styleElement.hasAttribute("name"):
			print "Warning: type must have name"
			return	

		style = BFlowStyle(styleElement.getAttribute("name"))
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

		result = BFlowGroup(dia, el.getAttribute("id"), el.getAttribute("name"))

		if el.hasAttribute("style"):
			result.setStyle(el.getAttribute("style"))
	
		return result 

	def parseParam(self, paramElement):
		if not paramElement.hasAttribute("name") or not paramElement.hasAttribute("value"):
			print "Warning: param must have both name and value"
			return	
		return (paramElement.getAttribute("name"), paramElement.getAttribute("value"))



