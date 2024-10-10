from eventFlow import *
from processorRDF import *


##########################################
# FLOW

flow = SampleProcessing("flowTest")

flow.loadFlowFromFile("flow_OpenData_ATLAS.json")



##########################################
# RDF processor


pRDF = Processor_RDF("pRDF", flow, "../test_data/OpenData_ATLAS-DAOD_PHYSLITE.37621409._000041.pool.root.1", "CollectionTree")

pRDF.RunProcessor()

