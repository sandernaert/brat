from projectconfig import TypeHierarchyNode, ProjectConfiguration
from annotation import Annotations,TextLevelAnnotation, SimpleAnnotations
from message import Messager
from ApplicationScope import getAnnObject

class NoTextLevelConf(Exception):
    def __init__(self):
        Exception.__init__(self)
    def __str__(self):
        return u'No text level annotations defined in configuration'
        
class noValidAnswer(Exception):
    def __init__(self,answer):
        Exception.__init__(self)
        self.answer = answer
    def __str__(self):
        return u'%s is not a valid answer'%(self.answer)
        
class noValidNextStep(Exception):
    def __init__(self,next_step):
        Exception.__init__(self)
        self.next_step = next_step
    def __str__(self):
        return u'%s is not a valid next step, check configuration'%(self.next_step)
        
class TextAnnotations(object):
    '''this is the main class for annotations on textlevel
        It will read the projectconf and make all necesary classes.
    '''
    
    def __init__(self,projectconf, ann=""):
        self.projectconf = projectconf
        self.lists = {}
        self.defs = {}
        self.startlists = {}
        self.selectedList = None
        #ann is not the entire Annotations object but only a list of textLevel annotations
        self.ann = ann
        text_types = []
        try:
            text_types = self.projectconf.get_text_type_hierarchy()
        except KeyError:
            raise NoTextLevelConf()
        for i in text_types:
            if i.terms[0] == "Def":
                answer = Answer(i.arguments["id"][0], i.arguments["text"][0])
                self.defs[answer.id] = answer 
            elif i.terms[0] == "List":
                answers = {}
                nexts = {}
                index = 0
                for answer in i.arguments["defs"]:
                    answers[answer] = self.defs[answer]
                    nexts[answer] = i.arguments["next"][index]
                    index += 1
                lst = AnswerList(i.arguments["id"][0], i.arguments["name"][0],answers,nexts)
                self.lists[lst.id] = lst;
                self.startlists[lst.id] =StartList(self.defs,self.lists,lst)
            elif i.terms[0] == "SubList":
                answers = {}
                index = 0
                check = False
                if "checkboxes" in i.arguments and i.arguments["checkboxes"][0] == "True":
                    check = True
                for answer in i.arguments["defs"]:
                    answers[answer] = self.defs[answer]
                    if not check:
                        nexts[answer] = i.arguments["next"][index]
                        index += 1
                    else:
                        nexts[answer] = i.arguments["next"][0]
                lst = AnswerList(i.arguments["id"][0], i.arguments["name"][0],answers,nexts,True,check)
                self.lists[lst.id] = lst
        for annotation in self.ann:
            #TODO:Correct error if type is not found
            for i in self.startlists:
                if self.startlists[i].start.name == annotation.type:
                    self.startlists[i].set_ann(annotation)
                    break
    
    def set_ann(self, annotations):
        self.ann = annotations
        for annotation in self.ann:
            #TODO:Correct error if type is not found
            for i in self.startlists:
                if self.startlists[i].start.name == annotation.type:
                    self.startlists[i].set_ann(annotation)
                    break
                    
    def select(self,_id,start_list=None,current_list=None):
        #~ if not self.selectedList and not start_list:
            #~ self.selectedList = self.startlists[_id[0]]
            #~ return self.startlists[_id[0]].currentList
        if not start_list:
            self.selectedList = self.startlists[_id[0]]
            return self.startlists[_id[0]].start
        elif start_list:
            self.selectedList = self.startlists[start_list]
        return self.selectedList.select(_id,current_list)
    
    def unselect(self,start_list, current_id):
        self.selectedList = self.startlists[start_list]
        if self.selectedList.followed_path:
            return self.selectedList.unselect(current_id)
        else:
            return None
    
        
        

