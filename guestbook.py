#!/usr/bin/env python

#TODO:
#Emoji tool tip with emoji names, and remove "series 1"
#time to respond
#conversation flow
#unique words
#distribution of number of words in messages
#summary: word count, message count, emoji count
#summary: average length of conversation



from google.appengine.ext import vendor
try:
	vendor.add('env/lib/python2.7/site-packages/')
except ValueError:
	# windows OS
	vendor.add('env/Lib/site-packages/')

#from google.appengine.api import users
#from google.appengine.ext import ndb
import os
import urllib
import jinja2
import webapp2
import logging
import json
import emoji
import re
from collections import Counter, defaultdict
import dateutil.parser
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
JINJA_ENVIRONMENT.globals['json'] = json

class MainPage(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render())


class Analyzer(webapp2.RequestHandler):
    def post(self):
        try:
            content = self.request.POST['upload_file'].file.read().decode('utf8')
        except:
            content = self.request.get('content')

        chat = Chat(content)
        conversation_starters, conversation_enders = chat.who_starts_and_ends_the_conversation()
        template = JINJA_ENVIRONMENT.get_template('analysis.html')
        template_values = {
            'emojis_by_name': json.dumps(chat.normalized_emoji_counts()),
            'conversation_starters': json.dumps(conversation_starters),
            'conversation_enders': json.dumps(conversation_enders)
        }
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/analyze', Analyzer),
    ('/analyze_uploaded_file', Analyzer),
], debug=True)



class OneSidedChat:
    def __init__(self, one_sided_text):
        self._txt = one_sided_text
        self._emoji_counter = self._find_all_emoticons()
    
    def _find_all_emoticons(self):
        emoji_unicode = re.compile(u'('
                            u'\ud83c[\udf00-\udfff]|'
                            u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
                            u'[\u2600-\u26FF\u2700-\u27BF]|'
                            u'[\u203c-\u3299])', 
                            re.UNICODE)
        return Counter(emoji_unicode.findall(self._txt))

    def normalized_emoji_counter(self, normalize_by):
        return [(emoji, count, 100.0 * count / normalize_by) for emoji, count in self._emoji_counter.most_common()]

    def emoji_highest_frequency(self):
        emoji_name, count = self._emoji_counter.most_common(1)[0]
        return count

class Chat:
    def __init__(self, whole_conversation):
        self._whole_txt = whole_conversation
        self._chats_by_name = self._extract_chat_by_name(whole_conversation)
    
    @property
    def _names(self):
        return sorted(self._chats_by_name.keys())

    def _extract_chat_by_name(self, txt):
        names = set(re.findall('(?:^|\n)[\d/, :]+? - (.*?):', txt))
        return {name: OneSidedChat('\n'.join(re.findall(name + r': (.+)\n', txt))) for name in names}

    def normalized_emoji_counts(self):
        emoji_highest_frequency = max([one_sided_chat.emoji_highest_frequency() for one_sided_chat in self._chats_by_name.itervalues()])
        return [(name, self._chats_by_name[name].normalized_emoji_counter(emoji_highest_frequency)) for name in self._names]

    def _new_conversation_started(self, now, before):
        MIN_GAP = datetime.timedelta(hours=8)
        return now - before > MIN_GAP

    def who_starts_and_ends_the_conversation(self):
        starts = Counter()
        ends = Counter()
        times_names = re.findall('(?:^|\n)([\d/, :]+?) - (.*?):', self._whole_txt)
        times_names = [(dateutil.parser.parse(t), n) for t, n in times_names]
        last_time, last_name = times_names[0]
        starts[last_name] += 1
        for cur_time, cur_name in times_names[1:]:
            if self._new_conversation_started(cur_time, last_time):
                starts[cur_name] += 1
                ends[last_name] += 1
            last_time = cur_time
            last_name = cur_name
        ends[last_name] += 1
        return [[{'name': name, 'y': counter[name]} for name in sorted(counter.iterkeys())] for counter in [starts, ends]]
