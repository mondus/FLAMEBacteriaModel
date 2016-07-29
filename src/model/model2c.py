#!/usr/bin/python
# $Id$
#
# Author: Alcione de Paiva Oliveira
# version: 0.9.12
# Date : 28 july 2016
#
# Description:
# Create c functions from the Flame GPU model file.
#
# input arguments
# Example python3 model2c.py  XMLModelFile.xml model.json

import getopt, sys, math
import json
from random import randint
from xml.dom.minidom import parse
import xml.dom.minidom

funcOrder =[]
previousState =[]
afterState=[]
conditions=[]
mes = []
memory = []
substances=[]
agentsnames=[]
model={}

agents     = type(xml.dom.minicompat.NodeList)
layers     = type(xml.dom.minicompat.NodeList)
collection = type(xml.dom.minidom.Element)

#---------------------------------------------------------------------
#    Get node in text format
#---------------------------------------------------------------------
def getNodeText(node):
    nodelist = node.childNodes
    result = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            result.append(node.data)
    return ''.join(result)

#---------------------------------------------------------------------
#    get actions names from model
#---------------------------------------------------------------------
def getActionsAg(agent):
    global model
    listaAc = []
    actions = model[agent]["actions"]
    for action in actions:
        listaAc.append(action["name"])

    return listaAc

#---------------------------------------------------------------------
#    get action by its name
#---------------------------------------------------------------------
def getActionByname(agent,name):
    global model
    listaAc = []
    actions = model[agent]["actions"]
    for action in actions:
        if action["name"] == name:
            return action
    return {}

#---------------------------------------------------------------------
#    Get condition in text format
#---------------------------------------------------------------------
def getCondition(node):
    globalCond = False
    condT = (node.getElementsByTagName('condition'))
    if (not condT):
       condT = (node.getElementsByTagName("gpu:globalCondition"))
       if (not condT):
           return ""
       else:
           globalCond = True

    lhsNode = node.getElementsByTagName('lhs')[0].getElementsByTagName('agentVariable')
    if (lhsNode):
        lhs = getNodeText(lhsNode[0])
    else:
        lhs = getNodeText(node.getElementsByTagName('lhs')[0].getElementsByTagName('value')[0])

    rhsNode = node.getElementsByTagName('rhs')[0].getElementsByTagName('agentVariable')
    if (rhsNode):
        rhs = getNodeText(rhsNode[0])
    else:
        rhs = getNodeText(node.getElementsByTagName('rhs')[0].getElementsByTagName('value')[0])

    operator = getNodeText(node.getElementsByTagName('operator')[0])
    if (operator == "&lt;"):
        operator = "<"
    elif (operator == "&le;"):
        operator = "<="
    elif (operator == "&gt;"):
        operator = ">"
    elif (operator == "&ge;"):
        operator = ">="

    if (globalCond):
        return "[ label =\"global :"+ lhs+operator+rhs+"\"]"
    return "[ label =\""+ lhs+operator+rhs+"\"]"

#---------------------------------------------------------------------
#    Get the functions that are defined in the layers
#---------------------------------------------------------------------
def getFuncLayers():
  global layers
  global funcOrder
  global previousState
  global afterState
  global conditions
  # Get a list of the function execution in the correct order
  for layer in layers:
     nomeFuncLayer = (layer.getElementsByTagName('name')[0]).childNodes[0].data
     funcOrder.append(nomeFuncLayer)
     previousState.append("")
     afterState.append("")
     conditions.append("")
     #print ("Function:%s\n" % (nomeFuncLayer), file=sys.stderr)

