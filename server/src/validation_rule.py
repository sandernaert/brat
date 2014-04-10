from projectconfig import TypeHierarchyNode, ProjectConfiguration
from annotation import Annotations, TextBoundAnnotation, TextAnnotations,EventAnnotation, BinaryRelationAnnotation
from message import Messager

RULE_ARG= ["if","req","allowed","notallowed"]

class ValidationRule(object):
    def __init__(self, node):
        self.node = node
        self.arguments = node.arguments
        self.type = node.terms[0]
        
        for arg in RULE_ARG:
            if not arg in self.arguments:
                self.arguments[arg]=[]

    def validate(self, annotation, connections,pos_ann,ann,projectconf):
        #connections contains all the annotations that have a connection with the annotation
        from verify_annotations import AnnotationIssue
        def disp(s):
            return projectconf.preferred_display_form(s)
            
        aid = annotation.id
        issue =[]
        if_response = True
        
        if self.arguments["if"]:
            if_response = parse_if(self.arguments["if"][0],annotation,connections,pos_ann,ann)
        if self.arguments["req"] and if_response:
            #check if required annotations are present
            self.arguments["req"] = extend_arg(pos_ann,self.arguments["req"])
            found = 0
            for req in self.arguments["req"]:
                if any(x.type == req for x in connections[aid]):
                    found+=1
            if not (found <= self.node.argument_maximum_count("req") and found >= self.node.argument_minimum_count("req")):
                issue.append(AnnotationIssue(annotation.id, "AnnotationError", "%s is needed for %s" % (' or '.join(self.arguments["req"]), disp(annotation.type))))
        if self.arguments["allowed"] and if_response:
            #check if there aren't to many allowed annotations
            self.arguments["allowed"] = extend_arg(pos_ann,self.arguments["allowed"])
            found = 0
            for allowed in self.arguments["allowed"]:
                if any(x.type == allowed for x in connections[aid]):
                    found+=1
            if found > self.node.argument_maximum_count("allowed"):
                issue.append(AnnotationIssue(annotation.id, "AnnotationError", "%s can only have %s" % (' or '.join(self.arguments["allowed"]), disp(annotation.type))))
        if self.arguments["notallowed"] and if_response:
            #check if there are no annotations that aren't allowed
            self.arguments["notallowed"] = extend_arg(pos_ann,self.arguments["notallowed"])
            found = 0
            for nallowed in self.arguments["notallowed"]:
                if any(x.type == nallowed for x in connections[aid]):
                    found+=1
            if found >= self.node.argument_minimum_count("notallowed"):
                issue.append(AnnotationIssue(annotation.id, "AnnotationError", "%s can't have %s" % (disp(annotation.type),' or '.join(self.arguments["notallowed"]))))
        
        return issue
            
class ValidationRules(object):
    '''
    Connects all annotation types with rules to validate them in dictionary "data"
    '''
    def __init__(self, projectconf):
        self.data = {}
        self.val = True
        self.projectconf = projectconf
        for t in projectconf.get_entity_types():
            self.data[t] = []
        for t in projectconf.get_event_types():
            self.data[t] = []
        for t in projectconf.get_relation_types():
            self.data[t] = []
        for t in projectconf.get_attribute_types():
            self.data[t] = []
        for t in projectconf.get_equiv_types():
            self.data[t] = []
        try:
            nodes = projectconf.get_rules_type_hierarchy()
            if not nodes:
                raise KeyError
            for node in nodes:
                vrule = ValidationRule(node)
                self.data[vrule.type].append(vrule)
        except KeyError:
            self.val = False
            Messager.debug("No rules defined")
            
        
    def validate(self, annotations,ids=[]):
        #ids is an array to specify which annotations should be validated
        from annotation import OnelineCommentAnnotation,UnknownAnnotation,TextLevelAnnotation
        annotations.validated = True
        issues=[]
        response = False
        if self.val:
            connections = build_connections(annotations)
            if not ids:
                response = False
                ids= annotations._ann_by_id.keys()
            else:
                #this will find all annotations that have to be revalidated
                response = True
                temp_ids = set()
                for i in ids:
                    temp_ids.add(i)
                    recursive_ann(annotations.get_ann_by_id(i),connections,temp_ids,annotations)
                ids = list(temp_ids)
            for _id in ids:
                try:
                    annotation = annotations.get_ann_by_id(_id)
                except:
                    annotation = None
                if annotation and not isinstance(annotation, OnelineCommentAnnotation) and not isinstance(annotation, TextLevelAnnotation) and not isinstance(annotation, UnknownAnnotation):    
                    for rule in self.data[annotation.type]:
                        issue = rule.validate(annotation, connections,self.data.keys(),annotations,self.projectconf)
                        issues+=issue
        if not response:
            ids = []
        return issues, ids
        
