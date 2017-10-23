import requests
import json

# settings

domain = 'http://mike.ceriumplatforms.com'
login_endpoint = '/taboo-api/user/login.json'
logout_endpoint = '/taboo-api/user/logout.json'

# log in

head = {'Content-Type':'application/json'}

login_data = {'username':'','password':''}

with open('password.json', 'r') as f:
  login_data = json.load(f)

ld=json.dumps(login_data)

l = requests.post(domain + login_endpoint, headers=head, data=ld)

user_data = json.loads(l.text)

head['Cookie'] = user_data['session_name'] + '=' + user_data['sessid']
head['X-CSRF-Token'] = user_data['token']

# create nodes

#~ new_node = {}
#~ new_node['type'] = 'quotemine_qa_entry'
#~ new_node['title'] = 'http://test-url/test2'
#~ new_node['field_redirect_url'] = {'und':[{'value':'http://test-url/test-test'}]}
#~ new_node['field_status'] = {'und':[{'value':'200'}]}
#~ new_node['field_duration'] = {'und':[{'value':'0.3456'}]}
#~ new_node['field_url_source'] = {'und':[{'value':'http://test-url'},{'value':'http://test-url/test'}]}


#~ node_data = json.dumps(new_node)

#~ req = requests.post('http://quotemine-dev/quotemine/node', headers=head, data=node_data)

#~ print(req.status_code)
#~ print(req.text)

# log out
x = requests.post(domain + logout_endpoint, headers=head)
