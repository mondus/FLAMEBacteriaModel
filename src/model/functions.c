#ifndef _FUNCTIONS_H_
#define _FUNCTIONS_H_

#include "header.h "


// Tissue cells states
#define TS_NORMAL    1
#define TS_SIGNALING 2

#define DEAD         3
#define THRESHOLD    1

#define MACROPHAGE 1
#define BACTERIA 2

// SIZE
#define XMAX  512
#define YMAX  512

#define ANTIBIOTIC_X 141
#define ANTIBIOTIC_Y 280

__FLAME_GPU_INIT_FUNC__ void setConstants(){
     int size = 512;
}
/**************************************
    UTIL FUNCTIONS
**************************************/
__FLAME_GPU_FUNC__ float dist(int x, int y, int x1, int y1){
    return sqrtf((x - x1)*(x - x1) + (y - y1)*(y - y1));
}

__FLAME_GPU_FUNC__ int dotprod(int x, int y, int x1, int y1, int ox, int oy){
    return (x - ox)*(x1 - ox) + (y - oy)*(y1 - oy);
}

////////////////////////////////////////////////////////////////////////////


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
}
////////////////////////////////////////////////////////////////////////////
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
}
/**************************************
     Tissue cell functions
**************************************/


__FLAME_GPU_FUNC__ int TissueCell_input_bacteria(xmachine_memory_TissueCell* agent, xmachine_message_bacteriaInfo_list* bacteria_messages, xmachine_message_bacteriaInfo_PBM *pbm){

    xmachine_message_bacteriaInfo* current = get_first_bacteriaInfo_message(bacteria_messages, pbm, (float)agent->x, (float)agent->y, 0.0);

	int status = 0;
    agent->timecount++;
    float value;
	while (current)
	{

       status = 1;
	   value = current->value;
       current = get_next_bacteriaInfo_message(current, bacteria_messages, pbm);
	}

	if (status ==1 ) {

		agent->citokine_x = agent->x;
		agent->citokine_y = agent->y;
	    agent->state = TS_SIGNALING;
		agent->citokine_value = value;
	}
    if (status ==0)  agent->state = TS_NORMAL;

	return 0;
}
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int TissueCell_output_antibiotic(xmachine_memory_TissueCell* agent, xmachine_message_antibiotic_list* antibiotic_messages){ 
	if ( agent->timecount % 50 ==0 && agent->antibiotic_x == ANTIBIOTIC_X && agent->antibiotic_y == ANTIBIOTIC_Y ) {
	   //agent->state = TS_SIGNALING; 
	   agent->antibiotic_x = ANTIBIOTIC_X; 
	   agent->antibiotic_y = ANTIBIOTIC_Y; 
	   agent->antibiotic_value = 10; 
	   agent->antibiotic_time = agent->timecount; 
	}

	if (agent->antibiotic_value > 0.0) {
		add_antibiotic_message<DISCRETE_2D>(antibiotic_messages, agent->x, agent->y, agent->antibiotic_x, agent->antibiotic_y, agent->antibiotic_value, agent->antibiotic_time);
	} else {
        agent->state = TS_NORMAL;
		add_antibiotic_message<DISCRETE_2D>(antibiotic_messages, agent->x, agent->y, -1, -1, 0.0, 0);
	}
    return 0;
}
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int TissueCell_input_antibiotic(xmachine_memory_TissueCell* agent, xmachine_message_antibiotic_list* antibiotics){
	agent->antibiotic_x = -1;
	agent->antibiotic_y = -1;
	agent->antibiotic_value = -1.0;
	agent->antibiotic_time = -1;

	xmachine_message_antibiotic* current = get_first_antibiotic_message<DISCRETE_2D>(antibiotics, agent->x, agent->y);

    while (current)
    {
		if (newMsg(agent, current->x,current->y,current->antibiotic_x,current->antibiotic_y)==1) {
				agent->antibiotic_x = current->antibiotic_x;
				agent->antibiotic_y = current->antibiotic_y;
				agent->antibiotic_value = current->antibiotic_value;
				agent->antibiotic_time = current->antibiotic_time;
				//agent->state = TS_SIGNALING;
		}
        current = get_next_antibiotic_message<DISCRETE_2D>(current, antibiotics);
    }
    return 0;
}

