import json
config_dict = {
}

summary_dict = {
}

def update_config(key, value):
    config_dict[key] = value
    with open('config.txt', 'w') as file:
        file.write(str(config_dict))

def reset_config():
    config_dict=[]
    with open('config.txt', 'w') as file:
        file.write(str(config_dict))
        
def update_summary(key, value):
    summary_dict[key] = value
    with open('summary.txt', 'w') as file:
        json.dump(summary_dict, file)
        
def reset_summary():
    summary_dict=[]
    with open('summary.txt', 'w') as file:
        json.dump(summary_dict, file)

def load_summary():
     with open('summary.txt', 'r') as file:
        data = json.load(file)
     summary_dict.update(data)