#---------------------------------------------------------------------
#    print the utilities functions
#---------------------------------------------------------------------
def printUtilFunc():
    print("/**************************************")
    print("    UTIL FUNCTIONS")
    print("**************************************/")
    print("""__FLAME_GPU_FUNC__ float dist(int x, int y, int x1, int y1){
    return sqrtf((x - x1)*(x - x1) + (y - y1)*(y - y1));
}

__FLAME_GPU_FUNC__ int dotprod(int x, int y, int x1, int y1, int ox, int oy){
    return (x - ox)*(x1 - ox) + (y - oy)*(y1 - oy);
}
""")
    print("////////////////////////////////////////////////////////////////////////////\n")
    print("""
__FLAME_GPU_FUNC__ int newMsg(xmachine_memory_TissueCell* agent, int x, int y, int ox, int oy){
    float distAgent = 0.0;
    float distAnt = 0.0;
    float dotprod = 0.0;
    float cosAB = 0.0;

    distAgent = dist(agent->x, agent->y, ox,oy);
    distAnt = dist(x, y, ox, oy);
    dotprod = (agent->x - ox)*(x - ox) + (agent->y - oy)*(y - oy);
    cosAB = distAnt !=0.0 ? dotprod / (distAgent*distAnt): 1.0;
	if (distAgent > distAnt+0.5 && cosAB > 0.98) {
		return 1;
	}
    return 0;
}""")

    print("""////////////////////////////////////////////////////////////////////////////
__FLAME_GPU_FUNC__ int receptorMatch(int p1, int p2){
   int p3 = ~(p1^p2);

   int count = 0;
   int max   = 0;
   int i;
   for ( i=0;i<sizeof(int)*8;i++)
   {
       if (p3 & 1)
           count++;
       else
           if (count>max)
           {
              max   = count;
              count = 0;
           }
       p3 >>= 1;
   }
   if (count>max)  max   = count;

   return max;
}""")

#---------------------------------------------------------------------
#    print divide function
#---------------------------------------------------------------------
def printDivide(nameFunc,name):
    global memory
    global model
    global substances
    prob = "0.5"
    nameSub = "-"
    action = getActionByname(name,nameFunc.split("_")[1])
    for sub in substances:
        if sub in action.keys():
            val = action[sub]
            nameSub = sub
            prob = str((100+int(val))/100)
#    print("memoria:",memory, file=sys.stderr)
    print("""
__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, xmachine_memory_%s_list*  %s_agents, RNG_rand48* rand48){
	int dt = agent->dividingTime;
    float divideProb = 0.9f; """ % (nameFunc,name,name,name))
    if nameSub != "-":
        print("""    if (agent->%s_value >0.0) divideProb = %s;""" % (nameSub,prob))
    print("""
    if (dt == 1) {
		if (rnd(rand48)<divideProb) {
			add_%s_agent(
				%s_agents""" % (name,name))
    for variable in memory:
        print("""                ,agent->%s """ % (variable))
    print("""				);
		}
	}
    return 0;
} """ )

#---------------------------------------------------------------------
#    print die function
#---------------------------------------------------------------------
def printDie(nameFunc,name):
    global model
#    print("memoria:",memory, file=sys.stderr)
    print("""__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent){
    agent->state= DEAD;
    return 1;
} """ % (nameFunc,nome))

#---------------------------------------------------------------------
#    print Processing function
#---------------------------------------------------------------------
def printProcessing(nameFunc,name):
    global model
    print("""__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, RNG_rand48* rand48){""" % (nameFunc,nome))
    if "divide" in getActionsAg(name):
        print("    agent->lifetime++;\n    agent->dividingTime=0;");
        dr = int((model[name]["properties"]["divisionRate"]).split('h')[0])*10
        print("""    if (agent->lifetime  %% %s == 0) agent->dividingTime=1;""" % (dr))
    print("""    return 0;
} """)

#---------------------------------------------------------------------
#    print move random function
#---------------------------------------------------------------------
def printMoveFun(nameFunc,name):
    print("""
__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, RNG_rand48* rand48){
	float x1 = agent->x;
	float y1 = agent->y;
	float ale = rnd(rand48);

	if (ale < 0.25f) {
		x1 = x1 <= 0.0 ? 0.0 : x1 - 1.0;
	}
	else if (ale <0.5f) {
		x1 = x1 >= XMAX ? XMAX : x1 + 1.0;
	}
	else if (ale <0.75f) {
		y1 = y1 >= YMAX ? YMAX : y1 + 1.0;
	}
	else  {
		y1 = y1 <= 0.0 ? 0.0 : y1 - 1.0;
	}

	agent->x = x1;
	agent->y = y1;
	return 0;
}""" % (nameFunc,name))

