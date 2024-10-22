from infoGraph import InfoView, InfoGraph
from interfaceDictionary import interfaceDictionary
import json
import copy
import os
import hashlib


#######################################################################################
# Open points:
#   - some functions are RDF specific (i.e. Combinations, Take): evaluate if these needs to be generalized
#   - protection for boolean vectors for RDF not yet implemented
#       - this should be moved to the RDF's interface
#   - (OK - wrapped!)a few methods of the dictionary used by the translator are accessed directly tX.ID.***
#       - these should be nicely wrapped in translator's interface
#
#   - Requirements:
#       - (OK) implemented for selections
#       - NOT implemented yet for weights - TBC if this step is better fitted in the backend processor ... 
#
#   - Snapshots:
#       - NOT imlemented yet
#
#   - TakePair
#       - implemented for pairs only (not triplets yet)
#   - Distinct
#       - function implemented for n=2 only, so far
#       - should probably be renamed Pairs (or PairsFrom)
#       - TBC: it might be extended to pairs of different objects changing the "collection" input to a list of collections
#              On second thoughts this might be not practical: the definition of the variables of the combined pair is not automatic
#              (the features of the combined pair are - in principle - different from the ones of the building candidates - this is different respect to a pair of candidates of the same type!
#
#
#   - Regions: part of the datasample defined by a selection chain
#       - dictionary_of_regions : {region_name : list_of_selections for that region}
#       - region_name is defined by the last set of requirements for a node (e.g.: H1D might have more than 1 requirement - otherwise the region_name is that of
#         the last requirement in a selection/requirements chain and the list_of_requirements is the selection chain up to that node)
#
#
#######################################################################################


