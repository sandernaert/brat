#!/usr/bin/env python
# -*- coding: utf-8 -*-

from projectconfig import ProjectConfiguration
from verify_annotations import argparser
from annotation import Annotations,TextAnnotations
from ssplit import regex_sentence_boundary_gen 
from ssplit import _sentence_boundary_gen
from os.path import join as path_join
#from pynlpl.formats import folia
import folia
class EntityNotFoundError(Exception):
    def __init__(self, entity):
        self.entity = entity

    def __str__(self):
        return u'Entity not found: %s' % (entity )

def build_entities_attr(ann):
#input annotions object
#returns a dictionary key: entity id, value: set of attributes
    attributes={}
    for entity in ann.get_textbounds():
        attributes[entity.id]=set((a for a in ann.get_attributes() if a.target == entity.id))
    return attributes
    
def _text_by_offsets_gen(text, offsets):
        for start, end in offsets:
            sentence = text[start:end]
            yield start, end, sentence    
            
def build_text_structure(ann,txt_file_path):    
    '''
    Will split a text file in paragraphs, sentences and words and return the folia document
    For every word it will check 2 main things:
    1) is the word part of some entities? and if so it will add them to a list of lists of words
    2) is their an entity that ends with this word? if so it will create the entity with the right words out of the list and delete this element after 
    it took the words out. 
    After every sentence, paragraph all the entities that started and ended within that structure will be added into the EntityLayer

    '''
    from annotation import open_textfile
    from tokenise import gtb_token_boundary_gen
    def add_list_entities(struct, folia_entities):
    #will check if any entities have to be added and add if needed
        if folia_entities:
            layer = struct.append(folia.EntitiesLayer)
            for folia_entity in folia_entities:
                
                layer.append(folia_entity)
                for attr in attributes[folia_entity.id]:
                    folia_entity.append(folia.Feature(doc,subset=attr.type, cls=str(attr.value)))
            
    try:
            #Sort entities on offset instead of id        
            entities = sorted(ann.get_textbounds(), key=lambda entity: (entity.start, -entity.end))
            index = 0
            doc = folia.Document(id='brat')
            
            attributes = build_entities_attr(ann)
                    
            folia_text = doc.append(folia.Text)
            paragraph = folia_text.append(folia.Paragraph)
            folia_sentence = 0
            par_start = 0
            #fictive sets
            doc.annotationdefaults[folia.AnnotationType.ENTITY] = {"entiteit_set.xml": {} }
            doc.annotations.append( (folia.AnnotationType.ENTITY, "entiteit_set.xml" ) ) 
            doc.annotationdefaults[folia.AnnotationType.MORPHOLOGICAL] = {"morph_set.xml": {} }
            doc.annotations.append( (folia.AnnotationType.MORPHOLOGICAL, "morph_set.xml" ) ) 
    
            entity = entities[index]
            entities_words=[]
            inner_index=0
            entities_words.append([])
            
            folia_entitiesLayer_par=[]
            folia_entitiesLayer_sen=[]
            folia_entitiesLayer_txt=[]

            
            with open_textfile(txt_file_path, 'r') as txt_file:
                text = txt_file.read()
            offsets = [o for o in regex_sentence_boundary_gen(text)]
            for start, end, sentence in _text_by_offsets_gen(text, offsets):
                if start == end and text[start-1] == '\n':
                    add_list_entities(paragraph, folia_entitiesLayer_par)
                    folia_entitiesLayer_par = []
                    paragraph = folia_text.append(folia.Paragraph)
                    par_start = start
                elif sentence != "" :
                    add_list_entities(folia_sentence, folia_entitiesLayer_sen)
                    folia_entitiesLayer_sen = []
                    folia_sentence = paragraph.append(folia.Sentence,sentence)
                offsetsw = [o for o in gtb_token_boundary_gen(sentence)]
                for tok in _text_by_offsets_gen(sentence, offsetsw):
                    entity = entities[index]
                    inner_index=0
                    folia_word = folia_sentence.append(folia.Word, tok[2])
                    morph_layer= ""                
                    #check if word is part of the entity and if so remember folia word
                    while entity.start <= entities[index].end :
                        while( len(entities_words) <= inner_index ):
                                entities_words.append([])
                        for span_start, span_end in entity.spans:                                    
                            if ( span_start <= tok[0]+start and tok[1]+start <= span_end):
                                entities_words[inner_index].append(doc[folia_word.id])
                            #entity ends within the word
                            elif (tok[1]+start >= span_end and span_end > tok[0]+start) :
                                offset_start = span_start-(start+tok[0])
                                if offset_start <0 :# entity started before this word
                                    offset_start =0;
                                offset_end = span_end-(start+tok[0])
                                string = tok[2][offset_start:offset_end]
                                if not morph_layer:
                                    morph_layer = folia_word.append(folia.MorphologyLayer)
                                morph = morph_layer.append(folia.Morpheme(doc, generate_id_in=folia_word))
                                morph.append(folia.TextContent(doc, value=string, offset=offset_start))
                                entities_words[inner_index].append(doc[morph.id])
                            #entity starts within the word
                            elif (tok[1]+start > span_start and span_start >= tok[0]+start) :
                                offset_start = span_start-(start+tok[0])
                                offset_end = span_end-(start+tok[0])
                                string = tok[2][offset_start:offset_end]
                                if not morph_layer:
                                    morph_layer = folia_word.append(folia.MorphologyLayer)
                                morph = morph_layer.append(folia.Morpheme(doc, generate_id_in=folia_word))
                                morph.append(folia.TextContent(doc, value=string, offset=offset_start))
                                entities_words[inner_index].append(doc[morph.id])
                        inner_index = inner_index + 1
                        if len(entities) > index + inner_index :
                            entity = entities[index+inner_index]    
                        else:
                            break    
                    entity = entities[index]
                    inner_index = 0    
                    #check for end of an entity and append entity to either text, paragraph or sentece depending on start of the entity    
                    current_index = index
                    while entity.start <= entities[current_index].end :
                        if entity.end <= start + tok[1] and entity.start <= start + tok[0] :
                            if (entity.start >= start):
                                folia_entitiesLayer = folia_entitiesLayer_sen                
                            elif (entity.start >= par_start):
                                folia_entitiesLayer = folia_entitiesLayer_par
                            else:
                                folia_entitiesLayer = folia_entitiesLayer_txt                    
                            if entities_words[inner_index]:        
                                folia_entity = folia.Entity(doc, cls=entity.type, id=entity.id , contents=entities_words[inner_index])
                                folia_entitiesLayer.append(folia_entity)
                            elif not any(x.id == entity.id for x in folia_entitiesLayer):
                                #see if entity is already added
                                try:
                                    doc[entity.id]
                                except KeyError:
                                    raise EntityNotFoundError(entity)
                            if(inner_index == 0):
                                entities_words.pop(0)
                                if len(entities) > index+1 :
                                    index = index + 1
                                    for i in range(0, len(entities_words)):
                                        if(not entities_words[0]):
                                            entities_words.pop(0)
                                            index = index + 1
                                else:
                                    break
                                    
                            elif(inner_index > 0):
                                entities_words[inner_index]=[]
                                inner_index = inner_index + 1                            
                        else:
                            inner_index = inner_index + 1
                        if len(entities) > index + inner_index:
                            entity = entities[index+inner_index]
                        else:
                            break    
            add_list_entities(paragraph, folia_entitiesLayer_par)    
            add_list_entities(folia_sentence, folia_entitiesLayer_sen)
            add_list_entities(folia_text, folia_entitiesLayer_txt)        
            return doc
    except IOError:
        pass # Most likely a broken pipe
            
