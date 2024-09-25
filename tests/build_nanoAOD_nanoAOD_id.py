
# Interface description
from interfaceDictionary import interfaceDictionary


#####################################################################

dictionaryFileName = "nanoAOD_nanoAOD_id.json"
dictionaryName     = "nanoAOD_nanoAOD_test_interface"
dictionaryComment  = "Test interface for nanoAOD->nanoAOD format translation - equivalent to NO translation!"


#####################################################################

t = interfaceDictionary(dictionaryName)
t.set_comment(dictionaryComment)


t.set_base_format("scalar",     "VARIABLE")
t.set_base_format("vector",     "VARIABLE[INDEX]")
t.set_base_format("object",     "VARIABLE_FEATURE")
t.set_base_format("collection", "VARIABLE_FEATURE[INDEX]")


t.set_target_format("scalar",     "VARIABLE")
t.set_target_format("vector",     "VARIABLE[INDEX]")
t.set_target_format("object",     "VARIABLE_FEATURE")
t.set_target_format("collection", "VARIABLE_FEATURE[INDEX]")


#####################################################################


#### Run & event

t.add_variable("run")
t.add_variable("luminosityBlock")
t.add_variable("event")


#### HLT

t.add_variable("HLT_IsoMu24_eta2p1")
t.add_variable("HLT_IsoMu24")
t.add_variable("HLT_IsoMu17_eta2p1_LooseIsoPFTau20")


#### PV

t.add_variable("PV_npvs")
t.add_variable("PV_x")
t.add_variable("PV_y")
t.add_variable("PV_z")


#### Muon

t.add_variable("nMuon")
t.add_variable("Muon_pt")
t.add_variable("Muon_eta")
t.add_variable("Muon_phi")
t.add_variable("Muon_mass")
t.add_variable("Muon_charge")
t.add_variable("Muon_pfRelIso03_all")
t.add_variable("Muon_pfRelIso04_all")
t.add_variable("Muon_tightId")
t.add_variable("Muon_softId")
t.add_variable("Muon_dxy")
t.add_variable("Muon_dxyErr")
t.add_variable("Muon_dz")
t.add_variable("Muon_dzErr")
t.add_variable("Muon_jetIdx")
t.add_variable("Muon_genPartIdx")


#### Electron

t.add_variable("nElectron")
t.add_variable("Electron_pt")
t.add_variable("Electron_eta")
t.add_variable("Electron_phi")
t.add_variable("Electron_mass")
t.add_variable("Electron_charge")
t.add_variable("Electron_pfRelIso03_all")
t.add_variable("Electron_dxy")
t.add_variable("Electron_dxyErr")
t.add_variable("Electron_dz")
t.add_variable("Electron_dzErr")
t.add_variable("Electron_cutBasedId")
t.add_variable("Electron_pfId")
t.add_variable("Electron_jetIdx")
t.add_variable("Electron_genPartIdx")


#### Tau

t.add_variable("nTau")
t.add_variable("Tau_pt")
t.add_variable("Tau_eta")
t.add_variable("Tau_phi")
t.add_variable("Tau_mass")
t.add_variable("Tau_charge")
t.add_variable("Tau_decayMode")
t.add_variable("Tau_relIso_all")
t.add_variable("Tau_jetIdx")
t.add_variable("Tau_genPartIdx")
t.add_variable("Tau_idDecayMode")
t.add_variable("Tau_idIsoRaw")
t.add_variable("Tau_idIsoVLoose")
t.add_variable("Tau_idIsoLoose")
t.add_variable("Tau_idIsoMedium")
t.add_variable("Tau_idIsoTight")
t.add_variable("Tau_idAntiEleLoose")
t.add_variable("Tau_idAntiEleMedium")
t.add_variable("Tau_idAntiEleTight")
t.add_variable("Tau_idAntiMuLoose")
t.add_variable("Tau_idAntiMuMedium")
t.add_variable("Tau_idAntiMuTight")


#### Photon

t.add_variable("nPhoton")
t.add_variable("Photon_pt")
t.add_variable("Photon_eta")
t.add_variable("Photon_phi")
t.add_variable("Photon_mass")
t.add_variable("Photon_charge")
t.add_variable("Photon_pfRelIso03_all")
t.add_variable("Photon_jetIdx")
t.add_variable("Photon_genPartIdx")


#### MET

t.add_variable("MET_pt")
t.add_variable("MET_phi")
t.add_variable("MET_sumet")
t.add_variable("MET_significance")
t.add_variable("MET_CovXX")
t.add_variable("MET_CovXY")
t.add_variable("MET_CovYY")


#### Jet

t.add_variable("nJet")
t.add_variable("Jet_pt")
t.add_variable("Jet_eta")
t.add_variable("Jet_phi")
t.add_variable("Jet_mass")
t.add_variable("Jet_puId")
t.add_variable("Jet_btag")


#####################################################################

t.save_DB(dictionaryFileName)

print("\n ---------------------------- dictionary : ")
t.print_dictionary()

print("\n ---------------------------- summary : ")
t.print_summary()
