import json
import os
import graphviz
import hashlib
import copy


###   InfoView   ##############################################################
#
#  id_code: the digest for a view depends on the graph configuration - i.e. depends to
#           the digests of the its origins - so the digest must be evaluated by the graph object
#           (i.e. it is not an information self-contained in the view/node
#
#           id_code = MD5(view_name, view_algorithm, [view_origins])    (N.B: to be evaluated if the list of origins should be sorted )
#
#
#  status:  available   View already evaluated, info available
#           active      View changed (origins and/or algorithm) - it needs to be re-evaluated
#           undefined   Status not evaluated: id_code of the origins need to be provided in order
#                       to evaluate the id_code of the view (and then check if the corresponding
#                       info is already available)
#
#    Note on active status:
#         if the view has no origins and transformation, the active status should be
#         interpreted as "input information to the next transformation has changed"
#
#
#  Type of view    | Algorithm | Origins | Requirements    | Notes
# --------------------------------------------------------------------------------------------------------------
#  Transformation  |     Y     |    Y    |    Y/N          |
#  Aggregation     |     N     |    Y    |     ? (tbc ...) |
#  Constant        |     Y     |    N    |     -           | (Algorithm is returning the value of the constant)
#  Input           |    Y/N    |    N    |     -           | (A Constant is - of course - an Input as well)
# --------------------------------------------------------------------------------------------------------------
#
#

class InfoView:
    def __init__(self, infoName = "NONE"):

        self.view              = infoName
        self.algorithm         = 'NONE'
        self.origins           = []
        self.requirements      = []
        self.id_code           = 0
        self.status            = 'undefined'

        self.fetching_info     = {}



    def __str__(self):
        return f"{self.view:<20} <-- {self.algorithm:<20} -- {self.origins}"


    ################################################
    # info_dictionary -> is NOW a transient variable!!

    # Note if the statements inside update_info() are kept in the __init__(),
    # any assignment to self.algorithm is *NOT* propagated to the dictionary, since
    # the variable referenced by self.algorithm is changed (i.e. a new one is instantiated
    # and the old one "NONE" remains alive since it is referenced by self.info_dictionary["algorithm"]
    

    def get_info_dictionary(self):

        info_dictionary                      = {}
        info_dictionary["view"]              = self.view
        info_dictionary["algorithm"]         = self.algorithm
        info_dictionary["origins"]           = self.origins
        info_dictionary["requirements"]      = self.requirements
        info_dictionary["status"]            = self.status
        info_dictionary["id_code"]           = self.id_code

        info_dictionary["fetching_info"]     = copy.deepcopy(self.fetching_info)

        return info_dictionary


    def configure_from_info_dictionary(self, info_dictionary = {}):

        if (len(info_dictionary) == 0):
            print("[ InfoView ]  ERROR: info_dictionary is empty!!! ")
            return

        self.view          = info_dictionary["view"]
        self.algorithm     = info_dictionary["algorithm"]
        self.origins       = copy.deepcopy(info_dictionary["origins"])
        self.requirements  = copy.deepcopy(info_dictionary["requirements"])
        self.status        = info_dictionary["status"]
        self.id_code       = info_dictionary["id_code"]

        self.fetching_info = copy.deepcopy(info_dictionary["fetching_info"])

        return
            



    ################################################
    # Save & Load

    def save_to_file(self, fileName = "view.json"):
        info_dictionary = self.get_info_dictionary();
        with open(fileName, "w") as file:
            json.dump(info_dictionary, file)
        return


    def load_from_file(self, dbFileName):
        info_dictionary = {}
        with open(dbFileName) as file:
            info_dictionary = json.load(file)
        print("[ InfoView ]  View loaded from file :  ", dbFileName)

        self.configure_from_info_dictionary(info_dictionary)
        
        self.print_view()

        return



    ################################################
    # Building tools

    def add_origin(self, iv):                          self.origins.append(iv.view)
    def add_origins(self, _origins_list):              self.origins.extend(_origins_list)

    def add_requirement(self, iv):                     self.requirements.append(iv.view)
    def add_requirements(self, _requirements_list):    self.requirements.extend(_requirements_list)


    def set_algorithm(self, _algoName):       self.algorithm   = _algoName
    def set_id_code(self,   _code):           self.id_code     = _code
    def set_status(self,    _status):         self.status      = _status

    def set_active(self):                     self.set_status('active')
    def set_available(self):                  self.set_status('available')


    ################################################
    # Tests (is/has)

    def is_active(self):            return (self.status == 'active'   )
    def is_available(self):         return (self.status == 'available')

    def has_origin(self):           return (len(self.origins)      > 0      )
    def has_requirement(self):      return (len(self.requirements) > 0      )
    def has_transformation(self):   return (self.algorithm         != "NONE")
    def has_id_code(self):          return (self.id_code           != 0     )

    def has_fetching_info(self):    return (len(self.fetching_info) > 0)

    def is_transformation(self):    return (    self.has_origin() and      self.has_transformation() )
    def is_aggregation(self):       return (    self.has_origin() and (not self.has_transformation()))
    def is_input(self):             return (not self.has_origin() )
    def is_constant(self):          return (not self.has_origin() and      self.has_transformation() )   # A constant is - of course - an input as well



    ################################################
    # Access

    def get_sources(self):
        return self.origins + self.requirements



    ################################################
    # Tools for printing

    def print_view(self):
        info_dictionary = self.get_info_dictionary()
        print(info_dictionary)
        for v in info_dictionary:
            print(v.ljust(20), "  :  ", info_dictionary[v])
        return








