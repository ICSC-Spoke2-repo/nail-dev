from eventFlow import *
from processorRDF import *


print("[test] start")

flow = SampleProcessing("flowTest", 'dictionaries/nanoAOD_db.json')


flow.DefineEventWeight("Weight_normalisation",   "1.0f")
flow.DefineEventWeight("Weight_base_1",          "1.0f")

flow.Define("Muon_m",   "0*Muon_pfRelIso04_all+0.1056f")
flow.Define("Muon_p4",  "vector_map_t<ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> > >(Muon_pt , Muon_eta, Muon_phi, Muon_m)")
flow.Define("Muon_iso", "Muon_pfRelIso04_all")


flow.SubCollection("SelectedMuon", "Muon", sel="Muon_iso < 0.25 && Muon_tightId && Muon_pt > 20. && abs(Muon_eta) < 2.4")

#flow.DefineEventWeight("Weight_Mu_selection_eff", "0.95f", requires=["twoOppositeSignMuons"])

flow.DefineHisto1D("nSelectedMuon", [], 10, 0, 10)



flow.Selection("twoSelectedMuons", "nSelectedMuon==2")

flow.DefineEventWeight("Weight_Mu_selection_eff", "0.95f", requires=["twoSelectedMuons"])



flow.Distinct("MuMu", "SelectedMuon", requires=["twoSelectedMuons"])

flow.Define("OppositeSignMuMu", "Nonzero(MuMu0_charge != MuMu1_charge)", requires=["twoSelectedMuons"])


flow.Selection("twoOppositeSignMuons", "OppositeSignMuMu.size() > 0")

flow.TakePair("Mu", "SelectedMuon", "MuMu", "At(OppositeSignMuMu,0,-200)", requires=["twoOppositeSignMuons"])


flow.Define("Dimuon_p4", "Mu0_p4+Mu1_p4")
flow.Define("Dimuon_m", "Dimuon_p4.M()")



flow.Define("indices_SelectedMuon_pt_sorted", "Argsort(-SelectedMuon_pt)", requires=["twoOppositeSignMuons"])

flow.ObjectAt("LeadMuon", "SelectedMuon", "indices_SelectedMuon_pt_sorted[0]")
flow.ObjectAt("SubMuon",  "SelectedMuon", "indices_SelectedMuon_pt_sorted[1]")


flow.Selection("etaLeadMuonPos", "LeadMuon_eta > 0.0")
flow.Selection("etaLeadMuonNeg", "LeadMuon_eta <= 0.0")


flow.DefineHisto1D("Dimuon_m", ["twoOppositeSignMuons"], 100, 50.0, 150.0)


flow.DefineHisto1D("LeadMuon_pt",  ['etaLeadMuonPos'], 100, 0.0, 1000.0)
flow.DefineHisto1D("LeadMuon_pt",  ['etaLeadMuonNeg'], 100, 0.0, 1000.0)

flow.DefineHisto1D("LeadMuon_eta", ['etaLeadMuonPos'], 100, -5.0, 5.0)
flow.DefineHisto1D("LeadMuon_eta", ['etaLeadMuonNeg'], 100, -5.0, 5.0)



### NOTE: with the latest format for H1D definition, the target name for histos MUST include "__region" (if a region has been specified) - i.e. the DAG node has "__region_ in the name ... obviously! 
flow.BuildFlow()

targetList = ["HISTO_nSelectedMuon",
              "HISTO_Dimuon_m__twoOppositeSignMuons",
              "HISTO_LeadMuon_pt__etaLeadMuonPos",
              "HISTO_LeadMuon_pt__etaLeadMuonNeg",
              "HISTO_LeadMuon_eta__etaLeadMuonPos",
              "HISTO_LeadMuon_eta__etaLeadMuonNeg"]

flow.SetTargets(targetList)





print("\n -> Region for node --------------------------------------------------- \n")

for node in flow.AG.views:

    node_region = flow.region_id_for_node(node)
    rreq        = flow.AG.ranked_requirements_for_node(node)
    print(f"{node :<50}{node_region :<34}{rreq}")


print("\n -> Print Analysis graph FULL --------------------------------------------------- \n")

flow.AG.print_graph()


print("\n -> Print Analysis graph for TARGETS --------------------------------------------------- \n")

print(" Target list = ", targetList)

g1 = flow.GetGraphForTargets(targetList)

g1.print_graph()
g1.newDotFile("g1.dot", align_by_algorithm=False)
g1.convertDot2png("g1.dot")





print("\n -> Save full flow to file --------------------------------------------------- \n")

flow.saveFlowToFile("test_a_flow.json")



##########################################
# RDF processor

pRDF = Processor_RDF("pRDF", flow, "../CMS_nanoAOD/test_nanoAOD.root", "Events")


pRDF.RunProcessor()






print("[test] end")
