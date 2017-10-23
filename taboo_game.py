import requests
import json
import random
import sys
import time

def pprint(text):
  sys.stdout.write(str(text) + '\n')
  sys.stdout.flush()

class TabooGame():
  ######################################################################
  # Settings
  domain = 'http://45.55.76.168'
  login_endpoint = '/taboo-api/user/login.json'
  logout_endpoint = '/taboo-api/user/logout.json'
  node_endpoint = '/taboo-api/entity_node.json'

  pwfile = 'password.json'

  ######################################################################
  # Data
  
  # Server connection data
  head = {'Content-Type':'application/json'}
  login_data = {'username':'','password':''}

  ## Game data settings
  # Minimum plays for a card before difficulty is factored in
  min_plays_for_difficulty = 5

  # Minimum/Maximum difficulty ~ may be between 0 and 1
  min_difficulty = 0.1
  max_difficulty = 1
  
  # Difficulty limits
  # min may not go above limit. max may not go below limit
  min_difficulty_limit = 0.4
  max_difficulty_limit = 0.6

  # Cards
  cards = []

  ######################################################################
  # Helper Functions

  # Log in
  def login(self, pw_file = pwfile, endpoint = domain + login_endpoint):
    with open(pw_file, 'r') as f:
      self.login_data = json.load(f)

    ld=json.dumps(self.login_data)

    l = requests.post(endpoint, headers=self.head, data=ld)

    user_data = json.loads(l.text)

    self.head['Cookie'] = user_data['session_name'] + '=' + user_data['sessid']
    self.head['X-CSRF-Token'] = user_data['token']

  # Log out
  def logout(self, endpoint = domain + logout_endpoint):
    x = requests.post(endpoint, headers=self.head)
  
  ######################################################################
  # Game functions
  def get_cards(self):
    # Retrieve cards from endpoint
    c = requests.get(self.domain + self.node_endpoint + '?parameters[type]=taboo_card&fields=title,nid,field_words_to_avoid', headers = self.head)
    cards = json.loads(c.text)
    # Process cards into local card data
    for card in cards:
      ret_card = {'title':card['title'],'id':card['nid'], 'words_to_avoid':[]}
      for word in card['field_words_to_avoid']['und']:
        ret_card['words_to_avoid'].append(word['value'])
      score_data = self.calculate_difficulty(ret_card)
      ret_card['difficulty'] = score_data['score'] 
      ret_card['total_of_plays'] = score_data['total']
      self.cards.append(ret_card)

  def calculate_difficulty(self, card):
    s = requests.get(self.domain + '/taboo-api/entity_node/' + card['id'] + '/nodes_field_taboo_card?fields=field_score_type,field_score_time', headers = self.head)
    scores = json.loads(s.text)
    score_count = {'correct':0, 'pass': 0, 'taboo': 0}
    try:
      for score in scores:
        t = score['field_score_type']['und'][0]['value']
        score_count[t] += 1
#      print(score_count)
      score_total = score_count['correct'] + score_count['pass'] + score_count['taboo']
      return {'score':1 - (score_count['correct'] / score_total),'total':score_total}
      # if score_total > self.min_plays_for_difficulty:
#         return 1 - (score_count['correct'] / score_total)
#       else:
#         return 0
    except:
      return {'score':0,'total':0}

  def select_card(self):
    ret_card = {}
    reject_count = 0
    while not ret_card:
      if self.cards:
        random.shuffle(self.cards)
        c = self.cards.pop()
        # If we have too many rejects, expand the search range
        if reject_count > 10:
          if self.min_difficulty > 0.1:
            self.min_difficulty -= 0.1
          else:
            self.min_difficulty = 0
          if self.max_difficulty < 0.9:
            self.max_difficulty += 0.1
          else:
            self.max_difficulty = 1
       
        
        # Test difficulty
        if c['total_of_plays'] < self.min_plays_for_difficulty:
          ret_card = c
        elif c["difficulty"] >= self.min_difficulty and c["difficulty"] <= self.max_difficulty:
          ret_card = c
        else:
          reject_count += 1
          
      else:
        self.get_cards()
    
    return ret_card
    
    
  def record_score(self, typ, card, tim):
    # Adjust difficulty based on player response
    inc = 0.05
    if typ == 'correct':
      if self.max_difficulty + inc <= 1:
        self.max_difficulty += inc
      else:
        self.max_difficulty = 1 
      if self.min_difficulty + inc <= self.min_difficulty_limit:
        self.min_difficulty += inc
      else:
        self.min_difficulty = self.min_diffculty_limit
    else:
      if self.max_difficulty - inc >= self.max_difficulty_limit:
        self.max_difficulty -= inc
      else:
        self.max_difficulty = self.max_difficulty_limit
      if self.min_difficulty - inc >= 0:
        self.min_difficulty -= inc
      else:
        self.min_difficulty = 0
    # Push score to server
    push_data = {}
    push_data['type'] = 'score'
    push_data['field_taboo_card'] = {'und':[{'target_id':card['id']}]}
    push_data['field_score_time'] = {'und':[{'value':tim}]}
    push_data['field_score_type'] = {'und':[{'value':typ}]}
    push_data['title'] = 'Score for '+ card['title'] + ' on ' + time.strftime('%Y-%m-%d_%H:%M:%S')
    pd = json.dumps(push_data)
    try:
      s = requests.post(self.domain + self.node_endpoint, headers = self.head, data = pd)
    except:
      pass
    
######################################################################
  # Play the game
  
  def play(self):
    pprint("Welcome to Taboo")
    playing = True
    while playing:
      for i in range(0,5):
        pprint("You next card is...")
        c = self.select_card()
        t_start = time.time()
        pprint('Card: ' + c['title'])
        pprint('Words to avoid: '+ str(c['words_to_avoid']))
        score = 0
        while score not in ['1','2','3']:
          score = input('Type 1 for correct, 2 for incorrect/pass, 3 for Taboo: ')
          t_end = time.time()
          t = str(t_end - t_start)
          if score == '1':
            self.record_score('correct', c, t)
          elif score == '2':
            self.record_score('pass', c, t)
          elif score == '3':
            self.record_score('Taboo', c, t)
          else: 
            pprint('Sorry, we couldnot recognize that entry')
      go = 0
      while go not in ['y','n']:
        go = input("Keep playing? y/n: ")
        if go == 'y':
          playing = True
        elif go == 'n':
          playing = False
        else:
          pprint("Sorry, we couldn't recognize that entry")
          