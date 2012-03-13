############################################################
# BFlows - Callflow Diagrams Generator 
#
# Copyright (c) 2010, michal.nezerka(at)gmail.com 
#
# Tool for generating sequence diagrams from XML source
#
############################################################

import sys
import Image
import ImageDraw
import ImageFont
import logging
from bflow import *

class BFlowRasterObjectLifetime:
	"""Represents one object lifetime shape"""

	def __init__(self, obj, rasterizer):
		self.object = obj
		self.posLabels = 0
		self.rasterizer = rasterizer
		self.posLifeTime = rasterizer.paramVSkip 

	def draw(self, draw):

		offsetX = self.rasterizer.paramOffsetX
		offsetY = self.rasterizer.paramOffsetY
		colWidth = self.rasterizer.paramColWidth

		posX = self.getPosX()

		# lifetime line
		draw.line((posX, offsetY, posX, self.rasterizer.imgHeight - self.rasterizer.paramOffsetY), fill="#000000")

		# rectangle
		recOffset = colWidth / 2 - 5
		draw.rectangle(
			(posX - recOffset, offsetY, posX + recOffset, offsetY - 20),
			outline=self.object.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR),
			fill=self.object.getStyle().get(BFlowStyle.PARAM_FILL_COLOR))

		# title
		textSize = draw.textsize(self.object.getName())
		textX = posX - (textSize[0] / 2)
		textY = offsetY  - textSize[1] - 5;
		draw.text((textX, textY), self.object.getName(), fill=self.object.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR), font=self.rasterizer.getFont())

	def getPosX(self):
		return self.rasterizer.paramOffsetX + self.object.getPos() * self.rasterizer.paramColWidth

class BFlowRasterEvent:

	"""Represents graphical representation of one event"""
	def __init__(self, obj, rasterizer):
		logger = logging.getLogger()

		self.object = obj
		self.rasterizer = rasterizer
		# source and target object lifetime
		self.objSrc = rasterizer.getRasterObjectLifetime(obj.objSrc)
		self.objDst = rasterizer.getRasterObjectLifetime(obj.objDst)
		# get direction
		self.l2r = self.objSrc.getPosX() < self.objDst.getPosX();
		self.height = 0
		# get Y coordinate
		self.posY = rasterizer.paramOffsetY + max(self.objSrc.posLifeTime, self.objDst.posLifeTime)
		# position of text
		if len(obj.getName()) > 0:
			textSize = rasterizer.getTextSize(obj.getName())
			gapPos = (rasterizer.paramColWidth - textSize[0]) / 2;
			self.textX = self.objSrc.getPosX() + gapPos; 
			if (not self.l2r):
				self.textX = self.textX - rasterizer.paramColWidth
			self.textY = self.posY;
			self.height += textSize[1] + 2
		else:
			self.textY = 0
		# arrow below text position
		self.arrowY = self.posY + self.height + 2;
		# pixels for arrow
		self.height += 4
		# position of description (bellow arrow) 
		if len(obj.getDesc()) > 0:
			descSize = rasterizer.getTextSize(obj.getDesc())
			gapPos = (rasterizer.paramColWidth - descSize[0]) / 2;
			self.descX = self.objSrc.getPosX() + gapPos; 
			if (not self.l2r):
				self.descX = self.descX - rasterizer.paramColWidth
			self.descY = self.posY + self.height;
			self.height += descSize[1]
		else:
			self.descY = 0
		self.objSrc.posLifeTime = self.objDst.posLifeTime = max(self.objSrc.posLifeTime, self.objDst.posLifeTime) + self.height + self.rasterizer.paramVSkip

		logger.debug('BFlowRasterEvent::init() created new raster event instance for event: %s' % obj.getName())
		logger.debug('BFlowRasterEvent::init()   posY (name, arrow, desc): (%d, %d, %d)' % (self.textY, self.arrowY, self.descY))

	def getPosX(self):
		return self.posX 

	def getPosY(self):
		return self.posY
		 
	def getHeight(self):
		return self.height

	def draw(self, draw):

		# text above arrow
		if len(self.object.getName()) > 0:
			draw.text((self.textX, self.textY), self.object.getName(), fill=self.object.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR))

		# arrow
		arrowOffsetX = -10;
		if (not self.l2r):
			arrowOffsetX = 10;
		draw.line(
			(self.objSrc.getPosX(), self.arrowY, self.objDst.getPosX(), self.arrowY),
			fill=self.object.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR))
		draw.polygon((
			(self.objDst.getPosX(), self.arrowY),
			(self.objDst.getPosX() + arrowOffsetX, self.arrowY - 3),
			(self.objDst.getPosX() + arrowOffsetX, self.arrowY + 3)),
			fill=self.object.getStyle().get(BFlowStyle.PARAM_OUTLINE_COLOR))

		# description bellow arrow
		if len(self.object.getDesc()) > 0:
			draw.text((self.descX, self.descY), self.object.getDesc(), fill=self.object.getStyle().get(BFlowStyle.PARAM_TEXT_COLOR))

class BFlowRasterizer(BFlowWriter):
	"""Class for drawing BFlow to bitmap""" 

	paramVSkip = 5
	paramOffsetX = 70
	paramOffsetY = 40
	paramColWidth = 100

	def __init__(self, bFlow):

		self.__bFlow = bFlow; 
		self.__objects = []
		self.__events = []

		self.__imgTest = Image.new("RGB", (10, 10), "#ffffff")
		self.__drawTest = ImageDraw.Draw(self.__imgTest)

	def getTextSize(self, str):
		return self.__drawTest.textsize(str)
		

	def generate(self):
		logger = logging.getLogger()
		logger.debug('BFlowRasterizer::generate() ' + 'ENTER, diagram: %s', self.__bFlow.getName());

		bflow = self.__bFlow

		print "Generating Diagram", self.__bFlow.getName()

		objs = bflow.getObjects()

		logger.debug('BFlowRasterizer::generate() ' + 'Computing image width');

		self.imgWidth = self.paramOffsetX
		self.imgHeight = self.paramOffsetY

		# prepare set of object lifetimes
		for o in objs:
			x = BFlowRasterObjectLifetime(o, self)
			self.__objects.append(x)
			if x.getPosX() > self.imgWidth:
				self.imgWidth = x.getPosX();
		self.imgWidth += self.paramOffsetX

		# prepare set of events
		for e in bflow.getEvents():
			x = BFlowRasterEvent(e, self)
			self.__events.append(x)
			if x.getPosY() > self.imgHeight:
				self.imgHeight = x.getPosY();
		self.imgHeight += 2 * self.paramOffsetY

		# create image canvas and draw all objects
		logger.debug('Creating canvas of size: %dx%d', self.imgWidth, self.imgHeight)
		img = Image.new("RGB", (self.imgWidth, self.imgHeight), "#ffffff")
		draw = ImageDraw.Draw(img)

		# draw and store objects
		for o in self.__objects:
			o.draw(draw)

		# draw events
		for e in self.__events:
			e.draw(draw)	
			
		del draw 

		img.save(self.__bFlow.getName() + ".png", "PNG")

		logger.debug('BFlowRasterizer::generate() ' + 'LEAVE')

	def getRasterObjectLifetime(self, obj):
		result = None
		for o in self.__objects:
			if o.object == obj:
				result = o
				break
		return result

	def getFont(self):
		#return ImageFont.truetype("arial.ttf", 14)
		return ImageFont.load_default()