def build_relations(ann):
    from annotation import TextBoundAnnotation, AttributeAnnotation, BinaryRelationAnnotation, EventAnnotation, EquivAnnotation
    relations={}
    equivs={}
    events={}
    for a in ann:
        if isinstance(a, TextBoundAnnotation):
            relations[a.id] = []
            equivs[a.id] = []
        if isinstance(a, BinaryRelationAnnotation):
            relations[a.arg1].append(a)
        elif isinstance(a, EquivAnnotation):
            equivs[a.entities[0]].append(a)
        elif isinstance(a, EventAnnotation):
            events[a.trigger]=a
    return relations, equivs, events
    
def add_relations_to_layer(folia_structure,layers,relations,doc):
    #folia_structure is a sentence/paragraph/text 
    dependencies = []
    for layer in layers:
        for entity in layer.data:
            for dependency in relations[entity.id]:
                hd = folia.Headspan(doc, contents=doc[dependency.arg1].wrefs())
                al = hd.append(folia.Alignment)
                al.append(folia.AlignReference, id=dependency.arg1, type=folia.Entity)
                
                dep = folia.DependencyDependent(doc, contents=doc[dependency.arg2].wrefs())
                al = dep.append(folia.Alignment)
                al.append(folia.AlignReference, id=dependency.arg2, type=folia.Entity)
                
                folia_dependency = folia.Dependency(doc,cls=dependency.type, id=dependency.id)
                folia_dependency.append(hd)
                folia_dependency.append(dep)
                dependencies.append(folia_dependency)
    if dependencies:
        dependenciesLayer = folia_structure.append(folia.DependenciesLayer, contents=dependencies)
        