#---------------------------------------------------------------------
#    print direct move function
#---------------------------------------------------------------------
def printDirectMoveFun(nameFunc,name):
    global memory
    x=""
    y=""
    for m in memory:
        if m.endswith('_target_x'):
            x = m
        if m.endswith('_target_y'):
            y = m

    print("""
__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, RNG_rand48* rand48){

	/* these are the 'current' parameters*/
	float x1 = agent->x;
	float y1 = agent->y;
	float ale = rnd(rand48);

	if (ale < 0.25f) {
		x1 = x1 <= 0.0 ? 0.0 : x1 - 1.0;
	}
	else if (ale <0.5f) {
		x1 = x1 >= XMAX ? XMAX : x1 + 1.0;
	}
	else if (ale <0.75f) {
		y1 = y1 >= YMAX ? YMAX : y1 + 1.0;
	}
	else  {
		y1 = y1 <= 0.0 ? 0.0 : y1 - 1.0;
	}

	if (agent->%s != -1 && agent->%s != -1) {
		float dist1 = dist(agent->%s,agent->%s,agent->x,agent->y);
		if (dist1 > 5.0f) {
			float dist2 = dist(agent->%s,agent->%s,x1,y1);
			if (dist1 > dist2) {
				/* update memory with new parameters*/
				agent->x = x1;
				agent->y = y1;
			}
		}
		else {
			/* update memory with new parameters*/
			agent->x = x1;
			agent->y = y1;
		}
	}
	else {
		/* update memory with new parameters*/
		agent->x = x1;
		agent->y = y1;
	}
	return 0;
}
    """ % (nameFunc,name,x,y,x,y,x,y))

#---------------------------------------------------------------------
#    get the names of variables of a agent
#---------------------------------------------------------------------
def getMemoryAg(agent):
    global memory
    memory = []
    variables = agent.getElementsByTagName('memory')[0]
    vv = variables.getElementsByTagName("gpu:variable")
    for v in vv:
        name = (v.getElementsByTagName('name')[0]).childNodes[0].data
        memory.append(name)
#    print(memory, file=sys.stderr)

#---------------------------------------------------------------------
#                    INICIO
#---------------------------------------------------------------------
def printTissueFunc():
     global memory
     global model
     global agentsnames

     print("/**************************************")
     print("     Tissue cell functions" )
     print("**************************************/\n")

     pathogens = model['environment']['pathogens']

     for pat in pathogens:
         print("""
__FLAME_GPU_FUNC__ int TissueCell_input_%s(xmachine_memory_TissueCell* agent, xmachine_message_%sInfo_list* %s_messages, xmachine_message_%sInfo_PBM *pbm){

    xmachine_message_%sInfo* current = get_first_%sInfo_message(%s_messages, pbm, (float)agent->x, (float)agent->y, 0.0);

	int status = 0;
    agent->timecount++;
    float value;
	while (current)
	{""" % (pat,pat,pat,pat,pat,pat,pat) )

         print("""
       status = 1;
	   value = current->value;
       current = get_next_%sInfo_message(current, %s_messages, pbm);
	}

	if (status ==1 ) {

		agent->citokine_x = agent->x;
		agent->citokine_y = agent->y;
	    agent->state = TS_SIGNALING;
		agent->citokine_value = value;
	}
    if (status ==0)  agent->state = TS_NORMAL;

	return 0;
}""" % (pat,pat) )


     print("////////////////////////////////////////////////////////////////////////////\n")

     for mem in memory:
         if not mem.endswith('_x'):
             continue
         sub = mem[:mem.find('_')]
         print("""
__FLAME_GPU_FUNC__ int TissueCell_output_%s(xmachine_memory_TissueCell* agent, xmachine_message_%s_list* %s_messages){ """
         % (sub,sub,sub))
         if mem in model["environment"].keys():
             print("""	if ( agent->timecount %% 50 ==0 && agent->%s_x == %s_X && agent->%s_y == %s_Y ) {""" % (sub,sub.upper(),sub,sub.upper()))
             print("""	   //agent->state = TS_SIGNALING; """)
             print("""	   agent->%s_x = %s_X; """ % (sub,sub.upper()))
             print("""	   agent->%s_y = %s_Y; """ % (sub,sub.upper()))
             print("""	   agent->%s_value = %s; """ % (sub,model[sub]["value"]))
             print("""	   agent->%s_time = agent->timecount; """ % (sub))
             print("	}" )
         print("""
	if (agent->%s_value > 0.0) {
		add_%s_message<DISCRETE_2D>(%s_messages, agent->x, agent->y, agent->%s_x, agent->%s_y, agent->%s_value, agent->%s_time);
	} else {
        agent->state = TS_NORMAL;
		add_%s_message<DISCRETE_2D>(%s_messages, agent->x, agent->y, -1, -1, 0.0, 0);
	}
    return 0;
}""" % (sub,sub,sub,sub,sub,sub,sub,sub,sub))
         print("////////////////////////////////////////////////////////////////////////////\n")
         print("""
__FLAME_GPU_FUNC__ int TissueCell_input_%s(xmachine_memory_TissueCell* agent, xmachine_message_%s_list* %ss){
	agent->%s_x = -1;
	agent->%s_y = -1;
	agent->%s_value = -1.0;
	agent->%s_time = -1;

	xmachine_message_%s* current = get_first_%s_message<DISCRETE_2D>(%ss, agent->x, agent->y);

    while (current)
    {
		if (newMsg(agent, current->x,current->y,current->%s_x,current->%s_y)==1) {
				agent->%s_x = current->%s_x;
				agent->%s_y = current->%s_y;
				agent->%s_value = current->%s_value;
				agent->%s_time = current->%s_time;
				//agent->state = TS_SIGNALING;
		}
        current = get_next_%s_message<DISCRETE_2D>(current, %ss);
    }
    return 0;
}""" % (sub,sub,sub,sub,sub,sub,sub,sub,sub,sub, sub,sub,sub,sub,sub,sub,sub,sub,sub,sub,sub,sub))