def build_connections(ann):
    ''' 
    Builds a dictionary with key: annotation id and value: list of annotations that are connected with the other annotation
    '''
    from annotation import Annotations, TextBoundAnnotation, AttributeAnnotation, BinaryRelationAnnotation, EventAnnotation, EquivAnnotation
    connections={}
    equivs = {}
    for an in ann:
        if isinstance(an, TextBoundAnnotation):
            connections[an.id]=[]
            equivs[an.id]=[]
    for an in ann:
        if isinstance(an, AttributeAnnotation):
            #try, except because events can also have attributes but they should be connected to the trigger in this dict.
            try:
                connections[an.target].append(an)
            except:
                connections[ann.get_ann_by_id(an.target).trigger].append(an)
        if isinstance(an, BinaryRelationAnnotation):
            for i in an.get_deps()[1]:
                connections[i].append(an)        
        if isinstance(an, EventAnnotation):
            for i in an.get_deps()[0]:
                connections[i].append(an)
            for i in an.get_deps()[1]:
                connections[i].append(an)            
        if isinstance(an, EquivAnnotation):
            equivs[an.entities[0]]=an.entities
            
    #Gives all equiv entities the same connections
    for equiv in equivs:
        if equivs[equiv]:
            full_con = []
            for entity in equivs[equiv]:
                full_con.extend(connections[entity])
            for entity in equivs[equiv]:
                connections[entity]=full_con
    return connections
    