def add_equivs_to_layer(folia_structure,layers,equivs,doc):
    #folia_structure is a sentence/paragraph/text 
    dependencies = []
    for layer in layers:
        for entity in layer.data:
            for dependency in equivs[entity.id]:
                folia_dependency = folia.Dependency(doc,cls=dependency.type)
                for ent in dependency.entities:
                    hd = folia.Headspan(doc, contents=doc[ent].wrefs())
                    al = hd.append(folia.Alignment)
                    al.append(folia.AlignReference, id=ent, type=folia.Entity)
                    folia_dependency.append(hd)
                dependencies.append(folia_dependency)
    if dependencies:
        dependenciesLayer = folia_structure.append(folia.DependenciesLayer, contents=dependencies)
        
def add_event_rel_to_layer(folia_structure,layers,event_rel,doc):
    dependencies = []
    for layer in layers:
        for entity in layer.data:
            if entity.id in event_rel and event_rel[entity.id]:
                folia_dependency = folia.Dependency(doc,cls="Event",id=event_rel[entity.id].id)
                hd = folia.Headspan(doc, contents=doc[entity.id].wrefs())
                al = hd.append(folia.Alignment)
                al.append(folia.AlignReference, id=entity.id, type=folia.Entity)
                folia_dependency.append(hd)
                for arg in event_rel[entity.id].args:
                    dep = folia.DependencyDependent(doc, contents=doc[arg[1]].wrefs())
                    dep.append(folia.Feature(doc,subset=event_rel[entity.id].type, cls=str(arg[0])))
                    al = dep.append(folia.Alignment)
                    al.append(folia.AlignReference, id=arg[1], type=folia.Entity)
                    folia_dependency.append(dep)
                dependencies.append(folia_dependency)
    if dependencies:
        dependenciesLayer = folia_structure.append(folia.DependenciesLayer, contents=dependencies)


        
            
def add_relations(doc,ann):
    relations,equivs,event_rel = build_relations(ann)
    doc.annotationdefaults[folia.AnnotationType.DEPENDENCY] = {"relation_set.xml": {} }
    doc.annotations.append( (folia.AnnotationType.DEPENDENCY, "relation_set.xml" ) ) 
    for texts in doc.data:
        for par in doc.paragraphs():
            for sentence in par.sentences():
                layers = sentence.layers(folia.AnnotationType.ENTITY)
                add_relations_to_layer(sentence,layers,relations,doc)
                add_equivs_to_layer(sentence,layers,equivs,doc)
                add_event_rel_to_layer(sentence,layers,event_rel,doc)
            layers = par.layers(folia.AnnotationType.ENTITY)
            add_relations_to_layer(par,layers,relations,doc)
            add_equivs_to_layer(par,layers,equivs,doc)
            add_event_rel_to_layer(par,layers,event_rel,doc)
    layers = texts.layers(folia.AnnotationType.ENTITY)
    add_relations_to_layer(texts,layers,relations,doc)
    add_equivs_to_layer(texts,layers,equivs,doc)
    add_event_rel_to_layer(texts,layers,event_rel,doc)

def add_comments(doc, ann):
    for a in ann.get_oneline_comments():
        desc = folia.Description(doc,value=a.tail.strip())
        doc[a.target].append(desc)
        
def convert(path,doc):
    #path is path to the file without extension
    projectconf = ProjectConfiguration(path)
    path = path_join(path,doc)
    ann = Annotations(path+".ann")
    doc = build_text_structure(ann,path+".txt")
    add_relations(doc,ann)
    add_comments(doc,ann)
    #~ ent_set=xml(build_entity_set(doc))
    #~ rel_set=xml(build_relations_set(doc))
    #~ temp=open ("entiteit_set.xml",'w')
    #~ temp.write(ent_set)
    #~ temp.close()
    #~ rel=open ("relation_set.xml",'w')
    #~ rel.write(rel_set)
    #~ rel.close()
    doc.save(path+".xml")


def build_entity_set(doc, projectconf):
    #build a folia set for entities
    # dictionary so only unique id's are added
    classes={}
    subsets=[]
    for types in projectconf.get_entity_types():
        classes[types]=folia.ClassDefinition(types,folia.SetType.CLOSED,types)
    for event in projectconf.get_event_types():
        classes[event]=folia.ClassDefinition(event,folia.SetType.CLOSED,event)
    for t in projectconf.get_attribute_type_hierarchy():
        subset_classes ={}
        if "Value" in t.arg_list:
            for i in t.arguments["Value"]:
                subset_classes[i] = folia.ClassDefinition(i,folia.SetType.CLOSED,i)
            subsets.append(folia.SubsetDefinition(t.terms[0], folia.SetType.CLOSED, subset_classes))
        else:
            subsets.append(folia.SubsetDefinition(t.terms[0], folia.SetType.OPEN, subset_classes))
    setdef = folia.SetDefinition("entiteit_set",classes,subsets)
    doc.setdefinitions["entiteit_set.xml"] = setdef
    return setdef
    
