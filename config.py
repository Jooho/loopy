
config_dict = {
}

def update_config(key, value):
    config_dict[key] = value
    with open('config.txt', 'w') as file:
        file.write(str(config_dict))
