from infoGraph import InfoView, InfoGraph
from interfaceDictionary import interfaceDictionary
from eventFlow import SampleProcessing
import ROOT
from ROOT import TFile
import os


#######################################################################################
#
#
#
#######################################################################################


class ProcessorLoop:

    def __init__(self, name, flow, file_name, tree_name):

        print("[pRDF] __init__ : name = ", name, "  for flow = ", flow.name)

        self.name      = name
        self.flow      = flow
        self.file_name = file_name
        self.tree_name = tree_name
        self.dag       = "NOT_SET"
        self.cpp_text  = ""

        self.Types     = {}
        self.fileTypes = {}

        self.listOfRankedViews = []
        self.active_regions    = []

        self.cs        = self.generate_code_snippets()

        self.getFileTypes()

        # TO BE CHECKED : relevant for the functions declared in helpers.h
        ROOT.gInterpreter.Declare(self.cs["cpp_preprocessor"])

        print("[pLoop] ProcessorLoop __init__ : flow      = ", self.flow.name)


        #        print("************\n************\n************\n")
        #
        #        for i in self.cs:
        #            print("\n\n", i, "\n")
        #            print(self.cs[i])
        #
        #        print("************\n************\n************\n")

        


    #######################################################################################
    #
    def getFileTypes(self):

        _file = ROOT.TFile(self.file_name)
        _tree = _file.Get(self.tree_name)

        for _leaf in _tree.GetListOfLeaves():

            _leaf_name  = _leaf.GetName()
            _leaf_title = _leaf.GetTitle()
            _leaf_type  = _leaf.GetTypeName()

            _type        = _leaf_type
            

            # Check if the leaf contains an array

            if ('[' in _leaf_title) and (']' in _leaf_title):

                _type = 'array<'+_leaf_type+'>'


            self.fileTypes[_leaf_name] = _type


        _file.Close()


        print("\n@@  getFileTypes  @@@@@@@@@@@@@@@@@@@@@@@@@")
        for l in self.fileTypes:

            s_l   = self.flow.ID.target2source(l) 

            vtest = self.flow.has_index(s_l)

            if s_l != l:
                print(f"{l :<55}{' '}{  self.fileTypes[l] :<40}{'  -  '}{vtest}{'   ----->  '}{s_l}")
            else:
                print(f"{l :<55}{' '}{  self.fileTypes[l] :<40}{'  -  '}{vtest}")

        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n")


        return



    #######################################################################################
    #
    def init_dag(self):

        self.dag = self.flow.GetGraphForTargets()

        print(f"{'[pLoop] init_dag : '}{self.dag.name :<30}{'   ( '}{type(self.dag)}{' )'}")

        self.dag.print_graph()

        return




    #######################################################################################
    #
    def init_input_variables(self):

        # Update dictionary of variables' type for the input variables (here is the only place where the translation is strictly needed!)
        for v in self.dag.views:

            t_v = self.flow.ID.translate_string(v)

            if t_v in self.fileTypes:

                if self.flow.has_index(v):
                    _fType = self.fileTypes[t_v]
                    _type  = _fType
                    
                    # Map arrays and vectors to RVecs

                    if _fType.startswith('array<'):
                        _type = _fType.replace('array<', 'ROOT::VecOps::RVec<', 1)

                    if _fType.startswith('vector<'):
                        _type = _fType.replace('vector<', 'ROOT::VecOps::RVec<', 1)

                    self.Types[v] = _type


                else:
                    self.Types[v] = self.fileTypes[v]


        # Update list of ranked nodes
        self.listOfRankedViews = self.dag.list_of_ranked_views()

                
        print("-- init_input_variables -----------------------------")
        for v in self.Types:
            vtest    = self.flow.has_index(v)
            t_v      = self.flow.ID.translate_string(v)
            t_v_type = self.fileTypes[t_v]
            print(f"{v :<30}{'  ->  '}{self.Types[v]}{'  -  '}{vtest}{'  -  '}{t_v :<30}{t_v_type}")
        print("-----------------------------------------------------")



        # Get list of active regions
        self.active_regions = self.flow.GetListOfRegionsForTargets()

        print("\n List of active regions : \n", self.active_regions, "\n")


        return



    #######################################################################################
    #

    #    def Generate_Loop_cpp(self, cpp_file_name="loop_processor.C", translate=False):
    #
    #        print("[pLoop] Generate_Loop_cpp -> translate = "+str(translate)+" \n\n")
    #
    #        self.init_dag(translate)

    def Generate_Loop_cpp(self, cpp_file_name="loop_processor.C"):

        print("[pLoop] Generate_Loop_cpp  \n\n")

        self.init_dag()
        self.init_input_variables()

        self.dag.Plot("loop_target_graph.dot")

        Loop_cpp_txt = ""


        regions_dictionary = self.flow.regions_dictionary
        region_nodes       = self.flow.get_region_nodes_dictionary(self.dag)

        
        ###################################################

        
        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" REGION DICTIONARY \n")
        for _r in regions_dictionary:
            print(f"{_r :<33}{' selections      : '}{regions_dictionary[_r]['selections']}")
            print(f"{'' :<33}{' event weights   : '}{regions_dictionary[_r]['event_weights']}")
            print(f"{'' :<33}{' regionWeight_id : '}{regions_dictionary[_r]['regionWeight_id']}")
            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")


            

        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" NODES FOR REGION \n")
        for _r in region_nodes:
            for _n in region_nodes[_r]:
                print(f"{_r :<35}{_n}")
            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")



        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" SCHEMA \n")
        for _r in region_nodes:

            sels = regions_dictionary[_r]['selections']

            print("")
            print(f"{' Region : '}{_r :<35}{'  - selections : '}{sels}")
            print("")

            for _n in region_nodes[_r]:

                _v = self.dag.views[_n]

                txt = "NONE"
                
                if _v.is_input():
                    if _v.is_constant():      txt = "CONST"
                    else:                     txt = "INPUT"
                if _v.is_transformation():    txt = _v.algorithm

                print(f"{_n :<48}{txt}")




            print("")
        print("\n+++++++++++++++++++++++++++++++++++++\n")


        ###################################################



        ###  Includes
        Loop_cpp_txt += self.cs["cpp_preprocessor"]

        ###  Functions
        Loop_cpp_txt += self.generate_Loop_Functions_Code()

        ###  Loop function begin
        Loop_cpp_txt += self.cs["processorLoop_begin"]
            
        ###  Input file reader
        Loop_cpp_txt += self.configure_input_file_reader()

        ###  Constants definition
        Loop_cpp_txt += self.define_constants()

        ###  Input variables definition
        Loop_cpp_txt += self.define_input_variables()

        ###  H1Ds definition
        Loop_cpp_txt += self.define_H1Ds()

        ###  Begin event loop
        Loop_cpp_txt += self.cs["processorLoop_begin_event_loop"]

        ###  THIS STEP MIGHT BE REMOVED: validity of a variable is intrinsically guaranteed by the graph structure
        ###  (i.e. for any event a varible is accessed only if that variable has been first evaluated for the same event)
        ###  Reset all the selections vaiables to false at the beginning of a new event!
        Loop_cpp_txt += self.reset_requirement_variables()
        Loop_cpp_txt += "\n\n"

        ###  Update input variables
        Loop_cpp_txt += self.define_input_update()
        Loop_cpp_txt += "\n\n"



        ###  event loop operations

        Loop_cpp_txt += self.event_operations()
        Loop_cpp_txt += "\n"

        

        ###  Close event loop
        Loop_cpp_txt += self.cs["processorLoop_close_event_loop"]

        ###  Loop function end
        Loop_cpp_txt += self.cs["processorLoop_end"]


        ###  Dictionary and compilation comments
        Loop_cpp_txt += self.cs["processorLoop_dictionary"]


        print("\n===== Loop CPP_TEXT =================================\n")
        print(Loop_cpp_txt)


        cpp_file = open("eventProcessor_Loop.cxx", "w")

        cpp_file.write(Loop_cpp_txt)

        cpp_file.close()



        

        print("\n+++++++++++++++++++++++++++++++++++++")
        print(" TYPES \n")
        for _v in self.Types:
            print(f"{_v :<52}{self.Types[_v]}")
        print("\n+++++++++++++++++++++++++++++++++++++\n")
        

        
        return


    #######################################################################################
    #
    def generate_Loop_Functions_Code(self):

        funTxt = ""

        for v in self.listOfRankedViews:

            _view = self.dag.views[v]

            if self.flow.is_view_H1D(_view):
                continue


            fTxt = f"{'[pLoop] Generate function for view  '}{v :<30}"

            if _view.is_input():
                t_v = _view.view
                if not _view.is_constant():
                    t_v = self.flow.ID.translate_string(_view.view)
                fTxt += f"{' INPUT     ( '}{t_v}{' )'}"
            else:
                fTxt += f"{' TRANSFORMATION -> inputs = '}"
                for o in _view.origins:
                    fTxt += f"{o : <21}"

            print(fTxt)
                

            if _view.is_transformation() or _view.is_constant():
                funTxt += self.getFunctionForView(_view, declaration_only=False)
                funTxt += '\n'

        return funTxt






    #######################################################################################
    #
    def getFunctionForView(self, view, declaration_only=False):

        view_name    = view.view

        f_name       = 'func__'+view_name
        f_body       = view.algorithm
        f_type       = 'auto'

        par_list     = [self.Types[o]+' '+o for o in view.origins]

        f_parameters = ',\n\t\t'.join(par_list)


        if not view_name in self.Types:

            fCode  = f_type+' '+f_name
            fCode += '('+f_parameters+') '
            fCode += '{ return '+f_body+'; }'

            f_type = self.returnType(f_name, fCode)

            self.Types[view_name] = f_type
            self.Types[f_name]    = f_type

        else:

            f_type = self.Types[f_name]

            
        fCode  = f_type+' '+f_name
        fCode += '(\n\t\t'+f_parameters+')'
        if not declaration_only:
            fCode += ' {\n\treturn '+f_body+';\n}'
        else:
            fCode += ';'


        if self.dag.isNodeRequirement(view_name):
            if f_type != "bool" and f_type != "Bool_t":
                print("[pLoop] ** WARNING ** Non-boolean return type for  ", f_name)
        
        return fCode




    #######################################################################################
    # f_autocppcode : full function implementation with auto return type
    #
    def returnType(self, f_name, f_autocppcode):

        ### NOTE : TypeID2TypeName might be re-implemented (https://root.cern/doc/v622/RDFUtils_8cxx_source.html#l00084)
        
        ROOT.gInterpreter.Declare(f_autocppcode)
        getTypeNameF = "auto %s_typestring=ROOT::Internal::RDF::TypeID2TypeName(typeid(ROOT::TypeTraits::CallableTraits<decltype(%s)>::ret_type));" % (f_name, f_name)
        ROOT.gInterpreter.ProcessLine(getTypeNameF)
        fretType = getattr(ROOT, "%s_typestring" % f_name)

        return fretType




    #######################################################################################
    #
    def configure_input_file_reader(self):

        inputTxt = ""

        inputTxt += '  TFile* input_file = TFile::Open("'
        inputTxt += self.file_name
        inputTxt += '");\n\n'

        inputTxt += '  TTree* input_tree = (TTree*)input_file->Get("'
        inputTxt += self.tree_name
        inputTxt += '");\n\n'

        inputTxt += '  TTreeReader reader(input_tree);\n\n'

        inputTxt += '  reader.Restart();\n\n'

        return inputTxt


    

    #######################################################################################
    #
    def define_constants(self):

        constTxt = ""

        for v in self.listOfRankedViews:

            _v = self.dag.views[v]

            if _v.is_constant():
                constTxt += '  const '+self.Types[_v.view]+' '+f"{_v.view :<30}"+' = func__'+_v.view+'();\n'

        return constTxt


    

    #######################################################################################
    #
    def define_input_variables(self):

        inputTxt = "\n"

        # Definition of the TTreeReaderArrays and TTreeReadersValues
        
        for v in self.listOfRankedViews:

            _v = self.dag.views[v]

            if (_v.is_input() and (not _v.is_constant())):

                # This is a variable read from the input file - then it needs the translation
                t_view = self.flow.ID.translate_string(_v.view)

                _fType = self.fileTypes[t_view]
                _type  = _fType

                if self.flow.has_index(_v.view):

                    if _fType.startswith('array<'):
                        _type = _fType.replace('array<', '', 1).replace('>', '', 1)

                    if _fType.startswith('vector<'):
                        _type = _fType.replace('vector<', '', 1).replace('>', '', 1)


                    _raType = 'TTreeReaderArray<'+_type+'>'

                    print("***********  ", _v.view, "  -->>  ", t_view)

                    inputTxt += '  '+f"{_raType :<30}"+' ra_'+_v.view+'(reader, "'+t_view+'");\n'

                else:

                    #                    _rvType = 'TTreeReaderValue<'+self.fileTypes[_v.view]+'>'
                    #                    inputTxt += '  '+f"{_rvType :<30}"+' rv_'+_v.view+'(reader, "'+_v.view+'");\n'

                    ### TO BE CHECKED

                    _rvType = 'TTreeReaderValue<'+_type+'>'
                    inputTxt += '  '+f"{_rvType :<30}"+' rv_'+_v.view+'(reader, "'+t_view+'");\n'
                    

        inputTxt += '\n\n'


        # Definition of the variable used in the analysis of the event

        for v in self.listOfRankedViews:

            _v = self.dag.views[v]

            if ((not self.flow.is_view_H1D(_v)) and (not _v.is_constant())):

                inputTxt += '  '+f"{self.Types[_v.view] :<30}"+' '+_v.view+';\n'
                    
        inputTxt += '\n\n'


        return inputTxt


    

    #######################################################################################
    #
    def define_H1Ds(self):

        h1dsTxt = "\n"

        h1dsDictionary = self.flow.GetH1DsDictionary()

        for h in h1dsDictionary:

            hd = h1dsDictionary[h]

            h_name      = h
            h_var       = hd["var"]
            h_weight    = hd["weight"]
            h_nBins     = hd["nBins"]
            h_xMin      = hd["xMin"]
            h_xMax      = hd["xMax"]
            h_region    = hd["histo_region"]
            v_region    = hd["var_region"]
            h_selection = hd["histo_selection"]
            h_title     = hd["title"]

            #            _h1 = 'r.histos[std::string("'+h_name+'")]'
            #            h1dsTxt += '  '+f"{_h1 :<65}"+' = TH1D("'+h_name+'", "'+h_title+'", '+h_nBins+', '+h_xMin+', '+h_xMax+');\n'

            _h1 = 'r.histos[std::string("'+h_name+'")]'
            _h2 = ' = TH1D("'+h_name+'", '
            _h3 = '"'+h_title+'", '
            _h4 = f"{h_nBins :>6}{' , '}{h_xMin :>6}{' , '}{h_xMax :>6}{');'}"
            
            h1dsTxt += f"{'  '}{_h1 :<65}{_h2 :<50}{_h3 :<35}{_h4}"+'\n'

        h1dsTxt += '\n\n'

        for h in h1dsDictionary:
            h1dsTxt += '  TH1D* '+f"{h :<40}"+' = &(r.histos[std::string("'+h+'")]);\n'


        return h1dsTxt


    
    #######################################################################################
    #
    def define_input_update(self):

        inputTxt = "\n"

        for v in self.listOfRankedViews:

            _v = self.dag.views[v]

            if (_v.is_input() and (not _v.is_constant())):

                v_name = _v.view

                if self.flow.has_index(v_name):

                    inputTxt += '    '+f"{v_name :<30}"+' = '+self.Types[v_name]+"(ra_"+v_name+".begin() , ra_"+v_name+".end() );\n"

                else:

                    ### TO BE CHECKED !!
                    inputTxt += '    '+f"{v_name :<30}"+' = ('+self.Types[v_name]+")(*rv_"+v_name+");\n"
                    
        return inputTxt





    #######################################################################################
    #
    def reset_requirement_variables(self):

        inputTxt = "\n"

        for v in self.dag.list_of_requirement_nodes():

            inputTxt += '    '+f"{v :<30}"+' = false;\n'

        return inputTxt





    #######################################################################################
    #
    def event_operations(self):

        bodyTxt = ""

        h1dsDictionary     = self.flow.GetH1DsDictionary()
        region_nodes       = self.flow.get_region_nodes_dictionary(self.dag)


        for _r in region_nodes:

            indent = '    '

            sels = self.flow.regions_dictionary[_r]['selections']

            _condition = " and ".join(sels)

            if sels:
                bodyTxt += "\n\n"+indent+"if ("+_condition+") {\n"
                indent += '  '


            for _n in region_nodes[_r]:

                _v = self.dag.views[_n]

                if not _v.is_transformation():
                    continue

                if self.flow.is_view_H1D(_v):

                    h_name   = _v.view
                    h_var    = h1dsDictionary[h_name]["var"]
                    h_weight = h1dsDictionary[h_name]["weight"]

                    bodyTxt += indent+f"{h_name :<50}"+" -> Fill("+h_var+", "+h_weight+");\n"

                else:
                    f_parameters = ', '.join(_v.origins)

                    bodyTxt += indent+f"{_n :<50}"+" = func__"+_n+"("+f_parameters+");\n"


            if sels:
                indent   = indent[:-2]
                bodyTxt += indent+"}\n"

        return bodyTxt





    #######################################################################################
    #
    def Compile_cpp_file(self, cpp_file_name="eventProcessor_Loop.cxx"):

        so_file_name            = cpp_file_name.replace('.cxx', '.so')
        lib_file_name           = 'lib_'+so_file_name
        dictionary_file_name    = cpp_file_name.replace('.cxx', '_dict.cxx')
        dictionary_so_file_name = dictionary_file_name.replace('.cxx', '.so')

        os.system("rm %s" % so_file_name)
        os.system("rm %s" % lib_file_name)
        os.system("rm %s" % dictionary_file_name)
        os.system("rm %s" % dictionary_so_file_name)
        

        print("Generating root dictionary : rootcling -I./ -f %s %s " % (dictionary_file_name, cpp_file_name))
        os.system(                         "rootcling -I./ -f %s %s " % (dictionary_file_name, cpp_file_name))

        print("Compiling dictionary       : g++ -shared -fPIC -Wall -L. $(root-config --libs --cflags) -I. %s -o %s" % (dictionary_file_name, dictionary_so_file_name))
        os.system(                         "g++ -shared -fPIC -Wall -L. $(root-config --libs --cflags) -I. %s -o %s" % (dictionary_file_name, dictionary_so_file_name))

        print("Compiling eventProcessor   : g++ -shared -fPIC -Wall -L. $(root-config --libs --cflags) -I. %s -o %s" % (cpp_file_name, so_file_name))
        os.system(                         "g++ -shared -fPIC -Wall -L. $(root-config --libs --cflags) -I. %s -o %s" % (cpp_file_name, so_file_name))

        print("Generating library         : g++ -shared -o %s %s %s" % (lib_file_name, so_file_name, dictionary_so_file_name))
        os.system(                         "g++ -shared -o %s %s %s" % (lib_file_name, so_file_name, dictionary_so_file_name))

        return

    #############
    # Note:
    # in root
    # - .L lib_eventProcessor_Loop.so
    # - gInterpreter->Declare("Result event_processorLoop();")
    # - Result r = event_processorLoop()
    # - TH1D* h = &(r.histos[std::string("HISTO_LeadMuon_pt__etaLeadMuonNeg")])
    # - h->Draw()
















    def generate_code_snippets(self):

        _cs = {}

        ###
        
        cpp_preprocessor_text = '''
#include <vector>
#include <map>
#include <utility>

#include <TFile.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>
#include <TH1D.h>

#include <Math/VectorUtil.h>
#include <ROOT/RVec.hxx>
#include "Math/Vector4D.h"
#include <ROOT/RDataFrame.hxx>
#include "src/helpers.h"

//#define MemberMap(vector,member) Map(vector,[](auto x){return x.member;})
//#define P4DELTAR ROOT::Math::VectorUtil::DeltaR<ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>,ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>> 

//using namespace std;

#ifndef NAILSTUFF
#define NAILSTUFF

struct Result {
  Result() {}
  std::map<std::string, TH1D> histos;
};

#endif

'''
        _cs["cpp_preprocessor"] = cpp_preprocessor_text

        ###

        histos_function_declaration_text = '''
std::vector<ROOT::RDF::RResultPtr<TH1D>> histosWithSelection_eventProcessor(std::map<std::string,RNode> &rdf, std::string sel="1");

'''
        _cs["histos_function_declaration"] = histos_function_declaration_text

        ###

        processorLoop_begin_text = '''

Result event_processorLoop() {

  Result r;

'''
        _cs["processorLoop_begin"] = processorLoop_begin_text

        ###

        processorLoop_begin_event_loop_text = '''

  int counter = 0;

  while (reader.Next()) {

'''
        _cs["processorLoop_begin_event_loop"] = processorLoop_begin_event_loop_text

        ###

        processorLoop_close_event_loop_text = '''

    counter++;
    if ((counter%1000) == 0) { std::cout << "Processed events  " << counter << std::endl; }

  }

'''
        _cs["processorLoop_close_event_loop"] = processorLoop_close_event_loop_text

        ###

        processorLoop_end_text = '''

  return r;
}

'''
        _cs["processorLoop_end"] = processorLoop_end_text

        ###

        processorLoop_extra_text = '''
  r.histos[0]->SetXTitle("x-label");

'''
        _cs["processorLoop_extra"] = processorLoop_extra_text

        ###

        processorLoop_dictionary_text = '''

#ifdef __CLING__

#pragma link C++ struct Result+;

#endif


////////////////////////////////////////////////////////////////
//
// Compiling with dictionay:
//
// - rootcling -I./ -f NAME_dict.cxx NAME.C
// - g++ -c -fPIC -Wall -L. $(root-config --libs --cflags) -I. NAME.C -o NAME.o
// - g++ -shared -fPIC -Wall -L. $(root-config --libs --cflags) -I. NAME_dict.cxx -o NAME_dict.o
// - g++ -shared -o NAME.so NAME.o NAME_dict.o
//
////////////////////////////////////////////////////////////////

'''
        _cs["processorLoop_dictionary"] = processorLoop_dictionary_text

        return _cs


