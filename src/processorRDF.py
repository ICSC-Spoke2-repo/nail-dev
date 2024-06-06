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


class Processor_RDF:

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

        self.cs        = codeSnippets()

        self.getFileTypes()

        # TO BE CHECKED : relevant for the functions declared in helpers.h
        ROOT.gInterpreter.Declare(self.cs.cpp_includes())

        print("[pRDF] Processor_RDF __init__ : flow      = ", self.flow.name)



    #######################################################################################
    #
    def getFileTypes(self):

        _rdf = ROOT.RDataFrame(self.tree_name, self.file_name)

        for x in _rdf.GetColumnNames():
            v_n = str(x)
            #            if v_n in self.dag.views:
            vs = self.flow.ID.target2source(v_n)
            if self.flow.ID.is_defined(vs):
#                self.fileTypes[v_n] = _rdf.GetColumnType(v_n)
                self.fileTypes[vs] = _rdf.GetColumnType(v_n)

                print("v_n =", v_n, "   ", self.fileTypes[vs])
                print("vs  =", vs)
                

            #        for n in self.fileTypes:
            #            print(f"{n :<30}{'  ->  '}{self.fileTypes[n]}")
        
        del _rdf

        return



    #######################################################################################
    #
    def init_dag(self, translate=False):

        _graph = self.flow.GetGraphForTargets()


        if translate:
            print("\n\n 55555555555555555555555555555 DO TRANSLATE! \n\n")
            self.dag = self.flow.TranslateGraph(_graph)
        else:
            print("\n\n 55555555555555555555555555555 DO  NOT  TRANSLATE! \n\n")
            self.dag = _graph


        print("[pRDF] init_dag : type(dag) = ", type(self.dag))
        print("[pRDF] init_dag : name      = ", self.dag.name)

        self.dag.print_graph()

        # Update dictionary of variables' type for the input variables
        for v in self.dag.views:
            if v in self.fileTypes:
                self.Types[v] = self.fileTypes[v]


        # Update list of ranled nodes
        self.listOfRankedViews = self.dag.list_of_ranked_views()

                
        print("-----------------------------------------------------")
        for v in self.Types:
            print(f"{v :<30}{'  ->  '}{self.Types[v]}")
        print("-----------------------------------------------------")


        #        # Update list of active regions
        #        for r in self.flow.regions_dictionary:
        #
        #            rwn = "regionWeight_"+r
        #            if self.dag.isNodeDefined(rwn):
        #                self.active_regions.append(r)
        #
        #        print("\n List of active regions : \n", self.active_regions, "\n")



        # Get list of active regions
        self.active_regions = self.flow.GetListOfRegionsForTargets()

        print("\n List of active regions : \n", self.active_regions, "\n")


        return



    #######################################################################################
    #
    def GenerateRDFcpp(self, cpp_file_name="rdf_processor.C", translate=False):

        print("\n\n GenerateRDFcpp -> translate = "+str(translate)+" \n\n")


        self.init_dag(translate)
        
        self.dag.Plot("target_graph.dot")

        RDFcpp_txt = ""


        ###  Includes
        RDFcpp_txt += self.cs.cpp_includes()


        ###  Functions
        RDFcpp_txt += self.generate_RDF_Functions_Code()


        #        ### histo function declaration
        #        RDFcpp_txt += self.cs.histos_function_declaration()


        ### event processor begin
        RDFcpp_txt += self.cs.eventProcessor_begin()


        ### RDF slots declaration
        RDFcpp_txt += self.generate_RDF_Slots_Declaration()

        
        ### RDF filters declaration
        RDFcpp_txt += self.generate_RDF_Filters_Declaration()


        ### RDF H1Ds declaration
        RDFcpp_txt += self.generate_RDF_H1D_Declaration()


        ### event processor extra
        RDFcpp_txt += self.cs.eventProcessor_extra()


        ### event processor end
        RDFcpp_txt += self.cs.eventProcessor_end()


        print("\n===== CPP_TEXT =================================\n")
        print(RDFcpp_txt)


        cpp_file = open(cpp_file_name, "w")

        cpp_file.write(RDFcpp_txt)

        cpp_file.close()


        
        return



    #######################################################################################
    #
    def generate_RDF_Functions_Code(self):

        funTxt = ""

        for v in self.listOfRankedViews:

            _view = self.dag.views[v]

            if self.flow.is_view_H1D(_view):
                continue


            fTxt = f"{'[pRDF] Generate function for view  '}{v :<30}"

            if _view.is_input():
                fTxt += f"{' INPUT '}"
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
    def generate_RDF_Slots_Declaration(self):

        rdfSlots = ''

        _rdf = f"{'  auto rdf0 = rdf'}"

        for v in self.listOfRankedViews:

            _view = self.dag.views[v]

            # Skip slot delaration for H1Ds
            if not self.flow.is_view_H1D(_view):
                if _view.is_transformation() or _view.is_constant():

                    slotTxt  = _rdf+'.DefineSlot("'+_view.view+'", '
                    slotTxt += 'func__'+_view.view+', '
                    #                    if _view.has_origin():
                    #                        slotTxt += '{"'+'", "'.join(_view.origins)+'"})\n'
                    #                    else:
                    #                        slotTxt += '{})\n'                    

                    if _view.has_origin():

                        _o_names = []
                        for i in _view.origins:
                            _iv = self.dag.views[i]
                            if (_iv.is_input() and not _iv.is_constant()):
                                _o_names.append(self.flow.ID.translate_string(i))
                            else:
                                _o_names.append(i)
                        
                        slotTxt += '{"'+'", "'.join(_o_names)+'"})\n'
                    else:
                        slotTxt += '{})\n'                    

                    rdfSlots += slotTxt
                    _rdf = '\t\t '

                    print(slotTxt)

        rdfSlots   += '\t\t ;\n\n'

        rdfSlots   += '  r.rdf.emplace("",rdf0);\n\n'

        
        return rdfSlots



    #######################################################################################
    #
    def generate_RDF_Filters_Declaration(self):

        print("\n===== SELECTIONS =================================\n")

        r_d = self.flow.regions_dictionary

        ########################## WORKING HERE
        # r_d needs to be RANKED by the longest_path_lenght of the selection nodes requested in the selection chain (value for ranking for sc = max([sels for tht sc])
        # Filters need to be arranged from the shortest path onward ( -> more logical implementation and efficient execution for RDF)
        #
        # ?? selection chains should be considered (i.e. filter chain put in place here) for all the targets
        # (H1D - which used sel_weights - but variables as well - since this might be useful for snapshots/data filtration)

        selTxt = ''

        for region_id in self.active_regions:

            if region_id == "base":      continue

            _txt = '  auto selection_'+region_id+' = rdf0'

            for sel in r_d[region_id]['selections']:
                _txt += '.Filter("'+sel+'", "'+sel+'")'
            _txt += ';\n'

            _txt += '  r.rdf.emplace("selection_'+region_id+'", selection_'+region_id+');\n\n'

            print(_txt)
            print("\n")
            selTxt += _txt

        return selTxt



    #######################################################################################
    #
    def generate_RDF_H1D_Declaration(self):

        rdf_H1Ds = "\n  std::vector<ROOT::RDF::RResultPtr<TH1D>> H1Ds;\n\n"

        for v in self.listOfRankedViews:

            _view = self.dag.views[v]

            if not self.flow.is_view_H1D(_view):
                continue

            h_name = _view.view
            h_def  = _view.algorithm

            h_pars = h_def.replace('H1D::(','').replace(')','').replace(', ',',').split(',')

            h_var       = h_pars[0]
            h_weight    = h_pars[1]
            h_nBins     = h_pars[2]
            h_xMin      = h_pars[3]
            h_xMax      = h_pars[4]

            v_region    = self.flow.region_id_for_node(v)

            h_selection = ""
            if v_region != "base":
                h_selection = 'selection_'+v_region

            
            h_region = "__".join(_view.requirements)
            
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
            print("\n")

            rdf_H1Ds += '  H1Ds.emplace_back(r.rdf.find("'+h_selection+'")->second'
            rdf_H1Ds += '.Histo1D({"'+h_name+'", "'+h_var+' {'+h_region+'}", '+h_nBins+', '+h_xMin+', '+h_xMax+'},"'+h_var+'","'+h_weight+'"));\n'


        rdf_H1Ds += "\n"
        rdf_H1Ds += "  r.histos = H1Ds;\n"
        
        return rdf_H1Ds




    #######################################################################################
    #
    def getFunctionForView(self, view, declaration_only=False):

        view_name    = view.view

        f_name       = 'func__'+view_name
        f_body       = view.algorithm
        f_type       = 'auto'

        f_parameters = 'unsigned int __slot'
        for o in view.origins:
            f_parameters += ',\n\t\tconst '+self.Types[o]+' '+o

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
                print("[pRDF] ** WARNING ** Non-boolean return type for  ", f_name)
        
        return fCode




    #######################################################################################
    # f_autocppcode : full function implementation with auto return type
    #
    def returnType(self, f_name, f_autocppcode):

        ROOT.gInterpreter.Declare(f_autocppcode)
        getTypeNameF = "auto %s_typestring=ROOT::Internal::RDF::TypeID2TypeName(typeid(ROOT::TypeTraits::CallableTraits<decltype(%s)>::ret_type));" % (f_name, f_name)
        ROOT.gInterpreter.ProcessLine(getTypeNameF)
        fretType = getattr(ROOT, "%s_typestring" % f_name)

        return fretType





    #######################################################################################
    #
    def Compile_cpp_file(self, cpp_file_name="rdf_processor.C"):

        so_file_name = cpp_file_name.replace('.C', '.so')
        
        os.system("rm %s" % so_file_name)

        print("Compiling with: g++ -fPIC -Wall -O0 %s $(root-config --libs --cflags)  -o %s --shared -I..  -L. -I. " % (cpp_file_name, so_file_name))
        os.system(            "g++ -fPIC -Wall -O0 %s $(root-config --libs --cflags)  -o %s --shared -I..  -L. -I. " % (cpp_file_name, so_file_name))

        return





    #######################################################################################
    # TEMPORARY function - TO BE REMOVED

    def RunTest(self):

        print("\n===== RunTest - start =================================\n")


        ### Load library into ROOT

        print("Loading rdf_processor.so")
        ROOT.gSystem.Load("rdf_processor.so")

        ### Make the interpreter aware of the processor delaration (#include - equivalent / needed by the getattr call in the CastToNode function)

        ROOT.gInterpreter.Declare('Result eventProcessor_nail(RNode rdf, int nThreads);')


        ### Define service functions used by the Processor (through lambda function definition)
        ### CatToRNode function is not strictly necessary

        #        def CastToRNode(node): return ROOT.RDF.AsRNode(node)

        
        ### The attribute retrieved here allows the configuration of the rdf (passed as argument) as the Processor defined
        #        fu = (lambda rdf: getattr(ROOT, "eventProcessor_nail")(CastToRNode(rdf), 0))

        fu = (lambda rdf: getattr(ROOT, "eventProcessor_nail")(ROOT.RDF.AsRNode(rdf), 0))

        print("---------> fu = ", fu)

        print("\n===== RunTest - end  =================================\n")

        return fu




    

    #######################################################################################
    #
    def GetProcessor(self):

        print("\n===== GetProcessor() =================================\n")

        ### Load library into ROOT
        print("Loading rdf_processor.so")
        ROOT.gSystem.Load("rdf_processor.so")

        ### Make the interpreter aware of the processor delaration (#include - equivalent / needed by the getattr call in the CastToNode function)
        ROOT.gInterpreter.Declare('Result eventProcessor_nail(RNode rdf, int nThreads);')

        ### The attribute retrieved here allows the configuration of the rdf (passed as argument) as the Processor defined
        processor_function = (lambda rdf: getattr(ROOT, "eventProcessor_nail")(ROOT.RDF.AsRNode(rdf), 0))

        return processor_function




    #######################################################################################
    #
    def RunProcessor(self, translate=False):

        ### NOT ELEGANT - TO BE FIXED
        self.GenerateRDFcpp(translate=translate)

        self.Compile_cpp_file()

        _processor = self.GetProcessor()

        _rdf = ROOT.RDataFrame(self.tree_name, self.file_name)

        ## This call returns an object "Result" (defined in the autogen.C file) which contains both the configured rdfs (one per selection node) and the resulting histos
        _result = _processor(_rdf)

        print("-------------- STEP 7 ")

        print(" result = ", _result)

        print("-------------- STEP 8 ")

        # The actual loop is run when the first histo is accessed

        cc = ROOT.TCanvas()

        with TFile.Open("f.root", "recreate") as rootFile:

            for o in _result.histos:

                print(" histo   ", o.GetName(), "  ->  ", o)

                rootFile.WriteObject(o.GetValue(), o.GetName())
                
                o.Draw()
                cc.SaveAs("out-%s.png" % (o.GetName()))


        return

    



