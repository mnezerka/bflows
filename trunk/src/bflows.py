############################################################
# BFlows - Callflow Diagrams Generator 
#
# Copyright (c) 2010, michal.nezerka(at)gmail.com 
#
# Tool for generating sequence diagrams from XML source
#
############################################################

import sys
import logging
import bflowreaderxml
import bflowrasterizer

# configure logging
logging.basicConfig(level=logging.DEBUG, filename=sys.argv[0] + '.log', filemode="w")
logger = logging.getLogger()
logger.debug('start')

# check arguments
if (len(sys.argv) < 2):
	print "Usage", sys.argv[0], "xmlfile1 [xmlfile2, ...]"
	exit(1)

# process all files specified as parameters on command line
for xmlFileName in sys.argv[1:]:
	bFlowDS = bflowreaderxml.BFlowReaderXml()
	bFlows = bFlowDS.readFile(xmlFileName)

	for bFlow in bFlows:
		bFlowRasterizer = bflowrasterizer.BFlowRasterizer(bFlow)
		bFlowRasterizer.generate()

logger.debug('end')