class SampleProcessing:

    def __init__(self, name, dictionaryFile=""):
        print("[SP] __init__ : name = ", name)

        self.name       = name
        self.targetList = []
        self.AG         = InfoGraph(name+"_AG")

        self.event_weights      = []   # list of event weight nodes

        self.histos1D           = {}   # dictionary structure { h_name : { 'region'   : region_name ,
                                       #                                   'variable' : var ,
                                       #                                   'binning'  : [nBins, minB, maxB] } }
                                       #
                                       # * h_name      = <histo name>__<region_name>  (UNIQUE identifier for this histo)
                                       # * region_name = SINGLE region (i.e. selection) name - e.g. an eta range - for this histo



        self.regions_dictionary = {}   # dictionary structure {region ID : {'selections'      : ranked LIST of selections ,
                                       #                                    'event_weights'   : ranked LIST of event weights,
                                       #                                    'regionWeight_id' : region weight id } }
                                       #
                                       # * region id        = message digest (md5) of the (ranked) list of the selections
                                       # * region weight id = message digest (md5) of the (ranked) list of the event weights

        self.init_interfaceDictionary(dictionaryFile)


    def init_interfaceDictionary(self, dictionaryFile):
        self.ID = interfaceDictionary("pippo", dictionaryFile)
        return


    #####################################################
    # Info dictionary 
    #####################################################

    def get_info_dictionary(self, alternate_AG=""):

        info_dictionary                       = {}

        info_dictionary['name']               = self.name
        info_dictionary['type']               = str(type(self))
        info_dictionary['targetList']         = self.targetList
        info_dictionary['regions_dictionary'] = self.regions_dictionary

        if alternate_AG == "":
            info_dictionary['AG'] = self.AG.get_info_dictionary()
        else:
            info_dictionary['AG'] = alternate_AG.get_info_dictionary()

        info_dictionary['ID']     = self.ID.get_info_dictionary()

        return info_dictionary



    def configure_from_info_dictionary(self, info_dictionary):
        self.name                            = info_dictionary['name']
        self.targetList                      = info_dictionary['targetList']
        self.regions_dictionary              = info_dictionary['regions_dictionary']
        self.AG.configure_from_info_dictionary(info_dictionary['AG'])
        self.ID.configure_from_info_dictionary(info_dictionary['ID'])
        return






    #####################################################
    # Flow save & load
    #####################################################

    def saveFlowToFile(self, fileName = "flow.json", alternate_AG=""):

        info_dictionary = self.get_info_dictionary(alternate_AG)

        with open(fileName, "w") as file:
            json.dump(info_dictionary, file)
        return



    def loadFlowFromFile(self, fileName):

        print("Loading flow from file  ", fileName)

        info_dictionary = {}
        with open(fileName) as file:
            info_dictionary = json.load(file)

        self.configure_from_info_dictionary(info_dictionary)

        return





    #####################################################
    # Tools
    #####################################################

    def is_object_like_call(self, varString):

        varName, varFeat = self.ID.split_name_feat_base(varString)
        nf               = self.ID.number_of_features(varName)

        if (varFeat == 'NONE') and (nf > 0):
            return True
        
        return False


    def has_index(self, varString):    return self.ID.is_indexed(varString)

    

    #####################################################
    # Flow definition
    #####################################################

    #############
    # Base definition for analysis variables (views)
    def Define(self, name, code='', requires=[]):
        definition = code if code != '' else 'input'
        print(f"{'[SP] Define        : '}{name : <37}{' as   ' : <20}{definition}")

        if self.AG.isNodeDefined(name):
            print(f"{'[SP] Define        : '}{name : <37}{' node ALREADY DEFINED -> SKIP !'}")
            return

        inputList=[]
        if code != '':
            inputList = self.ID.get_var_list(code) # This method returns the list of the variables in the string passed (NO translation) - translation will be in the backend interface
            for var in inputList:

                # Check if a object or collection variable is accessed properly (through its components - not addressing the whole "object")
                if self.is_object_like_call(var):
                    print(f"{'[SP] ERROR: variable with feature NOT accessed properly - it must be adressed through its components, and not as a whole object!  '}{var : <37}{'  -> SKIP DEFINITION !'}")
                    return

                # Check if the node for the input variable is already defined
                if not self.AG.isNodeDefined(var):
                    # If variable is in the data dictionary it is an available input -> can be defined
                    if self.ID.is_defined(var):
                        print(f"{'[SP] Define        : '}{name : <37}{' input node added ' : <20}{var}")
                        self.AG.addNode(var)
                    else:
                        # Variable name is not in the data dictionary AND not defined yet -> it CANNOT be defined automatically because it will have no configuration of its inputs! -> Rise ERROR
                        print(f"{'[SP] Define        : '}{name : <37}{' ERROR: MISSING input ' : <20}{var}")
                        return
                        
        self.AG.addNode(name, inputList, code, requirements_list=requires)
        print(f"{'[SP] Define        : '}{name : <37}{' inputs '}{inputList}")


        self.ID.add_variable(name)

        return


    #############
    # Define multiplicative event weight - nodes to be generated once the variable definition is completed
    def DefineEventWeight(self, name, code='', requires=[]):
        if name in self.event_weights:
            print(f"{'[SP] Define Weight : '}{name : <37}{' weight already defined -> WARNING'}")
        else:
            self.event_weights.append(name)
            print(f"{'[SP] Define Weight : '}{name : <37}{' defined as   ' : <20}{code}{'   for requirements: '}{requires}")
            self.Define(name, code, requires)
        return


    #############
    # Filter a collection by mask
    def SubCollection(self, name, existing, sel='', requires=[], singleton=False):
        print(f"{'[SP] SubCollection : '}{name : <15}{' from  '}{existing : <15}{' with  ' : <20}{sel}")

        mask = "mask_%s_%s"%(existing, name)
        self.Define(mask, sel, requires)

        # Features SOURCE name
        for feature in self.ID.list_of_features_for(existing):
            var_target = "%s_%s"%(name, feature)
            var_source = "%s_%s"%(existing, feature)
            self.Define(var_target, "At(%s,%s)" % (var_source, mask))   # TBC : possible issue of RDF with bool types - hack with nail 1.0 -> To be implemented in backend interface

        if not singleton:
            #            self.Define("n%s" % name, "Sum(%s)" % (mask))
            self.Define(self.ID.get_counter_name_for(name), "Sum(%s)" % (mask))
        return


    #############
    # Filter a collection by index
    def SubCollectionFromIndices(self, name, existing, indices=''):
        print(f"{'[SP] SCFromIndices : '}{name : <15}{' from  '}{existing : <15}{' for indices  ' : <20}{indices}")

        # Features SOURCE name
        for feature in self.ID.list_of_features_for(existing):
            var_target = "%s_%s"%(name, feature)
            var_source = "%s_%s"%(existing, feature)
            self.Define(var_target, "Take(%s,%s)" % (var_source, indices))
            # TBC : Take() is RDF specific - a general sysntax should be pssible here, leaving the RDF specific implementation to the C++ code building

        #        self.Define("n%s" % name, "int(%s.size())" % (indices))
        self.Define(self.ID.get_counter_name_for(name), "int(%s.size())" % (indices))
        
        return


    #############
    # Define pairs from a collection
    def Distinct(self, name, collection, requires=[]):
        print(f"{'[SP] Distinct      : '}{name : <37}{' pairs from  ' : <20}{collection}")

        if not self.ID.is_defined("n%s" % collection):
            print("[SP] Distinct - ERROR : cannot find collection  ", collection)
            return

        # TBC - RF specific (but with no input ...)
        self.Define("indices_"+name, "ROOT::VecOps::Combinations(ROOT::VecOps::RVec<unsigned int>(n%s,true),2)" % collection, requires)
        ### Returns a Rvec of n Rvec, containing the indices of the first, second, etc... element of the combinations
        ### e.g.:
        ### root [1] ROOT::VecOps::Combinations(ROOT::VecOps::RVec<unsigned int>(3,true),2)
        ### (ROOT::VecOps::RVec<ROOT::VecOps::RVec<ROOT::VecOps::RVec<unsigned int>::size_type> >) { { 0, 0, 1 }, { 1, 2, 2 } }
        ###

        self.Define("indices_%s0" % name, "At(indices_%s,0)" % name)
        self.Define("indices_%s1" % name, "At(indices_%s,1)" % name)

        ### According to the previous example:
        ### <name>0_indices = { 0, 0, 1 }
        ### <name>1_indices = { 1, 2, 2 }

        self.SubCollectionFromIndices("%s0" % name, collection, indices= "indices_%s0" % name)
        self.SubCollectionFromIndices("%s1" % name, collection, indices= "indices_%s1" % name)
        return
    

    #############
    # Selection definition
    def Selection(self, name, code):
        print(f"{'[SP] Selection     : '}{name : <37}{' defined as   ' : <20}{code}")
        self.Define(name, code)
        return


    #############
    # Define a specific pair from a distinct definition
    def TakePair(self, name, existing, pairs, index, requires=[]):
        print(f"{'[SP] TakePair      : '}{name : <37}{' of  ' : <20}{existing : <20}{'  from pairs  '}{pairs}")

        self.Define("indices_%s" % (name), index, requires)

        self.ObjectAt("%s0" % (name), existing, "int(At(indices_%s0,indices_%s))" % (pairs, name))
        self.ObjectAt("%s1" % (name), existing, "int(At(indices_%s1,indices_%s))" % (pairs, name))
        return


    #############
    # Define an object from a collection (index specified)
    def ObjectAt(self, name, existing, index=""):
        print(f"{'[SP] ObjectAt      : '}{name : <15}{' from  '}{existing : <15}{' at    ' : <20}{index}")
        self.SubCollection(name, existing, index, singleton=True)
        return


    #############
    # Define a 1D histogram 
    def DefineHisto1D(self, var, requirements=[], nBins=100, xMin=0, xMax=100):

        full_hname = "HISTO_"+var
        #        if region != "":     full_hname = hname+"__"+region

        for r in requirements:    full_hname += "__"+r

        
        #        selections_list = self.AG.ranked_requirements_for_node(var)
        #        if region != "":     seletions_list.append(region)
        #
        #        _region_id = self.region_id(selections_list)
        #
        #        full_hname = hname+"__"+_region_id


        # H1D full_hname already defined
        if full_hname in self.histos1D:

            print(f"{'[SP] Define H1D    : SKIP  '}{full_hname : <37}{' already defined for '}{region}")
            return

        # H1D full_hname never defined yet (for any region) -> ADD full_hname for this region
        self.histos1D[full_hname]             = {}
        self.histos1D[full_hname]['region']   = requirements
        self.histos1D[full_hname]['variable'] = var
        self.histos1D[full_hname]['binning']  = [nBins, xMin, xMax]

        print(f"{'[SP] Define H1D    : '}{full_hname : <37}{' variable   ' : <20}{var}{'   for region: '}{requirements}")

        return

    



    #####################################################
    # DAG TRANSLATION
    #####################################################

    def translate_string(self, string_to_translate):
        return self.ID.translate_string(string_to_translate)




    def TranslateGraph(self, o_Graph):

        print("\n\n 77777777777777777777777777777777777777777777777 TRANSLATION \n\n")


        t_Graph = InfoGraph(o_Graph.name+"_translated")

        # The handling of fetching_info is TBC !!!
        
        for o_view in o_Graph.views.values():

            t_view_name              = self.ID.translate_string(o_view.view)
            t_view_algorithm         = self.ID.translate_string(o_view.algorithm)
            t_view_origins           = [self.ID.translate_string(_o) for _o in o_view.origins]
            t_view_requirements      = [self.ID.translate_string(_r) for _r in o_view.requirements]
            t_view_id_code           = copy.deepcopy(o_view.id_code)
            t_view_status            = copy.deepcopy(o_view.status)
            
            #            t_view_fetching_info     = copy.deepcopy(o_view.fetching_info)
            
            t_Graph.addNode(t_view_name, t_view_origins, t_view_algorithm, t_view_requirements, t_view_id_code, t_view_status)


        return t_Graph



    #####################################################
    # Info for backend
    #####################################################

    def SetTargets(self, tList):
        self.targetList = tList
        return


    def GetGraphForTargets(self, tList=""):
        if tList != "":
            self.SetTargets(tList)
        return self.AG.subGraphTo(self.targetList)



    def GetListOfRegionsForTargets(self):

        rList = []
        
        for target in self.targetList:

            r_id = self.region_id_for_node(target)
    
            if not r_id in rList:
                rList.append(r_id)

        return rList




    def GetH1DsDictionary(self):

        h1dsDictionary = {}

        listOfRankedViews = self.AG.list_of_ranked_views()


        for v in listOfRankedViews:

            _view = self.AG.views[v]

            if not self.is_view_H1D(_view):
                continue

            h_name = _view.view
            h_def  = _view.algorithm

            h_pars = h_def.replace('H1D::(','').replace(')','').replace(', ',',').split(',')

            h_var       = h_pars[0]
            h_weight    = h_pars[1]
            h_nBins     = h_pars[2]
            h_xMin      = h_pars[3]
            h_xMax      = h_pars[4]

            v_region    = self.region_id_for_node(v)

            h_selection = ""
            if v_region != "base":
                h_selection = 'selection_'+v_region

            
            h_region = "__".join(_view.requirements)

            h_title  = h_var+' {'+h_region+'}'
            
            print("\n == H1D :: ", v)
            print(" h_name      = ", h_name  )
            print(" h_var       = ", h_var   )
            print(" h_weight    = ", h_weight)
            print(" h_nBins     = ", h_nBins )
            print(" h_xMin      = ", h_xMin  )
            print(" h_xMax      = ", h_xMax  )
            print(" h_region    = ", h_region)
            print(" v_region    = ", v_region)
            print(" h_selection = ", h_selection)
            print(" h_title     = ", h_title)
            print("\n")


            hd = {}
            hd["var"]             =  h_var
            hd["weight"]          =  h_weight
            hd["nBins"]           =  h_nBins
            hd["xMin"]            =  h_xMin
            hd["xMax"]            =  h_xMax
            hd["histo_region"]    =  h_region
            hd["var_region"]      =  v_region
            hd["histo_selection"] =  h_selection
            hd["title"]           =  h_title

            h1dsDictionary[h_name] = hd

        return h1dsDictionary







    #####################################################
    # Regions and selection weights generation
    #####################################################

    def region_id(self, selections_list=[]):
        if not selections_list:    return "base"

        md = hashlib.md5()
        md.update("base".encode())
        for s in selections_list:    md.update(s.encode())
        return md.hexdigest()



    ################### Equivalent to region_id() -> TO BE REMOVED ?? (region_id() "evaluates", while this function search in the regions_dictionary ...)

    def get_region_id_for_requirements(self, req=[]):

        # NOTE: SAME RANKING inside the lists to be compared !!  --- The ranking might change after sub-graph extraction ?!?!?!?! -> TBC !!
        # Ranking should not be altered by sub-graph extraction by construction of the requirements chain

        for region in self.regions_dictionary:
            if req == self.regions_dictionary[region]['selections']:
                return region

        print("***************** ERROR : selection chain NOT FOUND for requirements: ", req)
        return ""



    def region_id_for_node(self, node_name):
        selections_list = self.AG.ranked_requirements_for_node(node_name)
        return self.region_id(selections_list)



    def regionWeight_id(self, event_weights_list=[]):
        md = hashlib.md5()
        md.update("base_regionWeight".encode())
        for ew in event_weights_list:    md.update(ew.encode())
        return md.hexdigest()



    def get_regionWeight_name(self, region_id):
        _regionWeight_name = "regionWeight_"+self.regions_dictionary[region_id]['regionWeight_id']
        return _regionWeight_name



    def get_regionWeight_name_for_requirements(self, req=[]):
        _region_id         = self.get_region_id_for_requirements(req)
        return self.get_regionWeight_name(_region_id)




    def list_of_weights_for_selections(self, req_list):
        lw =[]

        for ew in self.event_weights:

            ew_req = self.AG.list_of_requirements(ew)

            # If ALL the requirements for event_weight are in the requirements list for the region, then add the weight to the list
            # All "base" event_weights are added - because ew_req = [] (is empty)

            to_be_added = True

            for r in ew_req:
                if not r in req_list:
                    to_be_added = False
                    break

            if to_be_added:    lw.append(ew)

        return self.AG.rank_nodes(lw)



    
    # NOT USED - To BE REMOVED
    #    def list_of_weights_for_region(self, region):
    #        req_list = self.regions_dictionary[region]['selections']
    #        return self.list_of_weights_for_selections(req_list)