#---------------------------------------------------------------------
#                    Parse the precond to c
#---------------------------------------------------------------------
def parsePrecond(action):
    lista = action.split('=')
    right = lista[0]
    left = '0'
    if lista[1]=='true':
        left = '1'
    elif lista[1]=='value':
        left = 'current->value'
    return right+"="+left

#---------------------------------------------------------------------
#                    Parse the action to c
#---------------------------------------------------------------------
def parseAction(action, sub):
    lista = action.split('=')
    right = "agent->"+lista[0]
    left = '0'
    if lista[1]=='true':
        left = '1'
    elif lista[1]=='value':
        left = 'current->'+sub+'_value'
    return right+"="+left+";"

#---------------------------------------------------------------------
#       Print the funtion for setting global variables
#---------------------------------------------------------------------
def printSetConstFunc(intsize):
    global model

    print("""
__FLAME_GPU_INIT_FUNC__ void setConstants(){
     int size = %d;
}""" % (intsize))

#---------------------------------------------------------------------
#       Print the funtion for input
#---------------------------------------------------------------------
def printInputFunc(nome, nameFunc, inputs):
    global mes
    global substances
    global memory
    global model
    global agentsnames

    gpuIN = inputs[0].getElementsByTagName("gpu:input")[0]
    menName = getNodeText(gpuIN.getElementsByTagName("messageName")[0])

    if (menName not in mes):
        mes.append(menName)

    typemessage =""
    pm = ""
    z=""
    signature = "__FLAME_GPU_FUNC__ int "+nameFunc+"(xmachine_memory_"+nome+"* agent, xmachine_message_"+menName+"_list* "+menName+"_messages"
    if menName in substances:
        typemessage ="<CONTINUOUS>"
    else:
        signature = signature +",xmachine_message_"+menName+"_PBM* pm"
        pm =",pm"
        z=",0.0"
    if (rng == "false"):
        signature = signature +"){"
    else:
        signature = signature +", RNG_rand48* rand48){"
    print(signature)
    print("    xmachine_message_%s* current = get_first_%s_message%s(%s_messages%s, (float)agent->x, (float)agent->y%s);\n" % (menName,menName,typemessage,menName,pm,z))
    if  menName.endswith('Info'):
        print("    agent->nearagents = 0;"  )
    if menName in model.keys():
        print("    agent->%s_value = 0.0;" % menName )
    print("""    while (current)
    {""")
    if menName.endswith('Info'):
        print("       if (receptorMatch(agent->pattern, current->ivalue) >= THRESHOLD)   agent->nearagents |= current->type;"  )
    if 'citokine' == menName and 'infectionSite_target_x' in memory:
        print("       if (current->citokine_x != -1){")
        print("              agent->infectionSite_target_x = current->citokine_x;")
        print("              agent->infectionSite_target_y = current->citokine_y;")
    if menName in model.keys():
        print("             agent->%s_value=current->%s_value;" % (menName,menName))
    if 'citokine' == menName and 'infectionSite_target_x' in memory:
        print("       }")
    print("       current = get_next_%s_message%s(current, %s_messages%s);\n" % (menName,typemessage,menName,pm))
    print("    }")

    actions = model[nome]['actions']
    for action in actions:
        if 'agents' in action.keys():
            lagents = action['agents'].split(',')
            precond = action['precond']
            for agent in lagents:
                print("    if (%s & agent->nearagents) agent->%s;" % (agent.upper(),parsePrecond(precond)))

    print("    return 0;\n}")

