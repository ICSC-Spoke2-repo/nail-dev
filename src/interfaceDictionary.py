###################################################################################
#
# REWRITTEN: interfaceDictionary merged with translator in a single class
#  OK
#
###################################################################################
#
#  Based on NAIL/nanoAOD format (source/description):
#
#     Format of a variable: variable_feature[index]   (e.g. Muon_pt or Electron_eta[1])
#
#     - variable CANNOT contain "_"
#     - feature  can contain multiple "_"
#     - index is frequently omissed (due to automatic internal loop)
#     - a token ending with a "(" is a function/method, NOT a variable/feature
#
#     Types of codification for variables:
#
#     - Scalar:     no index, no feature         e.g. RunNumber
#     - Vector:        INDEX, no feature         e.g. MCweights[i]
#     - Object:     no index,    FEATURE         e.g. MET_x, MET_y
#     - Collection:    INDEX,    FEATURE         e.e. electron_pT[i]
#
#     Translation (i.e. dictionary) is relevant for variables and features *ONLY*
#
#     - index information managed in the convert method only!
#
#     Layout for counter variables (e.g. "nMuon") is hardcoded - for now - in the class initialization (but included in the saved infos)
#
#  NOTEs : VARIABLE_FEATURE_SEPARATOR is set when set_base_format("object", ...) is called !
#
#
#
#
#  Additional features:
#
#     Constants: during conversion a constant is translated with its actual value
#     NOTES: so far the constants are stored in the "vars" dictionary --> this might need to be split in a dedicated dictionary ...
#
#     Format of a constant: const_feature   (e.g. const_Muon_mass -> 0.1056f)
#
#     - const    identifier (hardcoded to "const" for now) 
#     - feature  name of the defined constant
#     - index is not considered
#
###################################################################################

import json