###   InfoGraph   ##############################################################
#
# REDESIGN sub-graph extraction according to "activation state"
#
# - set (and propagate activation) - IMPLEMENTED (forward only - so far)
# - extract sub-graph according to activation status of the views
# - propagate activation:
#    - forward (downstream)
#    - backward (upstream)
#
# - TBC - Right now the addition of nodes needs to be in the "right" order (MAYBE NOT ...)
#   (i.e. each node created needs to find its origins). This can be staged
#   (The present setup prevent the possibility of definition of loops - not meaningfull
#    for this problem (i.e. loops might be contained inside the algorithm parts))
#

class InfoGraph:
    def __init__(self, graph_name = "NONE"):

        self.name          = graph_name
        self.comment       = ""
        self.views         = {}           # Dictionary of the views

        self.fetching_info = {}


    def __str__(self):
        return f"InfoGrapf : {self.name}\n{self.comment}"


    ##################################
    # Basic features

    def set_comment(self, comment_text):     self.comment = comment_text

    def activate(self, view_name):           self.views[view_name].set_active()



    ################################################
    # Info dictionary 

    def get_info_dictionary(self):

        info_dictionary                      ={}
        info_dictionary['name']              = self.name
        info_dictionary['comment']           = self.comment

        info_dictionary['fetching_info']     = self.fetching_info

        info_dictionary['views'] = {}
        for iv in self.views.values():
            info_dictionary['views'][iv.view] = iv.get_info_dictionary()

        return info_dictionary


    def add_view_from_info(self, view_info):

        self.addNode(view_info['view'])
        self.views[view_info['view']].configure_from_info_dictionary(view_info)
        return


    ############### TBC : should copy.deepcopy() be used here ????????????????????????
    def configure_from_info_dictionary(self, info_dictionary={}):

        if (len(info_dictionary) == 0):
            print("[ InfoGraph ]  ERROR: info_dictionary is empty!!! ")
            return

        self.name              = info_dictionary['name']
        self.comment           = info_dictionary['comment']

        self.fetching_info     = copy.deepcopy(info_dictionary['fetching_info'])

        self.views.clear()
        for vd in info_dictionary['views'].values():
            self.add_view_from_info(vd)

        return



    ################################################
    # Save & Load

    def saveGraph(self, fileName = "graph.json"):

        info_dictionary = self.get_info_dictionary()

        with open(fileName, "w") as file:
            json.dump(info_dictionary, file)
        return



    def loadGraphFromFile(self, fileName):

        print("Loading graph from file  ", fileName)

        info_dictionary = {}
        with open(fileName) as file:
            info_dictionary = json.load(file)

        self.configure_from_info_dictionary(info_dictionary)

        self.print_graph()

        print("[ InfoGraph ]  Graph  ", self.name, "  loaded from file  ", fileName)

        return




    ################################################
    ### Graph building

    def addView(self, _view_obj):
        if _view_obj.view in self.views:
            print("[infoGraph] WARNING - view ", _view_obj.view, " already present in ", self.name)
        else:
            self.views[_view_obj.view] = _view_obj
        return



    # Used only in sub-graph extraction
    def add_view_deep_copy(self, _view_obj, reset_origins=False, reset_requirements=False):
        nv = copy.deepcopy(_view_obj)
        if reset_origins:         nv.origins.clear()
        if reset_requirements:    nv.requirements.clear()
        self.addView(nv)
        return


    def addViewDeepCopy(self, _view_obj):            self.add_view_deep_copy(_view_obj, reset_origins=False, reset_requirements=False)
    def addViewDeepCopyAsInput(self, _view_obj):     self.add_view_deep_copy(_view_obj, reset_origins=True,  reset_requirements=True)



    # Build the view and add it to the graph
    #
    # TBC : how fetching info are handled?????
    #
    def addNode(self, view_name, origins_list=[], algorithm_name='NONE', requirements_list=[], id_code="", status=""):
        _obj = InfoView(view_name)
        _obj.add_origins(origins_list)
        _obj.add_requirements(requirements_list)
        _obj.set_algorithm(algorithm_name)

        _obj.set_id_code(id_code)
        _obj.set_status(status)

        self.addView(_obj)


        #    # This method works, but it might be removed ... To be replaced with an external function for graphs' merging or by an "__IADD__" ("+=") method maybe ...
        #    # NOTE: NO deep copy so far (merge?)
        #    def addGraph(self, graph_to_add):
        #        for adding_v in graph_to_add.views:
        #            print("ADD GRAPH - checking  ", adding_v)
        #
        #            if adding_v in self.views:
        #                print("- present - skip - ", graph_to_add.views[adding_v], " -- ", self.views[adding_v])
        #            else:
        #                self.addView(graph_to_add.views[adding_v])
        #        return




    ################################################
    # Graph printing

    # Json-stype printing
    def print_graph(self):
        self.saveGraph('_to_be_removed.json')
        os.system('cat _to_be_removed.json | jq')







    ################################################
    # Graph checks on nodes (info available to the graph but not to the single view, plus some nice wrapping :) ) and paths

    ################################################
    # Node type

    def isNodeDefined(        self, view_name):        return (view_name in self.views)
    def isNodeInput(          self, view_name):        return (self.views[view_name].is_input())


    def isNodeEndpoint(self, view_name):
        for v in self.views.values():
            if (view_name in v.origins) or (view_name in v.requirements):
                return False
        return True


    def isNodeRequirement(self, view_name):
        for v in self.views.values():
            if view_name in v.requirements:
                return True
        return False



    ################################################
    # Lists of node by type

    def list_of_input_nodes(self):          return [v for v in self.views if self.isNodeInput(v)]
    def list_of_output_nodes(self):         return [v for v in self.views if self.isNodeEndpoint(v)]
    def list_of_requirement_nodes(self):    return [v for v in self.views if self.isNodeRequirement(v)]



    ################################################
    # Tools: requirements handling

    def list_of_requirements(self, view_name):
        l_req = []

        if not self.isNodeDefined(view_name):
            return l_req
        
        for uv in self.views[view_name].get_sources():
            for r in self.list_of_requirements(uv):
                if not r in l_req:     l_req.append(r)

        for r in self.views[view_name].requirements:
            if not r in l_req:     l_req.append(r)

        return l_req



    ################################################
    # Longest path to/from a node

    def longest_path_to_node(self, view_name):
        v = self.views[view_name]
        maxPath = 0
        for uv in v.get_sources():
            path = self.longest_path_to_node(uv)
            if path > maxPath:
                maxPath = path
        return (maxPath+1)



    def longest_path_from_node(self, view_name):
        maxPath = 0
        for dv in self.views:
            if view_name in self.views[dv].get_sources():
                path = self.longest_path_from_node(dv)
                if path > maxPath:
                    maxPath = path
        return (maxPath+1)




    ################################################
    # Nodes ranking

    def rank_nodes(self, nodesList=[]):
        d={}
        for v in nodesList:
            d[v] = self.longest_path_to_node(v)
        rd = dict(sorted(d.items(), key=lambda item: item[1]))

        return [v for v in rd.keys()]


    def ranked_requirements_for_node(self, view_name):
        lr  = self.list_of_requirements(view_name)
        return self.rank_nodes(lr)


    # Returns a dictionary {rank : [views]} (rank = longest path)
    def ranked_views(self):

        rd = {}
        for v in self.views:
            rd[v] = self.longest_path_to_node(v)

        max_lenght = max(rd.values())

        _ranked_views = {}
        for i in range(1, (max_lenght+1)):
            lv = []
            for v, r in rd.items():
                if r == i:     lv.append(v)
            _ranked_views[i] = lv

        return _ranked_views


    def list_of_ranked_views(self):
        _rv = self.ranked_views()
        lRV = [v for r in _rv for v in _rv[r]]
        return lRV





    ################################################
    # Id Codes

    def evaluate_id_code(self, iv):
        print('-- evaluate_id_code-- ', iv.view)
        
        if iv.has_id_code():
            print('-- evaluate_id_code-- has_code')
            #pass
        else:
            print('-- evaluate_id_code-- EVALUATING')
            digest_tool = hashlib.md5()

            digest_tool.update(iv.view.encode())

            # Fetching info - in particulat for input files this might protect against
            #                 unaccounted change in file content (eventually to be run on
            #                 multiple input files - if this would be the case ...)
            if iv.has_fetching_info():
                for fv in iv.fetching_info.values():
                    digest_tool.update(fv.encode())

            if iv.has_transformation():
                digest_tool.update(iv.algorithm.encode())

            if iv.has_origin():
                for ov in iv.origins:
                    self.evaluate_id_code(self.views[ov])
                    digest_tool.update(str(self.views[ov].id_code).encode())

            if iv.has_requirement():
                for rv in iv.requirements:
                    self.evaluate_id_code(self.views[rv])
                    digest_tool.update(str(self.views[rv].id_code).encode())

            iv.set_id_code(digest_tool.hexdigest())

        return



    def evaluate_all_id_codes(self):
        for iv in self.views.values():
            self.evaluate_id_code(iv)
            print(iv.view, '  has id_code  ', iv.has_id_code(), '  -  ', iv.id_code)



    ################################################
    # Check with db

    def check_availability(self, check_db):
        for ve in self.views:
            print(f"db checking  {ve:<20}", end=" ")
            v_id = self.views[ve].id_code
            if check_db.has_id(v_id):
                print("available")
                self.views[ve].set_available()
            else:
                print("********* NOT available")
                self.views[ve].set_active()








    ################################################
    # Tools: extract sub-graph

    # Note: self for this method refers - obviously - to the object calling it (i.e. the g1 InfoGraph istantiated in subGraphTo), while the input source_views is coming from the views of the original graph
    def add_backward_subgraph(self, starting_view, source_views, active_only):
        for iv_name in source_views[starting_view].get_sources():

            #            if not (iv_name in self.views):   # Avoid attempting to add multiple times the same view
            if not self.isNodeDefined(iv_name):   # Avoid attempting to add multiple times the same view

                if (active_only and source_views[iv_name].is_available()):
                    self.addViewDeepCopyAsInput(source_views[iv_name])
                else:
                    self.addViewDeepCopy(source_views[iv_name])
                    self.add_backward_subgraph(iv_name, source_views, active_only)
        return


    # This method supports the extraction of a sub-graph to multiple endpoints - the target's names must be passed as a list (also in case of a single target) 
    def subGraphTo(self, view_names = [], subGraph_name = "UPSTREAM", active_only = False):
        g1 = InfoGraph(subGraph_name)

        for view_name in view_names:
            if view_name in self.views:

                if not g1.isNodeDefined(view_name):
                    g1.addViewDeepCopy(self.views[view_name])

                g1.add_backward_subgraph(view_name, self.views, active_only)

        return g1




    def add_forward_subgraph(self, starting_view, source_views):
        for iv in source_views.values():
            if (starting_view in iv.get_sources()):
                if (iv.view in self.views):
                    del self.views[iv.view]
                self.addViewDeepCopy(iv)
                
                for x in [ov for ov in iv.get_sources() if ((ov != starting_view) and not (ov in self.views))]:
                    self.addViewDeepCopyAsInput(source_views[x])

                self.add_forward_subgraph(iv.view, source_views)


    # This method supports the extraction of a sub-graph from multiple start-points - the sources' names must be passed as a list (also in case of a single target) 
    def subGraphFrom(self, view_names = [], _graph_name = "DOWNSTREAM"):
        g1 = InfoGraph(_graph_name)

        for view_name in view_names:
            if view_name in self.views:
                if not (view_name in g1.views):
                    g1.addViewDeepCopyAsInput(self.views[view_name])
                g1.add_forward_subgraph(view_name, self.views)

        return g1



    ################################################
    # Activation propagation

    def propagate_activation_forward(self, starting_view):
        for iv in self.views.values():
            if starting_view in iv.get_sources():
                iv.set_active()
                self.propagate_activation_forward(iv.view)
        return


    def PropagateActivation(self):
        active_transformations = []
        for iv in self.views.values():
            if iv.is_active():
                active_transformations.append(iv)

        print(".......................... ACTIVE:")
        for iv in active_transformations:     print(iv.view)

        for iv in active_transformations:
            self.propagate_activation_forward(iv.view)
        return



    ################################################
    # Endpoints and tasks

    #    # This should probably be superseeded by list_of_output_nodes()
    #    def find_endpoints(self):
    #        endpoint_views = []
    #        for v_a in self.views:
    #            v_a_endpoint = True
    #            for v_b in self.views:
    #                if v_a in self.views[v_b].get_sources():
    #                    v_a_endpoint = False
    #                    break
    #            if v_a_endpoint:
    #                endpoint_views.append(v_a)
    #        print("Endpoints : ", endpoint_views)
    #        return endpoint_views
    #
    #
    #    def find_tasks(self, v, lv):
    #        if v.is_active():
    #            for o_i in v.get_sources():   self.find_tasks(self.views[o_i], lv)
    #            if not v in lv:               lv.append(v)
    #        return
    #
    #
    #    def print_tasks(self):
    #        endpoint_views = self.find_endpoints()
    #        tasks = []
    #        for ve in endpoint_views:
    #            self.find_tasks(self.views[ve], tasks)
    #
    #        print("--- List of tasks for graph ", self.name)
    #        for t_i in tasks:
    #            if not t_i.is_input():  print("--- Task : ", t_i)
    #            #            if t_i.is_transformation():  print("--- Task : ", t_i)
    #
    #        return



    def list_tasks_for(self, v):
        lv = []
        if v.is_active():
            for o_i in v.get_sources():
                lv.append(self.list_tasks_for(self.views[o_i]))
            if not v in lv:
                lv.append(v)
        return lv


    def print_tasks(self):
        endpoint_views = self.list_of_output_nodes()
        tasks = []
        for ve in endpoint_views:
            tasks.append(self.list_tasks_for(self.views[ve]))

        print("--- List of tasks for graph ", self.name)
        for t_i in tasks:
            if not t_i.is_input():  print("--- Task : ", t_i)

        return




    ################################################
    # Dot file generation - custom implementation

    # This custom method:
    # - does not implement yet the edges for requirements
    # - does implement a basic version of the aligned ranking feature
    #
    def saveDotFile(self, dotName = "graph.dot"):

        #        self.update_info_dictionary()

        dotFile = open(dotName, "w")
        dotFile.write('digraph {\n\n')

        # . Views and Transformation
        for iv in self.views.values():

            if iv.is_aggregation():
                origins_string=''
                for io in iv.origins: origins_string+='; '+io

                print('subgraph "cluster_'+iv.view+'"  { label="'+iv.view+'" '+origins_string+' } \n')

                dotFile.write('subgraph "cluster_'+iv.view+'"  { label="'+iv.view+'" '+origins_string+' } \n')

            else:
                color=''
                if   iv.is_active():     color=',style=filled, fillcolor=red'
                elif iv.is_available():  color=',style=filled, fillcolor=green'

                dotFile.write(f"{iv.view:<30} [shape=circle{color}]\n")

                if iv.algorithm != "NONE":
                    dotFile.write(f"T_{iv.view:<28} [shape=box, label={iv.algorithm}{color}]\n")

        dotFile.write('\n')

        # . Connections
        for iv in self.views.values():

            if iv.has_origin():
                if (not iv.is_aggregation()):
                    for io in iv.origins:
                        if io in self.views:
                            color=''
                            if   self.views[io].is_active():     color=',color=red, penwidth=2.0'
                            elif self.views[io].is_available():  color=',color=green, penwidth=2.0'
                            dotFile.write(f"{io:<20} -> T_{iv.view:<18} [arrowhead=none{color}]\n")
                            color=''                                                            # Indentation tbc
                    if   iv.is_active():     color=',color=red, penwidth=2.0'
                    elif iv.is_available():  color=',color=green, penwidth=2.0'
                    dotFile.write(f"T_{iv.view:<18} -> {iv.view:<20} [arrowtail=normal{color}]\n")


        dotFile.write('\n')

        # . Aligned ranking

        list_of_algorithms = [iv.algorithm for iv in self.views.values()]
        aligned_algorithms = {}

        #        print("list_of_algorithms : ", list_of_algorithms)

        for alg in list_of_algorithms:
            if (alg != 'NONE') and (not alg in aligned_algorithms) and (list_of_algorithms.count(alg) > 1):
                aligned_algorithms[alg] = [iv.view for iv in self.views.values() if iv.algorithm == alg]

                #        print("aligned_algorithms : ", aligned_algorithms)

        for alg in aligned_algorithms:
            as_algos = as_inputs = "{rank = same;"
            #as_inputs = "{rank = same;"

            for av in aligned_algorithms[alg]:
                as_algos  += f" T_{av};"
                for i_v in self.views[av].origins:    as_inputs += f" {i_v};"

            as_algos  += "}\n"
            as_inputs += "}\n"

            #            print(alg, "  A -->  ", as_algos)
            #            print(alg, "  I -->  ", as_inputs)

            dotFile.write(as_inputs)
            dotFile.write(as_algos)



        dotFile.write('\n}\n')
        dotFile.close()



    ################################################
    # Dot file generation - graphviz implementation

    # This method based on the python pakage:
    # - VIEW RANKING implemented. Views with equal-lenght path-to-node are aligned (not algos)
    # - Algorithm ranking might be implemented (not useful for event-loop)
    # - implements the edges for requirements (direct connection with empty-diamond arrowhead)
    # - Aggregations TO BE CHECKED
    #

    def addDotNode(self, dot_obj, _view, is_requirement = False, is_endpoint = False):
        t_style = v_style = ''
        t_fill  = v_fill  = ''

        if is_endpoint:
            v_style = 'filled'
            v_fill  = 'yellow'

        if _view.is_active():
            t_style = v_style = 'filled'
            t_fill  = v_fill  = 'red'
        elif _view.is_available():
            t_style = v_style = 'filled'
            t_fill  = v_fill  = 'green'
        elif _view.is_constant():
            t_style = v_style = 'filled'
            t_fill  = v_fill  = 'gray'


        if _view.view.startswith("regionWeight"):
            t_style = v_style = 'filled'
            t_fill  = v_fill  = 'cadetblue1'
            
            

        if _view.is_aggregation():
            dot_obj.node(_view.view, _view.view, shape='oval', penwidth='3.0', style=v_style, fillcolor=v_fill)
        else:
            #            if _view.has_requirement():
            if is_requirement:
                dot_obj.node(_view.view, _view.view, shape='circle', penwidth='3.0', style=v_style, fillcolor=v_fill)
            else:
                dot_obj.node(_view.view, _view.view, shape='circle', style=v_style, fillcolor=v_fill)

        if _view.is_transformation():
            dot_obj.node('T_'+_view.view, _view.algorithm, shape='box', style=t_style, fillcolor=t_fill)
        return


    def addDotEdge(self, dot_obj, node_from, node_to, _status, _type):
        temp_color    = ''
        temp_penwidth = '1.0'
        if (_status == 'active'):
            temp_color    = 'red'
            temp_penwidth = '2.0'
        elif (_status == 'available'):
            temp_color    = 'green'
            temp_penwidth = '2.0'

        if (  _type == 'in' ):     dot_obj.edge(node_from, node_to, arrowhead='none',     color=temp_color, penwidth=temp_penwidth)
        elif (_type == 'out'):     dot_obj.edge(node_from, node_to,                       color=temp_color, penwidth=temp_penwidth)
        elif (_type == 'req'):     dot_obj.edge(node_from, node_to, arrowhead='ediamond', arrowsize='2', color=temp_color, penwidth=temp_penwidth)
        else:                      print("ERROR: wrong edge type!  "+node_from+" -> "+node_to+"  , type = "+_type)
        return



    ###
    ###  TBC align_by_algoritm should be double-checked !!!!!!!!! -> set to False for the time being !
    ###

    def newDotFile(self, dotName = "graph.dot", align_by_view_rank=True, align_by_algorithm=False):

        dot = graphviz.Digraph('dot_graph', comment='dot_graph comment') 
            
        # . Views and Transformation
        for iv in self.views.values():

            is_requirement = self.isNodeRequirement(iv.view)
            is_endpoint    = self.isNodeEndpoint(iv.view)
            self.addDotNode(dot, iv, is_requirement, is_endpoint)

            #            if iv.is_aggregation():
            #
            #                with dot.subgraph(name="cluster_"+iv.view) as c1:
            #                    b_list = ['label = "'+iv.view+'"']
            #                    for io in iv.origins:
            #                        b_list.append(io);
            #
            #                    c1.body=b_list
            #                    
            #            else:
            #                self.addDotNode(dot, iv)

        

        # . Connections
        for iv in self.views.values():

            if iv.is_transformation():
                for io in iv.origins:     self.addDotEdge(dot, io, 'T_'+iv.view, self.views[io].status, 'in')
                self.addDotEdge(dot, 'T_'+iv.view, iv.view, iv.status, 'out')

            elif iv.is_aggregation():
                for io in iv.origins:     self.addDotEdge(dot, io, iv.view, self.views[io].status, 'out')

            if iv.has_requirement():
                for ir in iv.requirements:     self.addDotEdge(dot, ir, iv.view, self.views[ir].status, 'req')



        # . Align by view ranking

        if align_by_view_rank:

            ranked_views = self.ranked_views()

            for i, vl in ranked_views.items():
                if len(vl) > 0:
                    with dot.subgraph() as s:
                        s.attr(rank='same')
                        for v in vl:       s.node(v)



        # . Align by algorithms

        if align_by_algorithm:

            list_of_algorithms = [iv.algorithm for iv in self.views.values()]
            list_of_algorithms = list(dict.fromkeys(list_of_algorithms))
            if 'NONE' in list_of_algorithms:
                list_of_algorithms.remove('NONE')
            aligned_algorithms = {}

            for alg in list_of_algorithms:
                aligned_algorithms[alg] = [iv.view for iv in self.views.values() if iv.algorithm == alg]

                #print("aligned_algorithms : ", aligned_algorithms)

            for i, vl in aligned_algorithms.items():
                if len(vl) > 1:
                    with dot.subgraph() as s:
                        s.attr(rank='same')
                        for v in vl:       s.node('T_'+v)



        dot.save(dotName)

        return




    def convertDot2png(self, dotFile):
        pngFile = dotFile.replace('.dot', '.png')
        os.system('dot '+dotFile+' -Tpng -o '+pngFile)
        return




    def Plot(self, dot_file_name="graph.dot"):

        print("[infoGraph] Generating dot file for graph ", self.name)

        self.newDotFile(dot_file_name, align_by_algorithm=False)
        self.convertDot2png(dot_file_name)

        return



    
