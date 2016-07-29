#!/usr/bin/python
# $Id$
#
# Author: Alcione de Paiva Oliveira
# version: 0.9.9
# Date : 28 jul 2016
#
# Description:
# Create a XML model for the Flame GPU model based on a json specification.
#
#---------------------------------------------------------------------
#
# input arguments
# Example python3 modelgen.py file.json

import sys, math
import json

maxsize = 0
model = {}
substances=[]
env=[]
agents ={}
agentsnames=[]
messages=[]
agfunctions=[]
layers={'moving':[],'mov2em':[],'emiting':[],'em2sen':[],'sensing':[],'sen2act':[],'acting':[],'act2mov':[]}

def printTissueAg():
    global env
    global substances
    print("""
    <gpu:xagent>
      <name>TissueCell</name>
      <memory>
        <gpu:variable>
          <type>int</type>
          <name>x</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>y</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>agent_id</name>
        </gpu:variable>

        <!-- agent specific variables-->
        <gpu:variable>
          <type>int</type>
          <name>debug</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>state</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>status</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>timecount</name>
        </gpu:variable>""")

    print("""
        <!-- message specific variables-->""")
    for sub in substances:
        print("""
        <gpu:variable>
          <type>int</type>
          <name>%s_x</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>%s_y</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>%s_value</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>%s_time</name>
        </gpu:variable>""" % (sub,sub,sub,sub))

    pathogens = env['pathogens']
    for pat in pathogens:
        print("""
      </memory>

      <functions>

        <gpu:function>
          <name>TissueCell_input_%s</name>
          <description>checks others agents</description>
          <currentState>default</currentState>
          <nextState>default</nextState>
          <inputs>
            <gpu:input>
              <messageName>%sInfo</messageName>
            </gpu:input>
          </inputs>
          <gpu:reallocate>false</gpu:reallocate>
          <gpu:RNG>false</gpu:RNG>
        </gpu:function>""" % (pat,pat))

    for sub in substances:
        print("""
        <gpu:function>
          <name>TissueCell_input_%s</name>
          <description>checks environment</description>
          <currentState>default</currentState>
          <nextState>default</nextState>
          <inputs>
            <gpu:input>
              <messageName>%s</messageName>
            </gpu:input>
          </inputs>
          <gpu:reallocate>false</gpu:reallocate>
          <gpu:RNG>false</gpu:RNG>
        </gpu:function>

        <gpu:function>
          <name>TissueCell_output_%s</name>
          <description>outputs the state of the TissueCell</description>
          <currentState>default</currentState>
          <nextState>default</nextState>
          <outputs>
            <gpu:output>
              <messageName>%s</messageName>
              <gpu:type>single_message</gpu:type>
            </gpu:output>
          </outputs>
          <gpu:reallocate>false</gpu:reallocate>
          <gpu:RNG>false</gpu:RNG>
        </gpu:function>""" % (sub,sub,sub,sub))

    print("""
      </functions>

      <states>
        <gpu:state>
          <name>default</name>
        </gpu:state>
        <initialState>default</initialState>
      </states>

      <gpu:type>discrete</gpu:type>
      <gpu:bufferSize>%d</gpu:bufferSize>
    </gpu:xagent>""" % (maxsize*maxsize))


def initModule(arq):
    global model
    try:
        with open(arq, 'r') as fp1:
           model = json.load(fp1)
           return True
    except IOError:
        print ('file %s not found' % arq, file=sys.stderr)
        return False

def printpreambule():
    print("""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<gpu:xmodel xmlns:gpu=\"http://www.dcs.shef.ac.uk/~paul/XMMLGPU\"
    xmlns=\"http://www.dcs.shef.ac.uk/~paul/XMML\">""")

def printenv():
    env = model['environment']
    tam = env['size']
    print("""
  <name>Body</name>
    <gpu:environment>
      <gpu:constants>
          <gpu:variable>
             <type>int</type>
             <name>size</name>
         </gpu:variable>
         <gpu:variable>
             <type>int</type>
             <name>itEquiv</name>
         </gpu:variable>
      </gpu:constants>

      <gpu:functionFiles>
        <file>functions.c</file>
      </gpu:functionFiles>
      <gpu:initFunctions>
          <gpu:initFunction>
            <gpu:name>setConstants</gpu:name>
        </gpu:initFunction>
      </gpu:initFunctions>
    </gpu:environment>""")