#---------------------------------------------------------------------
#                    INICIO
#---------------------------------------------------------------------
# input arguments
# Example python3 model2c.py  XMLModelFile.xml model.json

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print ("Usage:", sys.argv[0]," <file>.xml <file>.json")
    sys.exit(1)

  entrada =sys.argv[1]
  if entrada.endswith(".json"):
      modelarq = entrada
      entrada = sys.argv[2]
  else:
      modelarq = sys.argv[2]

  DOMTree = xml.dom.minidom.parse(entrada)

  try:
      with open(modelarq, 'r') as fp1:
         model = json.load(fp1)
  except IOError:
    print ('file %s not found' % arq, file=sys.stderr)
    sys.exit(1)

  for key in model:
    element = model[key]
    chaves = element.keys()
    if 'type' in chaves and element['type'] == 'substance':
        substances.append(key)
    if 'type' in chaves and element['type'] == 'agent':
        agentsnames.append(key)

  print("#ifndef _FUNCTIONS_H_\n#define _FUNCTIONS_H_\n\n#include \"header.h \"\n")
  print("""
// Tissue cells states
#define TS_NORMAL    1
#define TS_SIGNALING 2

#define DEAD         3
#define THRESHOLD    1
""")

  index = 0
  while index < len(agentsnames):
      print("""#define %s %d""" %(agentsnames[index].upper(),pow(2,index)))
      index = index +1

  size = model["environment"]["size"]
  intsize = int(size[:2])

  if size.endswith("mm"):
      intsize= pow(2,math.ceil(math.log(intsize/0.03,2)))
  else:
      intsize= pow(2,math.ceil(math.log(intsize/0.3,2)))
#  print("size=",intsize,file=sys.stderr)

  print("""
// SIZE
#define XMAX  %s
#define YMAX  %s
""" % (intsize,intsize))

  for varenv in model["environment"].keys():
      if varenv.endswith("_x") or varenv.endswith("_y"):
          print("#define %s %s" % (varenv.upper(),str(randint(1,intsize))))


  # Open XML document using minidom parser
  collection = DOMTree.documentElement

  # Get all the agents in the collection
  agents = collection.getElementsByTagName("gpu:xagent")
  layers = collection.getElementsByTagName("gpu:layerFunction")

  # Get a list of the function execution in the correct order
  getFuncLayers()
  printSetConstFunc(intsize)
  printUtilFunc()

  # Print detail of each agent.
  for agent in agents:
     nome = (agent.getElementsByTagName('name')[0]).childNodes[0].data
     getMemoryAg(agent)
     if nome.startswith('TissueCell'):
         printTissueFunc()
         continue

     for childNode in (agent.getElementsByTagName('gpu:type')):
         agentType = getNodeText(childNode)
         if agentType in ['discrete','continuous']:
             break
     print ("agent: %s:%s" % (nome, agentType), file=sys.stderr)


     print("/**************************************")
     print("     %s functions" % (nome))
     print("**************************************/")

     funcs = agent.getElementsByTagName('functions')[0]
     funs = funcs.getElementsByTagName("gpu:function")
     for f in funs:
        noIO =True
        nameFunc = (f.getElementsByTagName('name')[0]).childNodes[0].data
        if (nameFunc not in funcOrder):
           print ('  warning : funtion %s is not in layers list.\n' % (nameFunc), file=sys.stderr)

#        print("Function:"+nameFunc, file=sys.stderr)
        condition = getCondition(f)