####    def list_of_ranked_nodes_per_region(self, region_id):
    



    


    def add_region(self, req_list=[]):

        region_id = self.region_id(req_list)

        if not region_id in self.regions_dictionary:

            ew_l = self.list_of_weights_for_selections(req_list)
            
            _d = {}
            _d['selections']      = req_list
            _d['event_weights']   = ew_l
            _d['regionWeight_id'] = self.regionWeight_id(ew_l)

            self.regions_dictionary[region_id] = _d

        return



    def get_H1D_ranked_requirements_list(self, hvar="", hreqs=[]):

        if not hreqs:
            rl = self.AG.list_of_requirements(hvar)
        else:
            rl = self.AG.list_of_requirements(hvar)
            for _r in hreqs:
                rl = self._merge_without_duplicates(rl, self.AG.list_of_requirements(_r)+[_r])

                #
        return self.AG.rank_nodes(rl)



    def evaluate_regions_dictionary(self):

        self.regions_dictionary.clear()
        
        print("\n========== evaluate_regions_dictionary ======================\n")

        #############
        # Views alredy defined

        for _view in self.AG.views:

            req_list  = self.AG.ranked_requirements_for_node(_view)

            self.add_region(req_list)

            print(f"{_view :<32}{'  -->  '}{req_list}")

        print("")


        #############
        # H1Ds (views NOT YET defined)

        for hname in self.histos1D:

            hvar     = self.histos1D[hname]['variable']
            hreqs    = self.histos1D[hname]['region']
            req_list = self.get_H1D_ranked_requirements_list(hvar, hreqs)

            self.add_region(req_list)

            print(f"{'H1D : '}{hvar :<26}{'  -->  '}{req_list}")


        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" REGION DICTIONARY \n")
        for _r in self.regions_dictionary:
            print(f"{_r :<33}{' selections      : '}{self.regions_dictionary[_r]['selections']}")
            print(f"{'' :<33}{' event weights   : '}{self.regions_dictionary[_r]['event_weights']}")
            print(f"{'' :<33}{' regionWeight_id : '}{self.regions_dictionary[_r]['regionWeight_id']}")
            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")


        return





    # NOT USED - to be removed ?
    #    def get_regions_dictionary(self):
    #
    #        if not self.regions_dictionary:
    #            # regions dictionary is empy - so re-evaluate
    #            self.evaluate_regions_dictionary()
    #
    #        return self.regions_dictionary


    

    def GenerateSelectionWeights(self):

        self.evaluate_regions_dictionary()

        for region in self.regions_dictionary:

            regionWeight_name = self.get_regionWeight_name(region)

            if not self.AG.isNodeDefined(regionWeight_name):

                req_list          = self.regions_dictionary[region]['selections']
                weights_list      = self.regions_dictionary[region]['event_weights']

                if not weights_list:
                    weights_list = ["1.0f"]
                
                regionWeight_code = ' * '.join(weights_list)

                # It is important to propagate the requirements list to the node definition in order to catch the selections applied to the H1D directly (e.g. eta range)
                self.Define(regionWeight_name, regionWeight_code, requires=req_list)

        return




    def GenerateHistos1D(self):

        for hname in self.histos1D:

            hvar     = self.histos1D[hname]['variable']
            hreqs    = self.histos1D[hname]['region']
            hbinning = self.histos1D[hname]['binning']

            # NOTE:  The ranking might change after sub-graph extraction ?!?!?!?! -> It should not (by construction - at least the relative ranking of nodes should not change!)
            #        Can the ranking change for sub-graph ??? (assuming no activation)
            #        In this case the ranking is evaluated on the complete Analysis Graph (not only the sub-graph defined by targets) -> OK! 

            req_list          = self.get_H1D_ranked_requirements_list(hvar, hreqs)
            regionWeight_name = self.get_regionWeight_name_for_requirements(req_list)

            hcode = 'H1D::('+hvar+', '+regionWeight_name+', '+str(hbinning[0])+', '+str(hbinning[1])+', '+str(hbinning[2])+')'

            #            if hregion != "":
            #                self.Define(hname, hcode, [hregion])
            #            else:
            #                self.Define(hname, hcode, [])

            self.Define(hname, hcode, hreqs)
                
        return




    def graph_has_region(self, graph, region):

        regionWeight_name = self.get_regionWeight_name(region)
        return graph.isNodeDefined(regionWeight_name)



    def is_view_H1D(self, _view):
        if (_view.algorithm.startswith('H1D::')):    return True
        return False
        
    

    #####################################################
    # Service functions
    #####################################################

    def Print(self):
        print("[SP] Printing analysis graph & dot file generation")

        self.AG.print_graph()

        self.AG.newDotFile("ag_test_1.dot")
        os.system('dot ag_test_1.dot -Tpng -o ag_test_1.png')

        return




    def _merge_without_duplicates(self, l1=[], l2=[]):
        _l = list(l1)
        for i in l2:
            if not i in _l:
                _l.append(i)
        return _l











    def BuildFlow(self):

        print("\n[BuildFlow] -> GenerateSelectionWeights --------------------------------------------------- \n")

        self.GenerateSelectionWeights()


        print("\n[BuildFlow] -> GenerateHistos1D --------------------------------------------------- \n")

        self.GenerateHistos1D()




        ranked_regions = {}

        for _r in self.regions_dictionary:

            region = self.regions_dictionary[_r]
            region_rank = len(region['selections'])

            if not region_rank in ranked_regions:

                ranked_regions[region_rank] = [_r]

            else:

                ranked_regions[region_rank].append(_r)


        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" RANKED REGIONS \n")
        for _rank in ranked_regions:
            print(f"{_rank :<5}{ranked_regions[_rank]}")
            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")


        region_nodes = self.get_region_nodes_dictionary(self.AG)

            

        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" NODES FOR REGION \n")
        for _r in region_nodes:
            for _n in region_nodes[_r]:
                print(f"{_r :<35}{_n}")
            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")



        
        return








    def get_region_nodes_dictionary(self, _dag):
        
        region_nodes = {}

        for _r in self.regions_dictionary:

            #            print("\n [get_region_nodes_dictionary] Nodes for region  ", _r, "\n")

            n4r = [n for n in _dag.views if self.region_id_for_node(n) == _r]

            region_nodes[_r] = _dag.rank_nodes(n4r)

            #            print(region_nodes[_r])

        return region_nodes


    
        


    #####################################################
    # Test functions
    #####################################################

    def GraphTest(self, targetList):
        print("[Print] printing analysis graph")
        self.AG.print_graph()

        self.AG.newDotFile("ag_test_1.dot", align_by_algorithm=False)


        print("[Print] printing analysis sub-graph to ", targetList)

        g1 = self.GetGraphForTargets(targetList)

        g1.print_graph()

        g1.saveGraph("g1.json")
        
        g1.newDotFile("g1.dot", align_by_algorithm=False)

        g1.convertDot2png("g1.dot")
        
        print("==================== RANKED LIST OF REQUIREMNTS ==============")
        for v in g1.views:
            rrl  = g1.ranked_requirements_for_node(v)
            print(f"{'- Requirements for  '}{v : <32}{rrl}")


        print("\n\n==================== RANKED VIEWS ==============\n")
        rv = g1.ranked_views()
        for r in rv:
            print(r, "    ", rv[r])


        self.ID.save_DB('g1_db.json')

        return



    def GraphTestWeights(self, targetList):

        print("")
        print("[GenerateSelectionWeights] --------------------------------------------------- ")
        print("")

        self.GenerateSelectionWeights()

        print("")
        print("[GenerateHistos1D] --------------------------------------------------- ")
        print("")

        self.GenerateHistos1D()
        
        print("\n --------------------------------------------------- \n")


        #        self.AG.print_graph()


        print(" ---- Region for node ------------------------------- \n")

        for node in self.AG.views:

            node_region = self.region_id_for_node(node)

            rreq        = self.AG.ranked_requirements_for_node(node)
            
            print(f"{node :<50}{node_region :<34}{rreq}")

        print("\n --------------------------------------------------- \n")




        print("[Print] printing analysis graph")
        self.AG.print_graph()

        self.AG.newDotFile("ag_test_w.dot", align_by_algorithm=False)


        print("[Print] printing analysis sub-graph to ", targetList)

        g1 = self.GetGraphForTargets(targetList)

        g1.print_graph()

        g1.saveGraph("g1.json")
        
        g1.newDotFile("g1.dot", align_by_algorithm=False)
        g1.convertDot2png("g1.dot")
        
        self.ID.save_DB('g1_db.json')

        return





    def GraphTranslationTest(self, targetList):

        t_g1 = self.GetGraphForTargets(targetList)

        print("\n\n--------------------------------------------------- graph \n\n")
        t_g1.print_graph()


        t_g2 = self.TranslateGraph(t_g1)

        print("\n\n--------------------------------------------------- graph TRANSLATED\n\n")
        t_g2.print_graph()
        
        t_g1.saveGraph("t_g1.json")
        t_g1.newDotFile("t_g1.dot", align_by_algorithm=False)
        t_g1.convertDot2png("t_g1.dot")

        t_g2.saveGraph("t_g2.json")
        t_g2.newDotFile("t_g2.dot", align_by_algorithm=False)
        t_g2.convertDot2png("t_g2.dot")

        self.saveFlowToFile(fileName = "flow_0.json", alternate_AG="")

        self.saveFlowToFile(fileName = "flow_1.json", alternate_AG=t_g1)

        self.saveFlowToFile(fileName = "flow_2.json", alternate_AG=t_g2)

        return