def parseCond(cond):
    cond = cond.replace('true','1')
    cond = cond.replace('false','0')
    lista = cond.split(' and')
    lista = lista[0].split('=')
    return lista

def printagfunctionsAndStates(name):
    global model
    global messages
    global agents
    global agentsnames
    global layers
    global substances

    moves = False

    inputs = agents[name]['inputs']
    actions = agents[name]['actions']

    print("""
          <functions>""")
    actionl = []
    #######################################################
    # printing the general processing funcion
    #######################################################
    layers['acting'].append(name+"_"+"processing")
    print("""
    <gpu:function>
      <name>%s_processing</name>
      <description> Process the memory</description>
      <currentState>%sActing</currentState>
      <nextState>%sActing</nextState>
      <gpu:reallocate>false</gpu:reallocate>
      <gpu:RNG>true</gpu:RNG>
    </gpu:function>""" % (name,name,name))
    #######################################################
    # printing the specific functions
    #######################################################

    for action in actions:
        actioname = action['name']
        actionl.append(actioname)
        statename = name+"Acting"
        rng="false"
        if actioname=='move' or actioname=='directedMove':
            rng="true"
            moves=True
            statename = name+"Moving"
            layers['moving'].append(name+"_"+actioname)
        else:
            layers['acting'].append(name+"_"+actioname)

        agfunctions.append(name+"_"+actioname)

        if actioname=='die':
            print("""
            <gpu:function>
              <name>%s_%s</name>
              <description> %s %s</description>
              <currentState>%s</currentState>
              <nextState>%sDying</nextState>""" % (name,actioname,actioname,name,statename,name))
        else:
            print("""
            <gpu:function>
              <name>%s_%s</name>
              <description> %s %s</description>
              <currentState>%s</currentState>
              <nextState>%s</nextState>""" % (name,actioname,actioname,name,statename,statename))
        if actioname=='divide':
            rng="true"
            print("""
              <xagentOutputs>
                <gpu:xagentOutput>
                  <xagentName>%s</xagentName>
                  <state>%s</state>
                </gpu:xagentOutput>
              </xagentOutputs>""" %(name,statename))

        if 'precond' in action.keys():
            precond = action['precond']
            condParsed = parseCond(precond)