#        print("Condition:"+condition, file=sys.stderr)
        rngT = (f.getElementsByTagName('gpu:RNG'))
        if (rngT):
            rng = rngT[0].childNodes[0].data
        else:
            rng = "false"
  #      description = f.getElementsByTagName('description')[0]
        ist = (f.getElementsByTagName('currentState')[0]).childNodes[0].data
        fst = (f.getElementsByTagName('nextState')[0]).childNodes[0].data
  #      print ("Funcao: %s" % nameFunc, file=sys.stderr)

        # Store the states of each function
        try:
            previousState[funcOrder.index(nameFunc)] = nome+":"+ist
            afterState[funcOrder.index(nameFunc)]=nome+":"+fst
            conditions[funcOrder.index(nameFunc)]= condition
        except ValueError:
          print("***** The function %s is not in the layers!" % nameFunc, file=sys.stderr)

        outputs = f.getElementsByTagName('outputs')
        if (outputs.length>0):
            gpuOut = outputs[0].getElementsByTagName("gpu:output")[0]
            menName = getNodeText(gpuOut.getElementsByTagName("messageName")[0])

            if (menName not in mes):
                mes.append(menName)

            noIO = False
            if (rng == "false"):
                print("__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, xmachine_message_%s_list* %s_messages){\n" %(nameFunc,nome,menName,menName))
            else:
                print("__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, xmachine_message_%s_list* %s_messages, RNG_rand48* rand48){" %(nameFunc,nome,menName,menName))
            print("    add_%s_message(%s_messages, agent->x, agent->y, 0.0,agent->type, agent->pattern,agent->value);" % (menName, menName))
            print("    return 0;\n}")

        inputs = f.getElementsByTagName('inputs')
        if (inputs.length>0):
            noIO = False
            printInputFunc(nome, nameFunc, inputs)

        if (noIO == True):
            if nameFunc.endswith('_move'):
                printMoveFun(nameFunc,nome)
            elif nameFunc.endswith('_directedMove'):
                printDirectMoveFun(nameFunc,nome)
            elif nameFunc.endswith('_divide'):
                printDivide(nameFunc,nome)
            elif nameFunc.endswith('_die'):
                printDie(nameFunc,nome)
            elif nameFunc.endswith('_processing'):
                printProcessing(nameFunc,nome)
            else:
                if (rng == "false"):
                   print("__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent){\n" %(nameFunc,nome))
                else:
                   print("__FLAME_GPU_FUNC__ int %s(xmachine_memory_%s* agent, RNG_rand48* rand48){\n" %(nameFunc,nome))
                print("    return 0;\n}")
        print("////////////////////////////////////////////////////////////////////////////\n")

  print("#endif // #ifndef _FUNCTIONS_H_")

  #*****************************************************************************
  #                    Printing 0.xml file                                     #
  #*****************************************************************************
  initfile = open('0.xml', 'w')

  initfile.write("""
<states>
    <itno>0</itno>
    <environment>
    </environment>""")

  idmin = 0
  idag = idmin

  nstate=3
  for agent in agents:
     nome = (agent.getElementsByTagName('name')[0]).childNodes[0].data
     getMemoryAg(agent)
     if nome.startswith('TissueCell'):
        # creating TissueCell
        for l in range(0,int(intsize)):
           x = l
           for i in range (0,int(intsize)):
              y = i
              idag = idag+1
              initfile.write("""
    <xagent>
        <name>TissueCell</name>
        <x>%d</x>
        <y>%d</y>
        <agent_id>%d</agent_id>
        <debug>5</debug>
        <state>1</state>
		<status>0</status>
        <timecount>0</timecount>""" % (x,y,idag))

              for mem in memory:
                 if  mem in ["x","y","agent_id","debug","status","timecount","state"]:
                    continue
                 initfile.write("""
		<%s>-1</%s>""" % (mem,mem))
              initfile.write("""
    </xagent>""")
     # creating other agents
     else:
        nstate = nstate+1
        numberag = int(model[nome]["number"])
        agtype =pow(2,agentsnames.index(nome))
        for i in range(0,numberag):
           x = randint(2,intsize)
           y = randint(2,intsize)
           idag = idag+1
           initfile.write("""
    <xagent>
        <name>%s</name>
        <x>%d.5</x>
        <y>%d.5</y>
		<z>0.1</z>
        <agent_id>%d</agent_id>
		<type>%d</type>
		<pattern>%d</pattern>
        <state>%d</state>
        <timecount>0</timecount>""" % (nome,x,y,idag,agtype,x|1,nstate))

           for mem in memory:
              if  mem in ["x","y","z","agent_id","pattern","type","state"]:
                 continue
              initfile.write("""
		<%s>0</%s>""" % (mem,mem))
           initfile.write("""
    </xagent>
""")

  # End XML file and close
  initfile.write("</states>\n")
  initfile.close();
  print(idag," agents created!", file=sys.stderr)
  print ("DONE", file=sys.stderr)