class StartList(object):
    def __init__(self,defs,lists,currentList, ann=""):
        self.defs = defs
        self.lists = lists
        self.start = currentList
        self.currentList = currentList
        self.followed_path = []    
        self.ann = ann    
    
    def set_ann(self, annotation):
        self.ann = annotation
        if self.ann:
            for id_ in self.ann.ids:
                ids = id_.split(';')
                if 'input' in ids:
                    text = self.ann.tail.split("|")[-1]
                    self.currentList.set_input(text)
                    self.followed_path.append(self.currentList.id)
                else:
                    self.select(ids,self.currentList.id)
        
    def select(self,_id,current_list):
        try:
            next_step,changed = self.lists[current_list].select(_id)
        except:
            raise
        #Will remove all following answers if one is changed
        if changed:
            found = False
            new_path = []
            for i in self.followed_path:
                if found:
                    self.lists[i].clear()
                else:
                    new_path.append(i)
                if i == current_list:
                    found = True
            self.followed_path = new_path
        if not current_list in self.followed_path :
            self.followed_path.append(current_list)
        if(not next_step == "stop"):
            try:            
                self.currentList = self.lists[next_step]
            except:
                raise noValidNextStep(next_step)
        else:
           self.currentList = "stop"
        #~ if not self.currentList == "stop":
            #~ try:
                #~ next_step = self.currentList.select(_id)
            #~ except:
                #~ raise noValidAnswer(_id)
            #~ self.followed_path.append(self.currentList.id)
            #~ if(not next_step == "stop"):
                #~ try:            
                    #~ self.currentList = self.lists[next_step]
                #~ except:
                    #~ raise noValidNextStep(next_step)
            #~ else:
                #~ self.currentList = "stop"
        return self.currentList
    
    def unselect(self, current_id):
        index = 0
        found = False
        if current_id == 'stop':
            self.currentList = self.lists[self.followed_path[-1]]
            return self.currentList
        for i in self.followed_path:
            if i == current_id:
                found = True
                break
            index += 1
        if index == 0:
            return None
        index -= 1
        self.currentList = self.lists[self.followed_path[index]]
        #~ self.currentList = self.start
        #~ if self.ann and len(self.ann.ids) >= 1:
            #~ for id_ in self.ann.ids[:-1]:
                #~ self.select(id_.split(';'),self.currentList.id)        
        return self.currentList
    
        

class AnswerList(object):
    #Has an id to identify the object and a name. 
    #Keeps a list of possible answers, and for every answer there is an value that gives says what the next_step is
    #this can be the id of an other (sub)list or can be "stop"
    def __init__(self,id, name,answers,next_steps, sublist=False, checkboxes=False):
        self.name = name
        self.id = id
        self.answers = answers
        self.nexts = next_steps
        self.sublist = sublist
        self.checkboxes = checkboxes
        self.answerids = []
        self.answertext = []
    def select(self,_id):
        changed = False
        if not self.checkboxes and self.answerids and not self.nexts[_id[0]] == self.nexts[self.answerids[0]]:
            changed = True
        self.answerids = []
        self.answertext = []
        for i in _id:
            #i can be empty if no answers were selected in the checkboxes
            if i:
                self.answerids.append(i)
                self.answertext.append(self.answers[i].text)
        #this only works for checkboxes and is needed because _id doesn't always contain a value
        if self.checkboxes :
            for i in self.nexts:
                return self.nexts[i],changed
        return self.nexts[_id[0]],changed
    def set_input(self, _input):
        self.answerids = ['input']
        self.answertext = [_input]
    def get_ids(self):
        return ';'.join(self.answerids)
    def get_texts(self):
        return ';'.join(self.answertext)
    def clear(self):
        self.answerids = []
        self.answertext = []
    def __str__(self):
        return u'%s\t%s' % (self.id,self.name)
      

class Answer(object):
    def __init__(self,id, text):
        self.id = id
        self.text = text
    def __str__(self):
        return u'%s\t%s' % (self.id,self.text)
        