#            print("precond:",condParsed, file=sys.stderr)
            print("""
              <condition>
                <lhs>
                  <agentVariable>%s</agentVariable>
                </lhs>
                <operator>==</operator>
                <rhs>
                  <value>%s</value>
                </rhs>
              </condition>""" %(condParsed[0],condParsed[1]))

        if actioname=='die':
            print("""
              <gpu:reallocate>true</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""")
        else:
            print("""
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>%s</gpu:RNG>
            </gpu:function>""" % (rng))

    #######################################################
    # printing the standard functions
    #######################################################
    layers['emiting'].append(name+"_output")

    print("""
            <gpu:function>
              <name>%s_output</name>
              <description> %s output info</description>
              <currentState>%sEmiting</currentState>
              <nextState>%sEmiting</nextState>
              <outputs>
                <gpu:output>
                  <messageName>%sInfo</messageName>
                  <gpu:type>single_message</gpu:type>
                </gpu:output>
              </outputs>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,name,name,name,name))

    for sub in substances:
        if sub in inputs:
            layers['sensing'].append(name+"_input_"+sub)

            print("""
            <gpu:function>
              <name>%s_input_%s</name>
              <description> %s input %s</description>
              <currentState>%sSensing</currentState>
              <nextState>%sSensing</nextState>
              <inputs>
                <gpu:input>
                  <messageName>%s</messageName>
                  <gpu:type>single_message</gpu:type>
                </gpu:input>
              </inputs>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,sub,name,sub,name,name,sub))

    for agname in agentsnames:
        if agname in inputs:
            layers['sensing'].append(name+"_input_"+agname)

            print("""
            <gpu:function>
              <name>%s_input_%s</name>
              <description> %s input agents info</description>
              <currentState>%sSensing</currentState>
              <nextState>%sSensing</nextState>
              <inputs>
                <gpu:input>
                  <messageName>%sInfo</messageName>
                  <gpu:type>single_message</gpu:type>
                </gpu:input>
              </inputs>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,agname,name,name,name,agname))

    #######################################################
    # printing the transition functions
    #######################################################
    if moves:
        layers['mov2em'].append(name+"_MovingToEmiting")
        print("""
            <gpu:function>
              <name>%s_MovingToEmiting</name>
              <description>change state Moving To Emiting</description>
              <currentState>%sMoving</currentState>
              <nextState>%sEmiting</nextState>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,name,name))

    layers['em2sen'].append(name+"_EmitingToSensing")
    print("""
            <gpu:function>
              <name>%s_EmitingToSensing</name>
              <description>change state Emiting To Sensing</description>
              <currentState>%sEmiting</currentState>
              <nextState>%sSensing</nextState>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,name,name))

    layers['sen2act'].append(name+"_SensingToActing")
    print("""
            <gpu:function>
              <name>%s_SensingToActing</name>
              <description>change state Sensing To Acting</description>
              <currentState>%sSensing</currentState>
              <nextState>%sActing</nextState>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,name,name))

    if moves:
        layers['act2mov'].append(name+"_ActingToMoving")
        print("""
            <gpu:function>
              <name>%s_ActingToMoving</name>
              <description>change state Acting To Moving</description>
              <currentState>%sActing</currentState>
              <nextState>%sMoving</nextState>
              <gpu:reallocate>false</gpu:reallocate>
              <gpu:RNG>false</gpu:RNG>
            </gpu:function>""" % (name,name,name))

    print("""
          </functions>""")

    print("""
          <states>""")
    if moves:
        print("""
            <gpu:state>
              <name>%sMoving</name>
            </gpu:state>""" % name)
    if 'die' in actionl:
        print("""
            <gpu:state>
              <name>%sDying</name>
            </gpu:state>""" % name)
    print("""
            <gpu:state>
              <name>%sEmiting</name>
            </gpu:state>
            <gpu:state>
              <name>%sSensing</name>
            </gpu:state>
            <gpu:state>
              <name>%sActing</name>
            </gpu:state>""" % (name,name,name))
    if moves:
        print("""
            <initialState>%sMoving</initialState>""" % (name))
    else:
        print("""
            <initialState>%sEmiting</initialState>""" % (name))

    print("""
          </states>

          <gpu:type>continuous</gpu:type>
          <gpu:bufferSize>%s</gpu:bufferSize>""" % (agents[name]['max']))

def printMessages():
    global maxsize
    global substances
    global agents
    global agentsname

    print("""
  <messages>""")

    for sub in substances:
        print("""
    <gpu:message>
      <name>%s</name>
      <variables>
        <gpu:variable>
          <type>int</type>
          <name>x</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>y</name>
        </gpu:variable>

        <gpu:variable>
          <type>int</type>
          <name>%s_x</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>%s_y</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>%s_time</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>%s_value</name>
        </gpu:variable>
      </variables>
     <gpu:partitioningDiscrete>
        <gpu:radius>1</gpu:radius>
      </gpu:partitioningDiscrete>
      <gpu:bufferSize>%d</gpu:bufferSize>
    </gpu:message>""" % (sub,sub,sub,sub,sub,maxsize*maxsize))


    for agname in agentsnames:
        print("""
    <gpu:message>
      <name>%sInfo</name>
      <variables>
        <gpu:variable>
          <type>float</type>
          <name>x</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>y</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>z</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>type</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>ivalue</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>value</name>
        </gpu:variable>

      </variables>
      <gpu:partitioningSpatial>
        <gpu:radius>1.0</gpu:radius>
        <gpu:xmin>0.0</gpu:xmin>
        <gpu:xmax>%d.0</gpu:xmax>
        <gpu:ymin>0.0</gpu:ymin>
        <gpu:ymax>%d.0</gpu:ymax>
        <gpu:zmin>0.0</gpu:zmin>
        <gpu:zmax>1.0</gpu:zmax>
       </gpu:partitioningSpatial>
      <gpu:bufferSize>%s</gpu:bufferSize>
    </gpu:message>"""  % (agname,maxsize,maxsize, (agents[agname]['max'])))

    print("""
  </messages>""")

