
from os.path import exists, dirname, join as path_join, isfile
from annotation import Annotations,SimpleAnnotations,TextAnnotations
from document import get_document
from projectconfig import ProjectConfiguration
from folia2brat import get_extra_info
try:
    from cPickle import dump as pickle_dump, load as pickle_load
except ImportError:
    from pickle import dump as pickle_dump, load as pickle_load

from config import WORK_DIR
from message import Messager
import session 


def filter_layers(ann,path):
     #Added by Sander Naert to disable the visualisation of same annotations
    try:
        import simplejson as json
        string = session.load_conf()["config"]
        val = json.loads(string)["layers"]
    except session.NoSessionError:
        val = []
    except KeyError:
        val = []
    except Exception as e:
        val = []
        Messager.error("Error while enabling/disabling layers: "+str(e))
    proj = ProjectConfiguration(path)
    forbidden_entitie_types = []
    forbidden_entities = set()
    forbidden_ann=[]
    for i in val:
        forbidden_ann.append(i)        
    temp_array = []
    
    #Remove forbidden entities
    for i in ann["entities"]:
        if i[1] in forbidden_ann:
            forbidden_entities.add(i[0])
        else:
            temp_array.append(i)
    ann["entities"] = temp_array
    #Remove forbidden triggers
    temp_array = []
    forbidden_events=[]
    for i in ann["triggers"]:
        if i[1] in forbidden_ann:
            forbidden_events.append(i[0])
        else:
            temp_array.append(i)
    ann["triggers"] = temp_array
    
    #Remove forbidden events
    temp_array = []
    for i in ann["events"]:
        if i[1] in forbidden_events:
            pass
        else:
            #delete references to removed entities
            i[2][:] = [ role for role in i[2] if not role[1] in forbidden_entities ]
            temp_array.append(i)
    ann["events"] = temp_array
    
    #Remove forbidden relations
    temp_array = []
    for i in ann["relations"]:
        if i[1] in forbidden_ann:
            pass
        else:
            #if an arg points to an forbidden_ent then also remove this relation
            roles = [ role for role in i[2] if role[1] in forbidden_entities ]
            if not roles:
                temp_array.append(i)
    ann["relations"] = temp_array
    
    #Remove forbidden attributes
    temp_array = []
    for i in ann["attributes"]:
        if i[1] in forbidden_ann:
            pass
        elif not i[2] in forbidden_entities:
                temp_array.append(i)
    ann["attributes"] = temp_array
    
    return ann
    
def filter_folia(ann_obj):
    forbidden_ann=[]
    response = {"entities":[],"comments":[],"relations":[],"attributes":[],"tokens":{}}
    try:
        import simplejson as json
        import session
        string = session.load_conf()["config"]
        val = json.loads(string)["foliaLayers"]
    except session.NoSessionError:
        val = []
    except KeyError:
        val = []
        pass
    except Exception as e:
        val = []
        Messager.error("Error while enabling/disabling folia layers: "+str(e))
        pass
    try:
        response["tokens"]=ann_obj.folia["tokens"]
    except KeyError as e:
        pass
    if val:
        removed = set()
        forbidden = set(i for i in val)
        result = []
        alternatives = "alter" in val
        try:
            if 'all' in val:
                response["tokens"]={}
                return response
            else:
                for i in ann_obj.folia["entities"]:
                    if not i[3] in forbidden and not ( i[4] and alternatives ):
                        result.append(i)
                    else:
                        removed.add(i[0])
                response["entities"] = result
                result = []
                for i in ann_obj.folia["relations"]:
                    if not i[3] in forbidden and not i[2][0][1] in removed and not i[2][1][1] in removed and not ( i[4] and alternatives ):
                        result.append(i)
                    else:
                        removed.add(i[0])
                response["relations"] = result
                result = []
                for i in ann_obj.folia["attributes"]:
                    if not i[2] in removed:
                        result.append(i)
                response["attributes"] = result
                result = []
                for i in ann_obj.folia["comments"]:
                    if not i[0] in removed:
                        result.append(i)
                response["comments"] = result
        except KeyError:
            pass
    else:
        response = ann_obj.folia
    return response
    
#~ def validation(ann): 
    #~ #Added by Sander Naert: check if validation isn't turned off by client
    #~ try:
        #~ import simplejson as json
        #~ import session
        #~ string = session.load_conf()["config"]
        #~ Messager.debug("session: " + session.load_conf()["config"])
        #~ val = json.loads(string)["validationOn"]
    #~ except session.NoSessionError:
        #~ val = False
    #~ except KeyError:
        #~ val = False
    #~ except Exception:
        #~ val = False
        #~ Messager.error("Error while loading validation config:"+str(e))
    #~ temp_array = []
    #~ for i in ann["comments"]:
        #~ if not val and i[1] == "AnnotationError":
            #~ pass
        #~ else:
            #~ temp_array.append(i)
    #~ ann["comments"] = temp_array
    #~ return ann
    
