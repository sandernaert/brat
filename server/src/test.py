from message import Messager
from validation_rule import ValidationRules
from projectconfig import ProjectConfiguration
from annotation import Annotations,TextLevelAnnotation,SimpleAnnotations,TextAnnotations
from validation_rule import ValidationRules
from ApplicationScope import getAnnObject, getAnnObject2,getDocJson
import projectconfig
from document import get_document
	
def select_layers():
	forbidden_ann = ["PolarExpr","in_span_with"]
	ann = Annotations("/home/sander/Downloads/brat/data/brat_vb/sentiment/detijd_other_bedrijfMulti_06-05-05")
	proj = ProjectConfiguration("/home/sander/Downloads/brat/data/brat_vb/sentiment")
	for a in ann:
		print a.get_deps()[1]
		if "T1" in a.get_deps()[1]:
			print "test"
		print a
	#~ print proj.arc_types_from("Entity")
	#~ print proj.relation_types_to("Entity", True)
	#~ for event in proj.get_event_types():
		#~ print proj.arc_types_from_to(event,"Entity", True)
	#~ print proj.attributes_for("Entity")
	
def test():
	try:
		from cPickle import dump as pickle_dump, load as pickle_load, dumps
	except ImportError:
		from pickle import dump as pickle_dump, load as pickle_load
	ann = TextAnnotations("/home/hast/Downloads/brat/data/brat_vb/sentiment/test")
	temp=open ("/home/hast/Downloads/brat/work/brat_vbsentimenttest", 'wb')
	sann = SimpleAnnotations(ann)
	pickle_dump(sann,temp)
	temp.close()
	
	#_json_from_ann(sann)
	#~ temp=open ("pickletest.txt", 'wb')
	#~ pickle_dump(sann,temp)
	#~ temp.close()
	
def test_createSpan():
    from annotator_cachen import create_span, delete_span
    #from annotator import create_span, delete_span
    create_span("/brat_vb/","detijd_other_Bekaert_12-05-05",'[[12,25]]', "PolarExpr",'{"Type": "2"}')
    #delete_span("/brat_vb/","detijd_other_Bekaert_12-05-05","T255")
def speed_test():
    from document import get_document
    from validation_rule import build_connections, ValidationRules,extend_arg
    from verify_annotations import verify_annotation
    import time
    millis = int(round(time.time() * 1000))
    #test_createSpan()
    #result = get_document("/brat_vb/sentiment/","huge")
    result = getDocJson("/brat_vb/sentiment/","huge")
    millis = int(round(time.time() * 1000)) - millis
    print millis
    #print result
    return millis
	
#~ def ann_json(ann_obj):
	#~ from annotator import _json_from_ann
	#~ return _json_from_ann(ann_obj)
	#~ 
	#~ 
#~ def test_exit():
	#~ import time
	#~ millis = int(round(time.time() * 1000))
	#~ print millis
	#~ millis = int(round(time.time() * 1000)) - millis
	#~ with TextAnnotations("/home/hast/Downloads/brat/data/brat_vb/sentiment/test") as ann:
		#~ millis = int(round(time.time() * 1000))
		#~ print millis
		#~ ann.get_ann_by_id('A1').value = 3
	#~ millis = int(round(time.time() * 1000))
	#~ print millis
	#~ 
	
if __name__ == '__main__':
    speed_test()
    #~ ann = Annotations("/home/sander/Documents/Masterproef/brat/data/brat_vb/sentiment/sporza")
    #~ print ann.get_textLevels()[0]


