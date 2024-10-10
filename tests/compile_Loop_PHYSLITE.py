from eventFlow import *
from processorLoop import *
import ROOT


##########################################
# FLOW

flow = SampleProcessing("flowTest")

flow.loadFlowFromFile("flow_OpenData_ATLAS.json")



##########################################
# Plain Loop processor

pLoop = ProcessorLoop("pLoop", flow, "../test_data/OpenData_ATLAS-DAOD_PHYSLITE.37621409._000041.pool.root.1", "CollectionTree")

pLoop.Generate_Loop_cpp()

pLoop.Compile_cpp_file()