def parse_if(string,annotation,connections,pos_ann,ann):
    import re
    parts = string.split()
    i=0
    ifstring = []
    for part in parts:
        ifstring.append(part)
        m = re.search('(and|or|not|==|<=|>=|>|<|\(|\))', part)
        comp = False
        comp_place = 0
        if (i< len(parts)-1 and re.search('==|<=|>=|>|<',parts[i+1])):
            comp = True
            comp_place =1
        if (i>0 and re.search('==|<=|>=|>|<',parts[i-1])):
            comp = True
            comp_place =-1
        if not (m and part == m.group(0)):
            ifstring[i] = test(annotation,part,connections,comp,pos_ann,ann)
            if ifstring[i] == "False" and comp:
                if comp_place == -1:
                    #i is second part of comparision, delete 2 previous elements and change i
                    parts.pop(i-1)
                    parts.pop(i-2)
                    i=i-2
                if comp_place == 1:
                    #i is first part of comparision, delete 2 next elements, i doesn't need to change
                    parts.pop(i+1)
                    parts.pop(i+1)

        i+=1    
    response = " ".join(ifstring)
    try:
        response = eval(response)
    except:
        pass
    if response:
        response = True
    else:
        response = False
    return response

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
def test(annotation, arg, connections,comp,pos_ann,ann):
    '''
    if arg is attr replace with value
    if arg is relation replace with arg2
    if arg is event replace with trigger
    if arg is entity replace with id
    '''
    import re
    from annotation import TextBoundAnnotation, AttributeAnnotation, BinaryRelationAnnotation, EventAnnotation, EquivAnnotation, AnnotationNotFoundError
    
    parts = []
    string = arg
    if is_number(arg):
        return arg
    while re.search(r'(.+?)\.(.+)', string):
        m = re.search(r'(.+?)\.(.+)', string)
        if m: 
        #dot found, extra attribute specified
            parts.append(m.group(1))
            string = m.group(2)
    parts.append(string)
    if comp and not arg in pos_ann and len(parts) == 1:
        #in this case arg is a string that's part of a comparision and shouldn't be changed.
        response = '\''+str(arg)+'\''
        return response

    temp_ann = annotation
    response=""
    attr=""
    for p in parts:
        #see if p has a wildcard in it 
        extended = extend_arg(pos_ann,[p])
        arg_ann =""
        if attr and extended[0] in pos_ann:
            try:
                response = eval("temp_ann."+attr)
                temp_ann = ann.get_ann_by_id(response)
            except :
                response =""
                attr=""
                break
                
        if len(extended) == 0 and not extended[0] == p:
            p = extended[0]
        elif len(extended) > 1:
            #TODO: might be better solutions than first match
            #wildcard found and will replace p with the first match in connections
            for a in extended:
                if temp_ann.id in connections and any(b.type == a for b in connections[temp_ann.id]):
                    p = a
                    break
                
        if p in pos_ann:
            #p is an annotation name
            for a in connections[temp_ann.id]:
                if a.type == p:
                    arg_ann =a
            if arg_ann =="":
                #arg can still be the annotation itself
                if temp_ann.type == p:
                    arg_ann = temp_ann
                    attr="id"
            elif isinstance(arg_ann, TextBoundAnnotation):
                attr = "id"
            elif isinstance(arg_ann, BinaryRelationAnnotation):
                attr = "arg2"
            elif isinstance(arg_ann, EventAnnotation):
                attr = "trigger"
            elif isinstance(arg_ann, AttributeAnnotation):
                attr = "value"
            if not arg_ann:
                break
            else:
                temp_ann = arg_ann      
        else:
            #p is an attribute name(not annotation called attribute)
            attr = p
    try:
        response = eval("temp_ann."+attr)
    except:
        response =""
        pass
    if response:
        if not is_number(response):
            response = '\''+str(response)+'\''        
    else:
        response = "False"
    return str(response)


def extend_arg(pos_ann,arguments):
    response = []
    for arg in arguments:
        if arg[0] == "*" and arg[-1] == "*" :
            response += [i for i in pos_ann if arg[1:-1] in i ]
        elif arg[0] == "*":
            response += [i for i in pos_ann if i[-len(arg)+1:] == arg[1:]]
        elif arg[-1] == "*":
            response += [i for i in pos_ann if i[0:len(arg)-1] == arg[:-1] ]
        else:
            response.append(arg)
    
    return response

def recursive_ann(annotation,con,ids,ann):
    '''function that finds all annotations that depend on annotation and adds the id's to ids
    '''
    temp = []
    for temp_ann in con[annotation.id]: 
        if isinstance(temp_ann, EventAnnotation):
            for i in temp_ann.get_deps()[0]:
                if not i in ids:
                    temp.append(i)
                    ids.add(i)
        if isinstance(temp_ann, BinaryRelationAnnotation):
            for i in temp_ann.get_deps()[1]:
                if not i in ids:
                    temp.append(i)
                    ids.add(i)
    for i in temp:
        temp_ann = ann.get_ann_by_id(i)
        if isinstance(temp_ann, TextBoundAnnotation):
            recursive_ann(temp_ann,con,ids,ann)
    
if __name__ == "__main__":
    from annotation import TextBoundAnnotation, TextAnnotations,EventAnnotation, BinaryRelationAnnotation
    proj = ProjectConfiguration("/home/sander/Documents/Masterproef/brat/data/brat_vb/sentiment")
    ann = Annotations("/home/sander/Documents/Masterproef/brat/data/brat_vb/sentiment/sporza")
    
    #SPEED TEST
    import time
    millis = int(round(time.time() * 1000))
    print millis
    vrules = ValidationRules(proj)
    for i in vrules.validate(ann)[0]:
        print str(i)
    millis = int(round(time.time() * 1000)) - millis
    print millis
        

    

    
 