def build_relations_set(doc,projectconf):
    #build a folia set for dependencies
    classes={}
    subsets=[]
    for types in projectconf.get_relation_types():
        classes[types]=folia.ClassDefinition(types,folia.SetType.CLOSED,types)
    events = projectconf.get_event_type_hierarchy()
    if events:
        classes["Event"]=folia.ClassDefinition("Event",folia.SetType.CLOSED,"Event")
        for t in projectconf.get_event_type_hierarchy():
            subset_classes ={}
            for c in t.arg_list:
                if c == t.terms[0]:
                    c=t.terms[0] + "1"
                subset_classes[c] = folia.ClassDefinition(c,folia.SetType.CLOSED,c)
            subsets.append(folia.SubsetDefinition(t.terms[0], folia.SetType.CLOSED, subset_classes))
    setdef = folia.SetDefinition("relation_set",classes,subsets)
    doc.setdefinitions["relation_set.xml"] = setdef
    return setdef
    
def xml(sett):
    #takes a folia SetDefenition and will return a xml string 
    from lxml import etree
    import string
    xml_id = '{http://www.w3.org/XML/1998/namespace}id'
    NSFOLIA="http://ilk.uvt.nl/folia"
    root = etree.Element('set',{xml_id:sett.id, "type":"closed" }, namespace=NSFOLIA, nsmap={None: NSFOLIA, 'xml' : "http://www.w3.org/XML/1998/namespace"})
    for clas in sett.classes:
        root.append(etree.Element('class',{xml_id:sett.classes[clas].id, "label":sett.classes[clas].label }))
    for subset in sett.subsets:
        if subset.type == folia.SetType.CLOSED:
            ss = etree.Element('subset',{xml_id:subset.id, "class":"closed" })
        if subset.type == folia.SetType.OPEN:
            ss = etree.Element('subset',{xml_id:subset.id, "class":"open" })
        for sc in subset.classes:
            clas = subset.classes[sc]
            if(clas.id[0] == "_" or clas.id[0] in string.lowercase or clas.id[0] in string.uppercase):
                ss.append(etree.Element('class',{xml_id:clas.id, "label":clas.label}))
        root.append(ss)
    return etree.tostring(root, pretty_print=True)
    
def compare(path,doc):
    convert(path,doc)
    ann = Annotations(path+doc)
    fdoc = folia.Document(file=path+doc+".xml")
    #test entities
    for ent in ann.get_textbounds():
        try:
            found=fdoc[ent.id]
            text = [str(a) for a in found.wrefs()]        
            if ent.tail.strip() != " ".join(text):
                print "error: not found entity"
                print ent
                return False
        except KeyError:
            print "error: not found entity"
            print ent
            return False
    #test relations
    for rel in ann.get_relations():
        try:
            found=fdoc[rel.id]
            arefs = found.select(folia.AlignReference)
            if  not (any(a.id == rel.arg1 for a in arefs) and any(a.id == rel.arg2 for a in arefs)):
                print "error: not found relation"
                print rel
                return False
        except KeyError:
            print "error: not found relation"
            print rel
            return False
    #test events
    for event in ann.get_events():
        try:
            found=fdoc[event.id]
            arefs = found.select(folia.AlignReference)
            for role,rid in event.args:
                if  not any(a.id == rid for a in arefs) :
                    print "error: not found relation"
                    print rel
                    return False
        except KeyError:
            print "error: not found relation"
            print rel
            return False
    #test attributes
    for attr in ann.get_attributes():
        try:
            found=fdoc[attr.target]
            if  not any(fattr.cls == str(attr.value) and fattr.subset == attr.type for fattr in found.select(folia.Feature)) :
                print "error: not found attr"
                print attr
                print 
                return False
        except KeyError:
            print "error: not found attr"
            print rel
            return False
        
    print "file "+path+doc+" is OK"
    return True
            
       
if __name__ == '__main__':
    #convert("/home/sander/Documenten/Masterproef/pythontest/","folia")
    convert("/home/sander/Documents/Masterproef-v2/brat/data/brat_vb/sentiment/","sporza")
    ann = TextAnnotations("/home/sander/Documents/Masterproef-v2/brat/data/brat_vb/sentiment/sporza")
    #print ann._document_text
    #~ compare("/home/sander/Downloads/brat/data/testen/sentiment/","detijd_other_Bekaert_12-05-05")
    #~ compare("/home/sander/Downloads/brat/data/testen/sentiment/","detijd_other_bedrijfMulti_06-05-05")
    #~ compare("/home/sander/Downloads/brat/data/testen/vertaling/","1722_all_+DM")
    #~ compare("/home/sander/Downloads/brat/data/testen/sentiment/","testdoc")
    print "saved"
    #folia.validate("/home/sander/Documenten/Masterproef/pythontest/detijd_other_Bekaert_12-05-05.xml",deep="true")

    
    
