# Hack script

update_role_init_part:
- all main.sh/main.py contains boilerplate code (init)
- this script will update all files with single code
  
~~~
cd hacks/update_role_init_part
#update commons.sh and commons.py

python ./update_common.py  # for main.sh
python ./update_common.py py  # for main.py
~~~

update_test_custom_context_json:
- pytest need configuration and this file will update the json file.
~~~
cd hacks
python ./update_test_custom_context_json.py
~~~