def getAnnObject(collection,document):
    return getAnnObject2(collection,document)
    
#~ def getAnnObject1(collection,document):
    #~ app_path = WORK_DIR + "/application/"
    #~ ann = None
    #~ full_name = collection + document
    #~ full_name = full_name.replace("/","")
    #~ if( isfile(app_path+full_name)):
        #~ temp=open (app_path+full_name , 'rb')
        #~ ann = pickle_load(temp)
        #~ temp.close()
    #~ else:
        #~ ann = get_document(collection, document)
        #~ try:
            #~ #TODO:good error message
            #~ ann["folia"]=get_extra_info(collection,document)
        #~ except:
            #~ ann["folia"] = []
        #~ temp=open (app_path+full_name , 'wb')    
        #~ pickle_dump(ann, temp)
        #~ temp.close()
    #~ if ann == None:
        #~ ann = get_document(collection, document)
    #~ try:
        #~ from os.path import join as path_join
        #~ from document import real_directory
        #~ real_dir = real_directory(collection)
    #~ except:
        #~ real_dir=collection
    #~ filter_layers(ann,real_dir)
    #~ validation(ann)
    #~ return ann

def getAnnObject2(collection,document):
    '''newest version of the getAnnObject methode'''
    try:
        from os.path import join as path_join
        from document import real_directory
        real_dir = real_directory(collection)
    except:
        real_dir=collection      
    app_path = WORK_DIR + "/application/"
    ann = None
    full_name = collection + document
    full_name = full_name.replace("/","")
    if( isfile(app_path+full_name)):
        temp=open (app_path+full_name , 'rb')
        ann = pickle_load(temp)
        temp.close()
    else:
        ann = TextAnnotations(real_dir+document)
        ann = SimpleAnnotations(ann)
        ann.folia = {}
        try:
            #TODO:good error message
            ann.folia=get_extra_info(collection,document)
        except Exception as e:
            ann.folia = {}
            Messager.error('Error: get extra folia info() failed: %s' % e)
    #Validation:
    try:
        import os
        import simplejson as json
        import session
        docdir = os.path.dirname(ann._document)
        string = session.load_conf()["config"]
        val = json.loads(string)["validationOn"]
        #validate if config enables it and if it's not already done.
        if val:
            if not ann.validated:    
                from verify_annotations import verify_annotation
                projectconf = ProjectConfiguration(docdir)
                issues = []
                issues = verify_annotation(ann, projectconf)
            else:
                issues = ann.issues
        else:
            ann.validated = False
            issues = []
    except session.NoSessionError:
        issues = []
    except KeyError:
        issues = []
    except Exception as e:
        # TODO add an issue about the failure?
        issues = []
    ann.issues = issues
    temp=open (app_path+full_name , 'wb')    
    pickle_dump(ann, temp)
    temp.close()
    return ann

def getDocJson(collection,document):
    from annotator_cachen import _json_from_ann
    ann = getAnnObject(collection,document)
    return _json_from_ann(ann)
    
def update_pickle(sann):
    app_path = WORK_DIR + "/application/"
    temp_paths = sann.get_document().split("/data/")
    try:
        full_name = temp_paths[1].replace("/","")
        temp=open (app_path+full_name , 'wb')
        pickle_dump(sann, temp)
        temp.close()
    except Exception as e:
        Messager.error("Error while caching changes in the annotation file: "+str(e))
        
def update_dump(j_dic,file_path):
    app_path = WORK_DIR + "/application/"
    temp_paths = file_path.split("/data/")
    try:
        full_name = temp_paths[1].replace("/","")
        temp=open (app_path+full_name , 'wb')
        pickle_dump(j_dic, temp)
        temp.close()
    except Exception as e:
        Messager.error("Error while caching changes in the annotation file: "+str(e))
        
    
if __name__ == '__main__':
    import time
    millis = int(round(time.time() * 1000))
    print millis
    #ann = getAnnObject("/brat_vb/sentiment","detijd_other_Bekaert_12-05-05")
    ann = Annotations("/home/sander/Documents/Masterproef/brat/data/test")
    #~ ann = Annotations('/home/hast/Downloads/brat/data/brat_vb/sentiment/test')
    from annotation import TextBoundAnnotation
    #getAnnObject2("/","sporza")
    sann = SimpleAnnotations(ann)
    print filter_folia(sann)
    millis = int(round(time.time() * 1000)) - millis
    print millis