def printMemory(agentsname):
    global substances
    memos = agents[agentsname]['memory']
    inputs = agents[agentsname]['inputs']
    print("""
      <memory>
         <gpu:variable>
           <type>float</type>
           <name>x</name>
         </gpu:variable>
         <gpu:variable>
          <type>float</type>
          <name>y</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>z</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>agent_id</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>type</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>pattern</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>state</name>
        </gpu:variable>
        <gpu:variable>
          <type>int</type>
          <name>nearagents</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>value</name>
        </gpu:variable>""")
    for memo in memos:
        tipo = memo["type"]
        if tipo == "position":
            print("""
        <gpu:variable>
          <type>float</type>
          <name>%s_target_x</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>%s_target_y</name>
        </gpu:variable>""" % (memo["name"],memo["name"]))
        else:
            if tipo == "bool":
                tipo = "int"
            print("""
        <gpu:variable>
          <type>%s</type>
          <name>%s</name>
        </gpu:variable>""" % (tipo,memo["name"]))

    for input in inputs:
        print("""
        <gpu:variable>
          <type>float</type>
          <name>%s_x</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>%s_y</name>
        </gpu:variable>
        <gpu:variable>
          <type>float</type>
          <name>%s_value</name>
        </gpu:variable> """ % (input,input,input))


    print("""
      </memory>""")

def printagents():
    global model
    global messages
    global agents
    global agentsnames

    print("""
    <xagents>""")
    printTissueAg()
    for agentsname in agentsnames:
        print("""
        <!-- +++++++++++++++++++++++++++++++++++++++++++++++
                %s
             +++++++++++++++++++++++++++++++++++++++++++++++ -->
        <gpu:xagent>
          <name>%s</name>""" % (agentsname, agentsname))
        printMemory(agentsname)
        printagfunctionsAndStates(agentsname)
# print functions

        print("""
        </gpu:xagent>""")

    print("""
    </xagents>""")


def printend():
    print("""</gpu:xmodel>""")

def printLayers():
    global layers
    global substances

    # layers={'moving':[],'mov2em':[],'emiting':[],'em2sen':[],'sensing':[],'sen2act':[],'acting':[],'act2mov':[]}

#    print(layers)
    print("""
 <layers>""")

    lista = layers['moving']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['mov2em']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['emiting']
    print("""
    <layer>""")
    for sub in substances:
        print("""
      <gpu:layerFunction>
        <name>TissueCell_output_%s</name>
      </gpu:layerFunction>""" % (sub))
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['em2sen']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['sensing']
    pathogens = env['pathogens']
    print("""
    <layer>""")
    for pat in pathogens:
        print("""
      <gpu:layerFunction>
        <name>TissueCell_input_%s</name>
      </gpu:layerFunction>""" % (pat))
    for sub in substances:
        print("""
      <gpu:layerFunction>
        <name>TissueCell_input_%s</name>
      </gpu:layerFunction>""" % (sub))
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['sen2act']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['acting']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    lista = layers['act2mov']
    print("""
    <layer>""")
    for fun in lista:
        print("""
      <gpu:layerFunction>
        <name>%s</name>
      </gpu:layerFunction>""" % (fun))
    print("""
    </layer>""")

    print("""
  </layers>""")


def printXmlModel():
    printpreambule()
    printenv()
    printagents()
    printMessages()
    printLayers()
    printend()

if __name__ == '__main__':
    if len(sys.argv) < 2:
       print ("Usage:", sys.argv[0]," file.json")
       sys.exit(1)

    arq =sys.argv[1]
    if not initModule(arq):
        sys.exit(1)

    env = model['environment']

    size = env["size"]
    maxsize = int(size[:2])

    if size.endswith("mm"):
       maxsize= pow(2,math.ceil(math.log(maxsize/0.03,2)))
    else:
       maxsize= pow(2,math.ceil(math.log(maxsize/0.3,2)))

    for key in model:
        element = model[key]
        chaves = element.keys()
        if 'type' in chaves and element['type'] == 'agent':
            agentsnames.append(key)

    for key in model:
        element = model[key]
        chaves = element.keys()
        if 'type' in chaves and element['type'] == 'substance':
            substances.append(key)

#    print(substances, file=sys.stderr)

    for key in model:
        if key in agentsnames:
            agents[key]= model[key]


    printXmlModel()
