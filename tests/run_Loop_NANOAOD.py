from eventFlow import *
from processorLoop import *


##########################################
# FLOW

flow = SampleProcessing("flowTest")

flow.loadFlowFromFile("flow_OpenData_CMS.json")




##########################################
# RDF processor


pLoop = ProcessorLoop("pLoop", flow, "../test_data/OpenData_CMS-DA1BF301-762C-5048-A9EB-AB534069FB4B.root", "Events")

pLoop.RunProcessor()

