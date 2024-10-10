from eventFlow import *
from processorLoop import *
import ROOT


##########################################
# FLOW

flow = SampleProcessing("flowTest")

flow.loadFlowFromFile("flow_OpenData_CMS.json")



##########################################
# Plain Loop processor

pLoop = ProcessorLoop("pLoop", flow, "../test_data/OpenData_CMS-DA1BF301-762C-5048-A9EB-AB534069FB4B.root", "Events")

pLoop.Generate_Loop_cpp()

pLoop.Compile_cpp_file()