__FLAME_GPU_FUNC__ int TissueCell_output_citokine(xmachine_memory_TissueCell* agent, xmachine_message_citokine_list* citokine_messages){ 

	if (agent->citokine_value > 0.0) {
		add_citokine_message<DISCRETE_2D>(citokine_messages, agent->x, agent->y, agent->citokine_x, agent->citokine_y, agent->citokine_value, agent->citokine_time);
	} else {
        agent->state = TS_NORMAL;
		add_citokine_message<DISCRETE_2D>(citokine_messages, agent->x, agent->y, -1, -1, 0.0, 0);
	}
    return 0;
}
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int TissueCell_input_citokine(xmachine_memory_TissueCell* agent, xmachine_message_citokine_list* citokines){
	agent->citokine_x = -1;
	agent->citokine_y = -1;
	agent->citokine_value = -1.0;
	agent->citokine_time = -1;

	xmachine_message_citokine* current = get_first_citokine_message<DISCRETE_2D>(citokines, agent->x, agent->y);

    while (current)
    {
		if (newMsg(agent, current->x,current->y,current->citokine_x,current->citokine_y)==1) {
				agent->citokine_x = current->citokine_x;
				agent->citokine_y = current->citokine_y;
				agent->citokine_value = current->citokine_value;
				agent->citokine_time = current->citokine_time;
				//agent->state = TS_SIGNALING;
		}
        current = get_next_citokine_message<DISCRETE_2D>(current, citokines);
    }
    return 0;
}
/**************************************
     bacteria functions
**************************************/
__FLAME_GPU_FUNC__ int bacteria_processing(xmachine_memory_bacteria* agent, RNG_rand48* rand48){
    agent->lifetime++;
    agent->dividingTime=0;
    if (agent->lifetime  % 10 == 0) agent->dividingTime=1;
    return 0;
} 
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int bacteria_move(xmachine_memory_bacteria* agent, RNG_rand48* rand48){
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
}
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int bacteria_divide(xmachine_memory_bacteria* agent, xmachine_memory_bacteria_list*  bacteria_agents, RNG_rand48* rand48){
	int dt = agent->dividingTime;
    float divideProb = 0.9f; 
    if (agent->antibiotic_value >0.0) divideProb = 0.9;

    if (dt == 1) {
		if (rnd(rand48)<divideProb) {
            int lifetime = (int)(rnd(rand48)*10.0f);
			add_bacteria_agent(
				bacteria_agents
                ,agent->x 
                ,agent->y 
                ,agent->z 
                ,agent->agent_id 
                ,agent->type 
                ,agent->pattern 
                ,agent->state 
                ,agent->nearagents 
                ,agent->value 
                ,lifetime 
                ,agent->nAntibodyAttached 
                ,agent->deathSignal 
                ,agent->antibiotic 
                ,agent->infecting 
                ,agent->timeInfecting 
                ,agent->dividingTime 
                ,agent->antibiotic_x 
                ,agent->antibiotic_y 
                ,agent->antibiotic_value 
                ,agent->macrophage_x 
                ,agent->macrophage_y 
                ,agent->macrophage_value 
				);
		}
	}
    return 0;
} 
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_infect(xmachine_memory_bacteria* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_die(xmachine_memory_bacteria* agent){
    agent->state= DEAD;
    return 1;
} 
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_output(xmachine_memory_bacteria* agent, xmachine_message_bacteriaInfo_list* bacteriaInfo_messages){

    add_bacteriaInfo_message(bacteriaInfo_messages, agent->x, agent->y, 0.0,agent->type, agent->pattern,agent->value);
    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_input_antibiotic(xmachine_memory_bacteria* agent, xmachine_message_antibiotic_list* antibiotic_messages){
    xmachine_message_antibiotic* current = get_first_antibiotic_message<CONTINUOUS>(antibiotic_messages, (float)agent->x, (float)agent->y);

    agent->antibiotic_value = 0.0;
    while (current)
    {
             agent->antibiotic_value=current->antibiotic_value;
       current = get_next_antibiotic_message<CONTINUOUS>(current, antibiotic_messages);

    }
    if (MACROPHAGE & agent->nearagents) agent->deathSignal=1;
    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_input_macrophage(xmachine_memory_bacteria* agent, xmachine_message_macrophageInfo_list* macrophageInfo_messages,xmachine_message_macrophageInfo_PBM* pm){
    xmachine_message_macrophageInfo* current = get_first_macrophageInfo_message(macrophageInfo_messages,pm, (float)agent->x, (float)agent->y,0.0);

    agent->nearagents = 0;
    while (current)
    {
       if (receptorMatch(agent->pattern, current->ivalue) >= THRESHOLD)   agent->nearagents |= current->type;
       current = get_next_macrophageInfo_message(current, macrophageInfo_messages,pm);

    }
    if (MACROPHAGE & agent->nearagents) agent->deathSignal=1;
    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_MovingToEmiting(xmachine_memory_bacteria* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_EmitingToSensing(xmachine_memory_bacteria* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_SensingToActing(xmachine_memory_bacteria* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int bacteria_ActingToMoving(xmachine_memory_bacteria* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

/**************************************
     macrophage functions
**************************************/
__FLAME_GPU_FUNC__ int macrophage_processing(xmachine_memory_macrophage* agent, RNG_rand48* rand48){
    return 0;
} 
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int macrophage_move(xmachine_memory_macrophage* agent, RNG_rand48* rand48){
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
}
////////////////////////////////////////////////////////////////////////////


__FLAME_GPU_FUNC__ int macrophage_directedMove(xmachine_memory_macrophage* agent, RNG_rand48* rand48){

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

	if (agent->infectionSite_target_x != -1 && agent->infectionSite_target_y != -1) {
		float dist1 = dist(agent->infectionSite_target_x,agent->infectionSite_target_y,agent->x,agent->y);
		if (dist1 > 5.0f) {
			float dist2 = dist(agent->infectionSite_target_x,agent->infectionSite_target_y,x1,y1);
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
    
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_output(xmachine_memory_macrophage* agent, xmachine_message_macrophageInfo_list* macrophageInfo_messages){

    add_macrophageInfo_message(macrophageInfo_messages, agent->x, agent->y, 0.0,agent->type, agent->pattern,agent->value);
    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_input_citokine(xmachine_memory_macrophage* agent, xmachine_message_citokine_list* citokine_messages){
    xmachine_message_citokine* current = get_first_citokine_message<CONTINUOUS>(citokine_messages, (float)agent->x, (float)agent->y);

    agent->citokine_value = 0.0;
    while (current)
    {
       if (current->citokine_x != -1){
              agent->infectionSite_target_x = current->citokine_x;
              agent->infectionSite_target_y = current->citokine_y;
             agent->citokine_value=current->citokine_value;
       }
       current = get_next_citokine_message<CONTINUOUS>(current, citokine_messages);

    }
    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_MovingToEmiting(xmachine_memory_macrophage* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_EmitingToSensing(xmachine_memory_macrophage* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_SensingToActing(xmachine_memory_macrophage* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

__FLAME_GPU_FUNC__ int macrophage_ActingToMoving(xmachine_memory_macrophage* agent){

    return 0;
}
////////////////////////////////////////////////////////////////////////////

#endif // #ifndef _FUNCTIONS_H_
