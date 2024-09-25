
# Interface description
from interfaceDictionary import interfaceDictionary


#####################################################################


dictionaryFileName = "nanoAOD_PHYSLITE_id.json"
dictionaryName     = "nanoAOD_PHYSLITE_test_interface"
dictionaryComment  = "Test interface to run an analysis, described in nanoAOD format, on PHYSLITE format files."


#####################################################################


t = interfaceDictionary(dictionaryName)
t.set_comment(dictionaryComment)


t.set_base_format("scalar",     "VARIABLE")
t.set_base_format("vector",     "VARIABLE[INDEX]")
t.set_base_format("object",     "VARIABLE_FEATURE")
t.set_base_format("collection", "VARIABLE_FEATURE[INDEX]")


t.set_target_format("scalar",     "VARIABLE")
t.set_target_format("vector",     "VARIABLE[INDEX]")
t.set_target_format("object",     "VARIABLE.FEATURE")
t.set_target_format("collection", "VARIABLE.FEATURE[INDEX]")


#####################################################################


#### Run & event
#
#t.add_variable("run",  "run")
#t.add_variable("luminosityBlock", "luminosityBlock")
#t.add_variable("event",  "event")


#### HLT
#
#t.add_variable("HLT", "HLT")
#t.add_feature("HLT", "IsoMu24_eta2p1",                 "IsoMu24_eta2p1")
#t.add_feature("HLT", "IsoMu24",                        "IsoMu24")
#t.add_feature("HLT", "IsoMu17_eta2p1_LooseIsoPFTau20", "IsoMu17_eta2p1_LooseIsoPFTau20")


#### PV
#
#t.add_variable("PV", "PV")
#t.add_feature("PV", "npvs", "npvs")
#t.add_feature("PV", "x",    "x")
#t.add_feature("PV", "y",    "y")
#t.add_feature("PV", "z",    "z")


### Muon

t.add_variable("Muon", "AnalysisMuonsAuxDyn")
t.add_variable("nMuon", "nMuon")
t.add_feature("Muon", "pt",             "pt")
t.add_feature("Muon", "eta",            "eta")
t.add_feature("Muon", "phi",            "phi")
#t.add_feature("Muon", "mass",           "mass")
t.add_feature("Muon", "charge",         "charge")
#t.add_feature("Muon", "pfRelIso03_all", "pfRelIso03_all")

################ TO BE CHECKED !!!
t.add_feature("Muon", "pfRelIso04_all", "topoetcone40")

#t.add_feature("Muon", "tightId",        "tightId")
#t.add_feature("Muon", "softId",         "softId")
#t.add_feature("Muon", "dxy",            "dxy")
#t.add_feature("Muon", "dxyErr",         "dxyErr")
#t.add_feature("Muon", "dz",             "dz")
#t.add_feature("Muon", "dzErr",          "dzErr")
#t.add_feature("Muon", "jetIdx",         "jetIdx")
#t.add_feature("Muon", "genPartIdx",     "genPartIdx")

#t.add_feature("Muon", "iso",            "iso")
#t.add_feature("Muon", "mediumId",       "mediumId")


#### Electron
#
#t.add_variable("Electron", "Electron")
#t.add_variable("nElectron", "nElectron")
#t.add_feature("Electron", "pt",             "pt")
#t.add_feature("Electron", "eta",            "eta")
#t.add_feature("Electron", "phi",            "phi")
#t.add_feature("Electron", "mass",           "mass")
#t.add_feature("Electron", "charge",         "charge")
#t.add_feature("Electron", "pfRelIso03_all", "pfRelIso03_all")
#t.add_feature("Electron", "dxy",             "dxy")
#t.add_feature("Electron", "dxyErr",          "dxyErr")
#t.add_feature("Electron", "dz",              "dz")
#t.add_feature("Electron", "dzErr",           "dzErr")
#t.add_feature("Electron", "cutBasedId",      "cutBasedId")
#t.add_feature("Electron", "pfId",            "pfId")
#t.add_feature("Electron", "jetIdx",          "jetIdx")
#t.add_feature("Electron", "genPartIdx",      "genPartIdx")
#
#
#### Tau
#
#t.add_variable("Tau", "Tau")
#t.add_variable("nTau", "nTau")
#t.add_feature("Tau", "pt",              "pt")
#t.add_feature("Tau", "eta",             "eta")
#t.add_feature("Tau", "phi",             "phi")
#t.add_feature("Tau", "mass",            "mass")
#t.add_feature("Tau", "charge",          "charge")
#t.add_feature("Tau", "decayMode",       "decayMode")
#t.add_feature("Tau", "relIso_all",      "relIso_all")
#t.add_feature("Tau", "jetIdx",          "jetIdx")
#t.add_feature("Tau", "genPartIdx",      "genPartIdx")
#t.add_feature("Tau", "idDecayMode",     "idDecayMode")
#t.add_feature("Tau", "idIsoRaw",        "idIsoRaw")
#t.add_feature("Tau", "idIsoVLoose",     "idIsoVLoose")
#t.add_feature("Tau", "idIsoLoose",      "idIsoLoose")
#t.add_feature("Tau", "idIsoMedium",     "idIsoMedium")
#t.add_feature("Tau", "idIsoTight",      "idIsoTight")
#t.add_feature("Tau", "idAntiEleLoose",  "idAntiEleLoose")
#t.add_feature("Tau", "idAntiEleMedium", "idAntiEleMedium")
#t.add_feature("Tau", "idAntiEleTight",  "idAntiEleTight")
#t.add_feature("Tau", "idAntiMuLoose",   "idAntiMuLoose")
#t.add_feature("Tau", "idAntiMuMedium",  "idAntiMuMedium")
#t.add_feature("Tau", "idAntiMuTight",   "idAntiMuTight")
#
#
#### Photon
#
#t.add_variable("Photon", "Photon")
#t.add_variable("nPhoton", "nPhoton")
#t.add_feature("Photon", "pt",             "pt")
#t.add_feature("Photon", "eta",            "eta")
#t.add_feature("Photon", "phi",            "phi")
#t.add_feature("Photon", "mass",           "mass")
#t.add_feature("Photon", "charge",         "charge")
#t.add_feature("Photon", "pfRelIso03_all", "pfRelIso03_all")
#t.add_feature("Photon", "jetIdx",          "jetIdx")
#t.add_feature("Photon", "genPartIdx",      "genPartIdx")
#
#
#### MET
#
#t.add_variable("MET", "MET")
#t.add_feature("MET", "pt",           "pt")
#t.add_feature("MET", "phi",          "phi")
#t.add_feature("MET", "sumet",        "sumet")
#t.add_feature("MET", "significance", "significance")
#t.add_feature("MET", "CovXX",        "CovXX")
#t.add_feature("MET", "CovXY",        "CovXY")
#t.add_feature("MET", "CovYY",        "CovYY")
#
#
#### Jet
#
#t.add_variable("Jet", "Jet")
#t.add_variable("nJet", "nJet")
#t.add_feature("Jet", "pt",   "pt")
#t.add_feature("Jet", "eta",  "eta")
#t.add_feature("Jet", "phi",  "phi")
#t.add_feature("Jet", "mass", "mass")
#t.add_feature("Jet", "puId", "puId")
#t.add_feature("Jet", "btag", "btag")


t.save_DB(dictionaryFileName)

print("\n ---------------------------- dictionary : ")
t.print_dictionary()

print("\n ---------------------------- summary : ")
t.print_summary()