###   ViewDB   ################################################################
#
#
#
#


#class ViewDBentry:
#    def __init__(self, view_name, view_fetching_info):
#        self.view = {}
#        self.view['name']       = view_name
#        self.view['fetch_info'] = view_fetching_info


##### ViewDB assumes has_fetching_info = True !!!!! -> TBC


class ViewDB:
#    def __init__(self, dbName = 'vDB'):
    def __init__(self):
#        self.bd_name = dbName
        self.db      = {}

    def add_entry(self, view_name, view_id_code, view_fetching_info={}):
        self.db[view_id_code] = {}
        self.db[view_id_code]['name']       = view_name
        self.db[view_id_code]['fetch_info'] = view_fetching_info

    def add_view(self, view):
        self.add_entry(view.view, view.id_code, view.fetching_info)
        return

    def has_id(self, id_test):
        return (id_test in self.db)

    def print_db(self):
        print(self.db)

    def saveDB(self, fileName = "vDB.json"):
        with open(fileName, "w") as file:
            json.dump(self.db, file)

    def loadDBFromFile(self, fileName):
        with open(fileName) as file:
            self.db = json.load(file)

        # Print the type of data variable
        print("db type: ", type(self.db))
        self.print_db()

    def pruneDB(self):
        print('Placeholder for pruning function')  # Remove the entries for which no file is actually available