def get_list(path,doc):
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(path)
    except:
        real_dir=path
    ann =getAnnObject(path,doc)
    proj = ProjectConfiguration(real_dir)
    try:
        txt_lvl = TextAnnotations(proj,ann.get_textLevels())
    except NoTextLevelConf as e:
        return {'exception' :str(e) }
    #~ if txt_lvl.currentList == "stop":
        #~ return {'stop':True, 'annotation':str(txt_lvl.selectedList.ann),}
    response = list_to_dict(txt_lvl.selectedList.currentList)
    #Back_pos tells if there is still atleast 1 answer left that can be removed
    response["back_pos"] = False
    if len(txt_lvl.followed_path) >0 :
        response["back_pos"] = True
    return response
    
def get_startlist(path,doc):
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(path)
    except:
        real_dir=path
    ann =getAnnObject(path,doc)
    proj = ProjectConfiguration(real_dir)
    try:
        txt_lvl = TextAnnotations(proj,ann.get_textLevels())
    except NoTextLevelConf as e:
        return {'exception' :str(e) }
    response = startlist_to_dict(txt_lvl.startlists)
    #Back_pos tells if there is still atleast 1 answer left that can be removed
    response["back_pos"] = False
    return response
    
def select(path,doc,_id,start_list=None, current_list=None):
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(path)
    except:
        real_dir=path
    proj = ProjectConfiguration(real_dir)
    try:
        import simplejson as json
        _id = json.loads(_id)
        txt_lvl = TextAnnotations(proj)
        if start_list:
            answerlist = txt_lvl.startlists[start_list].start
            with getAnnObject(path, doc) as ann:
                ann_txtLvl = ann.get_textLevels()
                annotation = None
                for i in ann_txtLvl:
                    if i.type == answerlist.name:
                        annotation = i
                if not annotation:
                    ann_id = ann.get_new_id('F')
                    ann.add_annotation(TextLevelAnnotation(ann_id, answerlist.name,[]))
                    annotation = ann.get_ann_by_id(ann_id)
                    ann_txtLvl = ann.get_textLevels()
                txt_lvl.set_ann(ann_txtLvl)
                response = txt_lvl.select(_id,start_list,current_list)
                update_annotations(ann,annotation, txt_lvl.startlists[start_list])
        else:
            ann = getAnnObject(path,doc)
            ann_txtLvl = ann.get_textLevels()
            if ann_txtLvl:
                txt_lvl.set_ann(ann_txtLvl)
            response = txt_lvl.select(_id,start_list)
    except Exception,e :
        raise
        return {'exception' :str(e) }
    if response == "stop":
        return {'stop':True , 'annotation':str(txt_lvl.selectedList.ann),}
    return list_to_dict(response)

def unselect(path,doc,start_list, current_id):
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(path)
    except:
        real_dir=path
    from message import Messager
    with getAnnObject(path, doc) as ann:
        proj = ProjectConfiguration(real_dir)
        ann_txtLvls = ann.get_textLevels()
        if not ann_txtLvls:
            return get_startlist(path,doc)
        txt_lvl = TextAnnotations(proj,ann_txtLvls)
        response_list = txt_lvl.unselect(start_list,current_id)
        #answerlist = txt_lvl.startlists[start_list].start
        #~ for i in ann_txtLvls:
                #~ if i.type == answerlist.name:
                    #~ update_annotations(ann,i, txt_lvl.startlists[start_list])
                    #~ break
        if response_list:
            response = list_to_dict(response_list)
        else:
            response = get_startlist(path,doc)
        return response
    