###########################################################################
#    
###########################################################################

class codeSnippets:

    def __init__(self):
        print("[cS] __init__  ")



    def cpp_includes(self):

        text = '''
#include <vector>
#include <map>
#include <utility>

#include <Math/VectorUtil.h>
#include <ROOT/RVec.hxx>
#include "Math/Vector4D.h"
#include <ROOT/RDataFrame.hxx>
#include "src/helpers.h"

#define MemberMap(vector,member) Map(vector,[](auto x){return x.member;})
#define P4DELTAR ROOT::Math::VectorUtil::DeltaR<ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>,ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>> 
//ROOT::Math::PtEtaPhiMVector,ROOT::Math::PtEtaPhiMVector> 

using namespace std;

#ifndef NAILSTUFF
#define NAILSTUFF

using RNode = ROOT::RDF::RNode;
struct Result {
  Result() {}
  // Result(RNode  rdf_) {rdf[""]=rdf_;}
  std::map<std::string,RNode> rdf;
  ROOT::RDF::RResultPtr<TH1D> histo;
  std::vector<ROOT::RDF::RResultPtr<TH1D>> histos;
  std::map<std::string,std::vector<ROOT::RDF::RResultPtr<TH1D> > > histosOutSplit;
};

// Not used right now (ROOT.RDF.AsRNode is used instead) !!
//template <typename T>
//class NodeCaster {
//public:
//  static ROOT::RDF::RNode Cast(T rdf)
//  {
//    return ROOT::RDF::RNode(rdf);
//  }
//};

#endif

'''
        return text



    def histos_function_declaration(self):

        text = '''
std::vector<ROOT::RDF::RResultPtr<TH1D>> histosWithSelection_eventProcessor(std::map<std::string,RNode> &rdf, std::string sel="1");

'''
        return text

#    def eventProcessor_begin(self):
#
#        text = '''
#Result eventProcessor_nail(RNode rdf,int nThreads,std::map<std::string,std::string> outSplit=std::map<std::string,std::string>()) {
#
#  Result r;
#
#  if (nThreads > 0) { ROOT::EnableImplicitMT(nThreads); };
#
#'''
#        return text



    def eventProcessor_begin(self):

        text = '''
Result eventProcessor_nail(RNode rdf,int nThreads) {

  Result r;

  if (nThreads > 0) { ROOT::EnableImplicitMT(nThreads); };

'''
        return text



    def eventProcessor_end(self):

        text = '''
  return r;
}

'''
        return text



    def eventProcessor_extra(self):

        text = '''
  r.histos[0]->SetXTitle("x-label");

'''
        return text