class interfaceDictionary:
    def __init__(self, interfaceName = "", db_file = ""):

        self.name              = interfaceName
        self.comment           = ""

        self.CONVERSION_ERROR  = "CONVERSION_ERROR"
        
        self.VARIABLE_label    = "VARIABLE"
        self.FEATURE_label     = "FEATURE"
        self.INDEX_label       = "INDEX"

        self.CONSTANT_label    = "const"

        self.V_F_SEPARATOR_BASE   = "_"
        self.V_F_SEPARATOR_TARGET = "_"
        
        self.scalar_type       = "scalar"
        self.vector_type       = "vector"
        self.object_type       = "object"
        self.collection_type   = "collection"

        self.counter_base_layout = 'n'+self.VARIABLE_label

        self.types             = (self.scalar_type, self.vector_type, self.object_type, self.collection_type)
        self.typesWithIndex    = (                  self.vector_type,                   self.collection_type)
        self.typesWithFeature  = (                                    self.object_type, self.collection_type)

        self.DB                   = {}

        self.DB["base_formats"]   = {}
        self.DB["target_formats"] = {}
        self.DB["vars"]           = {}

        self.DB["vars"][self.CONSTANT_label] = {}


        for t in self.types:
            self.DB["base_formats"][t]   = self.source_format(t)
            self.DB["target_formats"][t] = "NOT_SET"

        self.DB["counter_base_layout"] = self.counter_base_layout

        self.feature_first = True
        self.set_feature_index_order()


        
        if db_file != "":
            self.load_DB(db_file)


        if interfaceName != "":
            if interfaceName != self.name:
                print("Interface renamed :  ", self.name, "  ->  ", interfaceName)
            self.name = interfaceName


        print(f"{'[ interfaceDictionary ] object created : ' : <45}{self.name}")


    ###        
    def __str__(self):
        return (f"{'interfaceDictionary object - '}{self.name}")


    ##################################
    # Basic features

    ###
    def set_comment(self, comment_text):     self.comment = comment_text



    ##################################
    # info_dictionary 

    ###
    def get_info_dictionary(self):

        info_dictionary                     = {}

        info_dictionary["info"]             = {}
        info_dictionary["info"]["name"]     = self.name
        info_dictionary["info"]["type"]     = str(type(self))
        info_dictionary["info"]["comment"]  = self.comment

        info_dictionary["VARIABLE_label"]   = self.VARIABLE_label
        info_dictionary["FEATURE_label"]    = self.FEATURE_label
        info_dictionary["INDEX_label"]      = self.INDEX_label

        info_dictionary["CONSTANT_label"]   = self.CONSTANT_label

        info_dictionary["scalar_type"]      = self.scalar_type
        info_dictionary["vector_type"]      = self.vector_type
        info_dictionary["object_type"]      = self.object_type
        info_dictionary["collection_type"]  = self.collection_type

        info_dictionary["types"]            = self.types
        info_dictionary["typesWithIndex"]   = self.typesWithIndex
        info_dictionary["typesWithFeature"] = self.typesWithFeature

        info_dictionary["DB"]               = self.DB

        print(f"{'[ interfaceDictionary ] info_dictionary updated'}")
        print(info_dictionary, "\n")

        return info_dictionary
            

    ###
    def configure_from_info_dictionary(self, info_dictionary = {}):

        if (len(info_dictionary) == 0):
            print("[ interfaceDictionary ]  ERROR: info_dictionary is empty!!! ")
            return

        self.name             = info_dictionary["info"]["name"]
        self.comment          = info_dictionary["info"]["comment"]

        self.VARIABLE_label   = info_dictionary["VARIABLE_label"]
        self.FEATURE_label    = info_dictionary["FEATURE_label"]
        self.INDEX_label      = info_dictionary["INDEX_label"]

        self.CONSTANT_label   = info_dictionary["CONSTANT_label"]

        self.scalar_type      = info_dictionary["scalar_type"]
        self.vector_type      = info_dictionary["vector_type"]
        self.object_type      = info_dictionary["object_type"]
        self.collection_type  = info_dictionary["collection_type"]

        self.types            = info_dictionary["types"]
        self.typesWithIndex   = info_dictionary["typesWithIndex"]
        self.typesWithFeature = info_dictionary["typesWithFeature"]

        self.DB               = info_dictionary["DB"]

        self.set_variable_feature_separator("base")
        self.set_variable_feature_separator("target")
        self.set_feature_index_order()


        print(f"{'[ interfaceDictionary ] Object configured from info_dictionary'}")

        return




    ##################################
    # Save & Load

    ###
    def save_DB(self, dbFileName):

        info_dictionary = self.get_info_dictionary()

        with open(dbFileName, "w") as file:
            json.dump(info_dictionary, file)
        print(f"{'[ interfaceDictionary ] object saved to : ' : <45}{dbFileName}")
        return


    ###
    def load_DB(self, dbFileName):
        info_dictionary = {}
        with open(dbFileName) as file:
            info_dictionary = json.load(file)
        print("** DB loaded from file ", dbFileName)

        print(f"{'[ interfaceDictionary ] info_dictionary loaded from : ' : <45}{dbFileName}")
        
        self.configure_from_info_dictionary(info_dictionary)
        
        self.print_summary()

        return
    


    ##################################
    # Placeholder for input-format-specific configurations

    ###
    def configureInterface(self):
        print(f"{'[ interfaceDictionary ] PLACEHOLDER for input-format-specific configurations'}")
        return



    ##################################
    #  Utilities for variables

    ###
    def split_name_feat(self, varString, separator):

        if varString.find(" ") != -1:
            print(f"{'[ interfaceDictionary ] ERROR split_name_feat : ' : <45}{' string contains blank spaces'}")
            return "ERROR_split_name_feat"

        separator_pos = varString.find(separator)

        if separator_pos == 0:
            print(f"{'[ interfaceDictionary ] ERROR split_name_feat : ' : <45}{' string starting with an underscore'}")
            return "ERROR_split_name_feat"

        if separator_pos != -1:
            v_name = varString[0:separator_pos]
            v_feat = varString[(separator_pos+len(separator)):]
        else:
            v_name = varString
            v_feat = 'NONE'

        return v_name, v_feat



    def split_name_feat_base(  self, varString):    return self.split_name_feat(varString, self.V_F_SEPARATOR_BASE)
    def split_name_feat_target(self, varString):    return self.split_name_feat(varString, self.V_F_SEPARATOR_TARGET)



        

    ###
    def is_defined(self, var_name, var_feat = ""):

        if var_feat == "":
            v_name, v_feat = self.split_name_feat_base(var_name)
        else:
            v_name = var_name
            v_feat = var_feat

        if not v_name in self.DB["vars"]:
            return False

        if v_feat != 'NONE':
            if not self.has_this_feature(v_name, v_feat):
               return False

        return True


    ###
    def has_this_feature(self, var_name, feature_name):    return (feature_name in self.DB["vars"][var_name])   # Search by source-name 


    ###
    def is_indexed(self, var_name):
        v_name, v_feat = self.split_name_feat_base(var_name)
        _counter_name  = self.get_counter_name_for(v_name)
        if self.is_defined(_counter_name):
            return True
        return False

        
    

    ###
    def type_if(self, has_feature, has_index):
        if   not has_feature and not has_index :    return self.scalar_type
        elif not has_feature and     has_index :    return self.vector_type
        elif     has_feature and not has_index :    return self.object_type
        elif     has_feature and     has_index :    return self.collection_type
        return


    ###
    def get_counter_name_for(self, var_name):
        return (self.counter_base_layout).replace(self.VARIABLE_label, var_name)


    ###
    def is_counter_defined_for(self, var_name):
        return self.is_defined(self.get_counter_name_for(var_name))
    
    

    ##################################
    #  Utilities for DB building


    ##################################
    #  Adding new variables and/or features to the db
    #
    # Baseline idea: addition to the analysis interface (dictionary) of variables defined during the data manipulation (e.g. event loop).
    # The name used will be just the one defined, since - by definition - this variable should not be present in the target data ntuple.
    # (Otherwise this should have been added to the interface definition upstream!)
    #
    # Index not searched for!
    #


    ###
    def add_variable(self, var_origin, var_target=""):

        if self.is_defined(var_origin):
            print(f"{'[ interfaceDictionary ] ERROR add_variable : ' : <45}{' trying to add a variable already defined in the dictionary  '}{var_origin}")
            return


        origin_name, origin_feat = self.split_name_feat_base(  var_origin)

        if var_target == "":
            var_target  = var_origin
            target_name = origin_name
            target_feat = origin_feat
            #            target_name, target_feat = self.split_name_feat_base(var_target)
        else:
            target_name, target_feat = self.split_name_feat_target(var_target)


        if (origin_feat != 'NONE') and (target_feat == 'NONE'):
            print(f"{'[ interfaceDictionary ] ERROR add_variable : ' : <45}{' origin has feature while target has none  '}{origin_feat}{' / '}{target_feat}")
            return

        if (origin_feat == 'NONE') and (target_feat != 'NONE'):
            print(f"{'[ interfaceDictionary ] ERROR add_variable : ' : <45}{' origin has no feature while target has    '}{origin_feat}{' / '}{target_feat}")
            return

        if not self.is_defined(origin_name):
            self.DB["vars"][origin_name] = {origin_name:target_name}

        # The check in the else field doesn't work when adding features for variable already defined with origin_name != target_name !!!
        #        else:
        #            if target_name != self.DB["vars"][origin_name][origin_name]:
        #                from_name = self.DB["vars"][origin_name][origin_name]
        #                print(f"{'[ interfaceDictionary ] ERROR add_variable : ' : <45}{' trying to redefine target variable name  '}{from_name}{' / '}{target_name}")
        #                return

        if origin_feat != 'NONE':
            self.add_feature(origin_name, origin_feat, target_feat)

        return


    ###
    def add_feature(self, var_origin, feat_origin, feat_target=""):

        if not self.is_defined(var_origin):
            print(f"{'[ interfaceDictionary ] ERROR add_feature : ' : <45}{' variable name not defined  '}{var_origin}")
            return

        if self.has_this_feature(var_origin, feat_origin):
            print(f"{'[ interfaceDictionary ] ERROR add_feature : ' : <45}{' feature  '}{feat_origin}{'  already defined for variable  '}{var_origin}")
            return

        if feat_target == "":
            feat_target = feat_origin
        self.DB["vars"][var_origin][feat_origin] = feat_target

        return



    ###
    #    def add_constant(self, const_prefix, const_name, const_value):
    def add_constant(self, constString, const_value):

        const_prefix, const_name = self.split_name_feat_base(constString)

        if const_prefix != self.CONSTANT_label:
            print(f"{'[ interfaceDictionary ] ERROR add_constant : ' : <45}{' wrong constant prefix  '}{const_prefix}{'  (expected  '}{self.CONSTANT_label}{' )'}")
            return
        
        self.add_feature(const_prefix, const_name, const_value)
        return



    ##################################
    # Utilities for Format

    ###
    def source_format(self, vType):
        source_format = self.VARIABLE_label
        if vType in self.typesWithFeature:      source_format+=self.V_F_SEPARATOR_BASE+self.FEATURE_label
        if vType in self.typesWithIndex:        source_format+='['+self.INDEX_label+']'
        return source_format


    ###
    def set_format(self, f_type, f_string, side):
        if   (side != "base" and side != "target"):                                        print("** WRONG side : ", side, "  ('base' or 'target')")
        elif not f_type in self.types:                                                     print("** WRONG format type set : ", f_type)
        elif not self.VARIABLE_label in f_string:                                          print("** "+side+" format(", f_string, ") - ERROR : missing ", self.VARIABLE_label, " keyword in the format string.")
        elif (f_type in self.typesWithIndex   and  not self.INDEX_label   in f_string):    print("** "+side+" format(", f_string, ") - ERROR : missing ", self.INDEX_label,    " keyword in the format string.")
        elif (f_type in self.typesWithFeature and  not self.FEATURE_label in f_string):    print("** "+side+" format(", f_string, ") - ERROR : missing ", self.FEATURE_label,  " keyword in the format string.")
        else:
            self.DB[side+"_formats"][f_type] = f_string
            print(f"{'[ interfaceDictionary ] Set format : ' : <45}{side: <10}{'  format for  '}{f_type : <12}{'  variables  =  '}{f_string}")

        if (f_type == "object"):                             self.set_variable_feature_separator(side)
        if (f_type == "collection") and (side == "base"):    self.set_feature_index_order()

        return

    ###
    def set_base_format(  self, f_type, f_string):    self.set_format(f_type, f_string, "base")
    def set_target_format(self, f_type, f_string):    self.set_format(f_type, f_string, "target")



    def set_variable_feature_separator(self, side):

        _f_string = self.DB[side+"_formats"]["object"]

        if side == "base":
            self.V_F_SEPARATOR_BASE   = _f_string.replace(self.VARIABLE_label, '').replace(self.FEATURE_label, '')
            print(f"{'[ interfaceDictionary ] Set variable-feature separator (base): ' : <45}{'*'}{self.V_F_SEPARATOR_BASE}{'*'}")
        elif side == "target":
            self.V_F_SEPARATOR_TARGET = _f_string.replace(self.VARIABLE_label, '').replace(self.FEATURE_label, '')
            print(f"{'[ interfaceDictionary ] Set variable-feature separator (target): ' : <45}{'*'}{self.V_F_SEPARATOR_TARGET}{'*'}")
                
        return



    def set_feature_index_order(self):

        _f_string = self.DB["base_formats"]["collection"]
        
        if _f_string.find("INDEX") < _f_string.find("FEATURE"):
            self.feature_first = False
            print(f"{'[ interfaceDictionary ] Set feature-index order : ' : <45}{' index - feature '}")
        else:
            self.feature_first = True
            print(f"{'[ interfaceDictionary ] Set feature-index order : ' : <45}{' feature - index '}")
        return



    ##################################
    # Utilities for dictionary extraction

    ###
    def dictionary_for(self, _var):
        # All variables requested
        if _var == "all":      return self.DB["vars"]

        # Variable name requested
        if self.is_defined(_var):    return self.DB["vars"][_var]

        print(" ERROR  -  variable ", _var, "  not defined!")
        return {}


    ### Feature SOURCE name
    def list_of_features_for(self, _var):
        if not self.is_defined(_var):    return []
        d_var = self.dictionary_for(_var)
        return [f for f in d_var if f != _var]


    ### Number of features for variable
    def number_of_features(self, _var):
        return len(self.list_of_features_for(_var))



    ##################################
    #  Print & Summary

    ###
    def print_interface_info(self):
        print(f"{'[ interfaceDictionary ] Interface info : ' : <45}")
        #        print("** Interface info")
        print("name             -->  ", self.name)
        print("comment          -->  ", self.comment)
        return

    ###
    def print_supported_formats(self):
        print(f"{'[ interfaceDictionary ] Supported formats : ' : <45}")
        #        print("** Supported Formats")
        print(" Type                Source format              -->   Target Format ")
        for vType in self.types:
            print(vType.ljust(20), self.DB["base_formats"][vType].ljust(24), "  -->  ", self.DB["target_formats"][vType])
        return


    ###
    def print_target_formats(self):
        print(f"{'[ interfaceDictionary ] Target formats : ' : <45}")
        #        print("** Target Formats")
        for tf in self.DB["target_formats"]:
            print(tf.ljust(20), "-->  ", self.DB["target_formats"][tf].ljust(20))
        return


    ###
    def print_list_of_variables(self):
        print(f"{'[ interfaceDictionary ] List of variables : ' : <45}")
        for v in self.DB["vars"]:
            if v != self.CONSTANT_label:
                print(v.ljust(20), "-->  ", self.DB["vars"][v][v].ljust(20))
        return


    ###
    def print_summary(self):
        print(f"{'[ interfaceDictionary ] Summary : ' : <45}")
        self.print_interface_info()
        self.print_supported_formats()
        return


    ###
    def print_dictionary(self, _name = "all"):
        print(f"{'[ interfaceDictionary ] Dictionary for  : ' : <45}{_name}")
        #        print(">> Dictionary for  ", _name)
        _d = self.dictionary_for(_name)
        for v in _d:     print(v.ljust(20), "-->", _d[v])
        return



    ##################################
    # Build variable name according to specified format (base or target)

    ###
    def build_with_target_format(self, _Var, _Feat, _Ind):      return self._build("target_formats", _Var, _Feat, _Ind)
    def build_with_base_format(  self, _Var, _Feat, _Ind):      return self._build("base_formats",   _Var, _Feat, _Ind)


    ###
    def _build(self, _format, _Var, _Feat, _Ind):

        tVar  = _Var
        tFeat = ""
        tInd  = ""

        _has_feature = False
        _has_index   = False

        # FEATURE
        if not _Feat == "NONE":
            tFeat        = _Feat
            _has_feature = True

        # INDEX
        if not ( (_Ind  == "NONE") or (_Ind  == "SKIP") ):
            tInd         = _Ind
            _has_index   = True

        typeVar = self.type_if(_has_feature, _has_index)
            
        return (self.DB[_format][typeVar].replace(self.VARIABLE_label, tVar).replace(self.INDEX_label, tInd).replace(self.FEATURE_label, tFeat))

        

    ##################################
    # Conversion from source to target format

    def convert(self, sVar, sFeat, sInd = ""):

        ### CONSTANT ###
        if sVar == self.CONSTANT_label:

            if not self.is_defined(sVar):
                print(f"{'[ interfaceDictionary ] convert : ' : <45}{'ERROR : no constant defined'}")
                return self.CONVERSION_ERROR

            if (not self.has_this_feature(sVar, sFeat)):
                print(f"{'[ interfaceDictionary ] convert : ' : <45}{'ERROR :  feature  '}{sFeat}{'  is NOT defined'}")
                return self.CONVERSION_ERROR

            return self.DB["vars"][sVar][sFeat]


        ### VARIABLE ###
        if not self.is_defined(sVar):
            print(f"{'[ interfaceDictionary ] convert : ' : <45}{'ERROR :  variable  '}{sVar}{'  is NOT defined'}")
            return self.CONVERSION_ERROR

        tVar  = self.DB["vars"][sVar][sVar]
        tFeat = sFeat

        if (sFeat != "NONE"):
            if (not self.has_this_feature(sVar, sFeat)):
                print(f"{'[ interfaceDictionary ] convert : ' : <45}{'ERROR :  variable  '}{sVar}{'  has NO feature  '}{sFeat}")
                return self.CONVERSION_ERROR
            else:
                tFeat = self.DB["vars"][sVar][sFeat]

        tInd  = sInd

        return self.build_with_target_format(tVar, tFeat, tInd)




    ##################################
    # Conversion from TARGET to SOURCE format (i.e. the other way round)

    def target2source(self, tString):


        tVar, tFeat = self.split_name_feat_target(tString)

        sVar  = ""
        sFeat = ""


        for v_name in self.DB["vars"]:

            if v_name == "const":
                continue

            if tVar == self.DB["vars"][v_name][v_name]:
                sVar = v_name
                break

        if sVar != "":
            for v_feat in self.DB["vars"][sVar]:

                if tFeat == self.DB["vars"][sVar][v_feat]:
                    sFeat = v_feat
                    break


        if sVar == "":
            #            print(f"{'[ interfaceDictionary ] target2source : ' : <45}{'source vaiable not found'}")
            return tString

        if (sFeat == "") and (tFeat != ""):
            #            print(f"{'[ interfaceDictionary ] target2source : ' : <45}{'source fature not found'}")
            return tString

        return self.build_with_base_format(sVar, sFeat, "NONE")





    ##################################
    # String handling tools

    ###
    def get_token(self, targetString, underscore_allowed = True):
        sToken     = ""
        sToken_pos = 0

        for c in targetString:

            if ((c.isalnum()) or (underscore_allowed and (c == '_'))):
                sToken += c
            else:
                if sToken == "":
                    sToken_pos += 1
                else:
                    break

        return sToken, sToken_pos


    ###
    def find_closed_sb(self, targetString):
        open_sb       = 1
        closed_sb_pos = -1

        for i in range(0, len(targetString)):
            c = targetString[i]
            if   c == "[":  open_sb += 1
            elif c == "]":  open_sb -= 1

            if open_sb == 0:
                closed_sb_pos = i
                break

        return closed_sb_pos


    ###
    # Finding the first token which corresponds to one of the variables in the dictionary
    def find_first_var(self, targetString):
        result = "NONE"
        vPos   = -1

        stringShift = 0

        while stringShift < len(targetString):

            t1, t1_pos = self.get_token(targetString[stringShift:], underscore_allowed=False)

            if self.is_defined(t1):
                return t1, (stringShift+t1_pos)
            else:
                stringShift += (t1_pos + len(t1))

        return result, vPos



    def get_first_var(self, targetString):
        
        # Find first variable (searcging among dictionary's keys)
        varName, string_shift = self.find_first_var(inputString)

        return varName
    

    ###
    # This assumes string starting with "_" (NAIL/nanoAOD specific)
    # Not searched in the dictionary: if a feature is found, its presence in the variable's dictionary will be checked in the main function
    def find_feature(self, targetString):
        result = "NONE"

        if (len(targetString) < 2) or (targetString[0] != self.V_F_SEPARATOR_BASE):
            return result

        t1, t1_pos = self.get_token(targetString[len(self.V_F_SEPARATOR_BASE):], underscore_allowed=True)

        if t1_pos != 0:
            self.report_error("Wrong-formed feature filed  "+t1, targetString)

        # Protection against function call!
        l = len(t1)
        if (t1 != "") and (targetString[l+1:l+2] != "("):
            result = t1

        return result



    ###
    # This assumes string starting with "[" and looks for the corresponding "]"
    def find_index(self, targetString):
        result = "NONE"

        if not (targetString[0:1] == '['):
            return result

        index_begin = 1
        index_end   = index_begin + self.find_closed_sb(targetString[index_begin:])

        if (index_end > index_begin):
            result = targetString[index_begin:index_end]
        elif (index_end == index_begin):
            result = "SKIP"

        return result





    ##################################
    #  Methods for the string translation

    ###
    # Note: index field is usually not present in case of automatic internal index loop - it is used only for explicit picking (re-definition) of one element of vector/collection
    def translate_string(self, inputString):

        #        if not self.do_translate:       return inputString
        if inputString == "":           return inputString

        sHeader     = ""
        varName     = "NONE"
        varFeature  = "NONE"
        varIndex    = "NONE"
        sFooter     = ""


        # Find first variable (searcging among dictionary's keys)
        varName, string_shift = self.find_first_var(inputString)


        # Exit condition
        if varName == "NONE":
            return inputString


        # Extract the header
        sHeader      =  inputString[0:string_shift]
        string_shift += len(varName)



        ### Search for feature is performed before/after the search for index, according to the value of the self.feature_first variable
        if self.feature_first:

            varFeature = self.find_feature(inputString[string_shift:])
            if varFeature != "NONE":    string_shift += (len(varFeature)+len(self.V_F_SEPARATOR_BASE))



        # Search for an index field
        tempIndex = self.find_index(inputString[string_shift:])

        if tempIndex != "NONE":

            if tempIndex == "SKIP":    string_shift +=  2
            else:                      string_shift += (2+len(tempIndex))

            # Translate index field - Recursive application
            varIndex = self.translate_string(tempIndex)



        ### Search for feature is performed before/after the search for index, according to the value of the self.feature_first variable
        if not self.feature_first:

            varFeature = self.find_feature(inputString[string_shift:])
            if varFeature != "NONE":    string_shift += (len(varFeature)+len(self.V_F_SEPARATOR_BASE))


            


        # Select the footer - Recursive application
        sFooter = self.translate_string(inputString[string_shift:])



        # Build the translated string using the method specific of the loaded interface
        outputString = sHeader+self.convert(varName, varFeature, varIndex)+sFooter


        return outputString




    ##################################
    #  Methods for the extraction of the list of variables (inputs)

    def get_var_list(self, inputString):

        varList = []
        
        if inputString == "":
            return varList

        varName     = "NONE"
        varFeature  = "NONE"


        # Find first variable (looping over dictionaries' keys)
        varName, string_shift = self.find_first_var(inputString)


        # Exit condition
        if varName == "NONE":
            return varList


        # Extract the header
        string_shift += len(varName)


        # Search for a feature
        varFeature = self.find_feature(inputString[string_shift:])

        if varFeature != "NONE":

            # Check if the feature found is present in the dictionary of the variable
            if not self.has_this_feature(varName, varFeature):
                print(f"{'[ interfaceDictionary ] get_var_list :  ' : <45}{'WARNING : feature  '}{varFeature}{'  NOT in the dictionary for variable  '}{varName}")

            string_shift += (len(varFeature)+1)


        # Add found variable to the list
        varList = [self.build_with_base_format(varName, varFeature, "NONE")]


        # Search for an index field
        tempIndex = self.find_index(inputString[string_shift:])

        if tempIndex != "NONE":

            if tempIndex == "SKIP":     string_shift += 2
            else:                       string_shift += (len(tempIndex)+2)

            # Add variables names found in the index field - Recursive application
            varList += self.get_var_list(tempIndex)


        # Select the footer - Recursive application
        varList += self.get_var_list(inputString[string_shift:])


        # Remove duplicates
        varList = list(dict.fromkeys(varList))


        return varList







    

    ##################
    # Notes:
    #
    # Built-in hash() function in Pyton is "salted" by a random mumber (unique per execution)
    # (see: https://docs.python.org/3/reference/datamodel.html#object.__hash__ )
    #    def hash_dict(self):
    #        return hash(str(self.OBJs_dict))
    #
    ##################
    
