from eventFlow import *
from processorRDF import *


##########################################
# FLOW

flow = SampleProcessing("flowTest")

flow.loadFlowFromFile("flow_OpenData_CMS.json")




##########################################
# RDF processor


pRDF = Processor_RDF("pRDF", flow, "../test_data/OpenData_CMS-DA1BF301-762C-5048-A9EB-AB534069FB4B.root", "Events")

pRDF.RunProcessor()

