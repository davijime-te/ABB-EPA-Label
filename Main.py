import csv
import os
import json
from connector import *
from colorama import Fore, Style, Back


def banner():
    with open('banner.txt', 'r') as file:
        banner = file.read()
    print(banner)

def read_files(directory_path:str):
     
     #dict that corelates the label name with the agents that has to be assigned
    label_to_agents = {}

    for filename in os.listdir(directory_path):
        print(f'Reading: {filename}')
        label = filename.split(".")[0]

        if filename.endswith('.csv'):
            file_path = os.path.join(directory_path, filename)

            with open(file_path, newline="") as csvfile:
                reader = csv.reader(csvfile)

                for row in reader:
                    if label in label_to_agents:
                        label_to_agents[label].append(row[0])
                    else:
                        label_to_agents[label] = [row[0]]

    return label_to_agents

def agents_to_dict(all_agents:dict):

    agents_name_id = {}

    if "endpointAgents" in all_agents:

        for agent in all_agents["endpointAgents"]:
            #si el agente está en esa lista entonces sacamos su ID
            agents_name_id[agent["agentName"]] = agent["agentId"]

    return agents_name_id

def labels_to_dict(all_labels:dict):
    
    labels_name_id = {}

    if "groups" in all_labels:
        for label in all_labels["groups"]:
            labels_name_id[label["name"]] = label["groupId"]

    return labels_name_id

def add_agents(headers:dict, labels_to_agents:dict ,account_group:str="ProServ Enablement"):

    
    agent = {}

    #We get the aid for the target Account group
    acc_endp = "https://api.thousandeyes.com/v6/account-groups.json"
    _,accounts = get_data(headers=headers, endp_url=acc_endp, params={})

    
    for acc in accounts["accountGroups"]:
        if acc["accountGroupName"] == account_group:
            aid = acc["aid"]
    

    #Obtenemos todos los agentes de ese account group para sacar su agentId
    agents_url = "https://api.thousandeyes.com/v6/endpoint-agents.json"
    _, all_agents = get_data(headers, agents_url, params={"aid": aid})

    #Con esto tenemos que hacer un diccionario de {Agent_name:agent_id }
    agents_name_id = agents_to_dict(all_agents)

    #hacemos lo mismo para los labels
    #ya que tenemos los agent IDs buscamos la info del label
    label_url = "https://api.thousandeyes.com/v6/groups/endpoint-agents.json"
    _,all_labels = get_data(headers, label_url, params={"aid": aid})

    labels_name_id = labels_to_dict(all_labels)

    #iterar en el diccionario de labels_to_agents y armar una lista de agent ids por cada agente
    for label, agents in labels_to_agents.items():
        
        agentsIds = []

        for agent in agents:

            if agent in agents_name_id:
                agentsIds.append({"agentId" :agents_name_id[agent]})
            else:
                print(f'This agent does not exists')
        

        #Ahora si agregamos los agentes a ese label
        payload = json.dumps({
            "name": label,
            "endpointAgents": agentsIds
            })
        
        update_label_url = "https://api.thousandeyes.com/v6/groups/%s/update.json?aid=%s" % (labels_name_id[label], aid)
        status_code,update = post_data(headers,update_label_url,payload)
    
        if status_code != 200:
            print("There was an issue with the agents please verify the list")
        else: 
            print("All agents added successfully")


    return 0

    


#############################
#           MAIN
#############################

if __name__ == "__main__":

    try:
        
        banner()

        OAuth = input(f"Please provide your ThousandEyes API {Back.RED}{Style.BRIGHT}OAUTH token{Style.RESET_ALL}: ")

        directory_path = f'./CSV'


        HEADERS = {'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + OAuth}
        

        #1. Label to agents relation:
        labels_to_agents = read_files(directory_path=directory_path)

        #2. Assign labels to agents:
        add_agents(headers=HEADERS, labels_to_agents=labels_to_agents)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")