def input_text(path,doc,_id,text,start_list, current_list=None):
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(path)
    except:
        real_dir=path
    proj = ProjectConfiguration(real_dir)
    txt_lvl = TextAnnotations(proj)
    answerlist = txt_lvl.startlists[start_list].start
    with getAnnObject(path, doc) as ann:
        ann_txtLvls = ann.get_textLevels()
        annotation = None
        for i in ann_txtLvls:
            if i.type == answerlist.name:
                annotation = i
        if annotation:
            txt_lvl.set_ann(ann_txtLvls)
        else:
            ann_id = ann.get_new_id('F')
            ann.add_annotation(TextLevelAnnotation(ann_id, answerlist.name,[]))
            annotation = ann.get_ann_by_id(ann_id)
            #~ ann_txtLvls = ann.get_textLevels()
        #~ if annotation.tail:
            #~ annotation.tail += ";"
        txt_lvl.startlists[start_list].currentList.set_input(text)
        txt_lvl.startlists[start_list].currentList = 'stop'
        if not current_list in txt_lvl.startlists[start_list].followed_path:
            txt_lvl.startlists[start_list].followed_path.append(current_list)
        update_annotations(ann,annotation, txt_lvl.startlists[start_list])
        #~ annotation.tail += text
        #~ annotation.ids.append(_id)
    return {'stop':True, 'annotation':str(annotation),}


def update_annotations(ann,ann_txtLvl, txt_lvl):
    #update annotation for file
    if len(txt_lvl.followed_path) == 0:
        ann.del_annotation(ann_txtLvl)
        return 0
    ann_txtLvl.tail = ""
    ann_txtLvl.ids = []
    for i in txt_lvl.followed_path:
        ann_txtLvl.tail += txt_lvl.lists[i].get_texts()+'|'
        ann_txtLvl.ids.append(txt_lvl.lists[i].get_ids())
    #remove extra ";" at end
    if ann_txtLvl.tail:
        ann_txtLvl.tail=ann_txtLvl.tail[:-1]

def list_to_dict(answer_list):    
    response = {'name':answer_list.name, 'id':answer_list.id, 'nexts':answer_list.nexts, 'sublist':answer_list.sublist,
     'stop':False, 'checkboxes':answer_list.checkboxes,}
    keys = answer_list.answers.keys()
    keys.sort() 
    response['answer_ids'] = [ a for a in keys ]
    response['answer_texts'] = [ answer_list.answers[a].text for a in keys ]
    if 'input' in answer_list.answerids:
        response['answers']= answer_list.answertext[0]
    else:
        response['answers']= answer_list.answerids
    response["back_pos"] = True
    return response
    
def startlist_to_dict(answer_list):    
    response = {'name':'', 'id':'', 'answers':[], 'sublist':False, 'stop':False,'checkboxes':False}
    #a is the id
    keys = answer_list.keys()
    keys.sort()
    response['answer_ids'] = [ a for a in keys ]
    response['answer_texts'] = [ answer_list[a].start.name for a in keys ]
    return response
        
if __name__ == "__main__":
    proj = ProjectConfiguration("/home/sander/Documents/Masterproef/brat/data/brat_vb/sentiment")
    #~ proj.get_text_type_hierarchy()
    #ann = Annotations("/home/sander/Documents/Masterproef/brat/data/brat_vb/sentiment/sporza")
    #textann = TextAnnotations(proj,ann.get_textLevels())
    #print textann.select(['0.2'],'0')
    #print textann.select(['1.2','1.3'],'0')
    #print textann.select(['5.2'],'0')
    #~ print "STARTLISTS"
    #~ print "###################"
    #~ print
    #~ print "LISTS"
    #~ print textann.lists
    #~ print "###################"
    #~ print
    #~ print "DEFS"
    #~ print textann.defs
    #~ print "###################"
    #~ print "#####SELECT########"
    #~ print textann.select('0.2','0')
    #detijd_other_Bekaert_12-05-05
    #~ import cProfile
    #~ cProfile.run('get_startlist("/brat_vb/sentiment/","sporza")')
    print get_list("/voorbeeld/","sporza")
    #~ print select('/brat_vb/sentiment/','sporza','0')
    #~ #print "#####UNSELECT#######"
    #~ print unselect('/brat_vb/sentiment/','sporza','0')
    #~ print select('/brat_vb/sentiment/','sporza','0.1','0')
