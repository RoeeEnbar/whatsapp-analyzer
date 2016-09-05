#!/usr/bin/env python

from google.appengine.ext import vendor
try:
	vendor.add('env/lib/python2.7/site-packages/')
except ValueError:
	# windows OS
	vendor.add('env/Lib/site-packages/')

import os
import urllib

#from google.appengine.api import users
#from google.appengine.ext import ndb

import jinja2
import webapp2
import logging

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

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
        template = JINJA_ENVIRONMENT.get_template('analysis.html')
        template_values = {
            'emojis_by_name': chat.normalized_emoji_counts()
                }
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/analyze', Analyzer),
    ('/analyze_uploaded_file', Analyzer),
], debug=True)

import emoji
import re
#import codecs
from collections import Counter, defaultdict
#from textblob import TextBlob
#import pandas as pd
import dateutil
#import matplotlib.pyplot as plt
import datetime
#import wikiwords
#plt.style.use('seaborn-darkgrid')
#


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

    def _extract_chat_by_name(self, txt):
        names = set(re.findall('(?:^|\n)[\d/, :]+? - (.*?):', txt))
        return {name: OneSidedChat('\n'.join(re.findall(name + r': (.+)\n', txt))) for name in names}

    def normalized_emoji_counts(self):
        emoji_highest_frequency = max([one_sided_chat.emoji_highest_frequency() for one_sided_chat in self._chats_by_name.itervalues()])
        return {name: one_sided_chat.normalized_emoji_counter(emoji_highest_frequency) for name, one_sided_chat in self._chats_by_name.iteritems()}


def words(txt, name):
    blob = TextBlob(txt)
    n_words = sum(blob.word_counts.values())
    n_msgs = len(blob.sentences)
    print 'total {} words'.format(n_words)
    print 'total {} messages'.format(n_msgs)
    print 'average {:.1f} words / message'.format(1.0 * n_words / n_msgs)
    print

    if False:
        print 'most used words:'
        weighted_words = []
        for word, count in blob.word_counts.iteritems():
            word = re.sub(u'[\U0001f004-\U0001f9c0|\u203c-\u3299]', '', word)
            if not re.match(r'[a-zA-Z]', word):
                # no letters
                continue
            if count == 1:
                continue
            try:
    #             w = max(1, log(wikiwords.occ(word)))
                w = wikiwords.occ(word)
            except NameError:
                # word not in wikiwords
                continue
            weighted_words.append((word, 1.0 * count / w, count))
        weighted_words = sorted(weighted_words, key=lambda x:x[1], reverse=True)
        print '\n'.join(['{:20}{}'.format(x[0], x[2]) for x in weighted_words[:200]])
        print
    if False:
        msg_len, count = zip(*Counter([len(sentence.words) for sentence in blob.sentences]).items())
        count = array(count)
        _ = plot(msg_len, 100.0 * count / sum(count), label=name)
        legend()
        title('message length distribution')
        ylabel('% of messages')
        xlabel('num words in message')
    
def reverse_hebrew_name(name):
    try:
        name.decode('ascii')
        return name
    except UnicodeEncodeError:
        return name[::-1]    

def reverse_hebrew_names(names):
    return map(reverse_hebrew_name, names)
    
def dist_msgs_in_a_row(raw_txt):
    c = defaultdict(Counter)
    names = re.findall('(?:^|\n)[\d/, :]+? - (.*?):', raw_txt)
    names = reverse_hebrew_names(names)
            
    last_name = names[0]
    i = 1
    for name in names[1:]:
        if name == last_name:
            i += 1
        else:
            c[last_name][i] += 1
            i = 1
            last_name = name
    c[last_name][i] += 1
    
    figure()
    df = pd.DataFrame(c)
    df = df.div(df.sum(axis=0)) * 100
    df.loc['4+'] = df.loc[4:].sum()
    df.loc[[1,2,3,'4+']].plot(kind='bar', rot=0)
    legend()
    xlabel('Number of messages in a row')
    ylabel('% of messages')  
    
def who_starts_the_conversation(raw_txt):
    MIN_GAP = datetime.timedelta(hours=8)
    c = Counter()
    times_names = re.findall('(?:^|\n)([\d/, :]+?) - (.*?):', raw_txt)
    times_names = [(dateutil.parser.parse(t), reverse_hebrew_name(n)) for t, n in times_names]
    last_time, last_name = times_names[0]
    for cur_time, name in times_names[1:]:
        if cur_time - last_time > MIN_GAP:
            # a new conversation was started by "name"
            c[name] += 1
        last_time = cur_time
    figure()
    s = pd.Series(c)
    s.plot(kind='bar', rot=0)
    title('how many times started the conversation')
    
def time_to_respond(raw_txt):
    MAX_GAP = datetime.timedelta(hours=4)
    c = defaultdict(list)
    times_names = re.findall('(?:^|\n)([\d/, :]+?) - (.*?):', raw_txt)
    times_names = [(dateutil.parser.parse(t), reverse_hebrew_name(n)) for t, n in times_names]
    n_names = len(set([x[1] for x in times_names]))
    if n_names != 2:
        print "time_to_respond only supported for a dialogue (found {} participants)".format(n_names)
        return
    
    last_time, last_name = times_names[0]
    for cur_time, name in times_names[1:]:
        if name != last_name and cur_time >= last_time and cur_time - last_time < MAX_GAP:
            # "name" has responded to "last_name"
            c[name].append((cur_time - last_time).total_seconds() / 60)
        last_time = cur_time
        last_name = name
    x = {k: pd.Series(v) for k, v in c.iteritems()}
    for k, v in x.iteritems():
        print k
        print v.describe()
        print
    x = pd.DataFrame({k: [sum((a <= v) & (v < b)) for a, b in [(0, 1), (1, 5), (5, 60), (60, 1000)]] for k, v in x.iteritems()},
                    index=['less than 1 min', '1 min - 5 min', '5 min - 1 hour', 'more than one hour'])
    x = x.div(x.sum()) * 100
    x.plot(kind='bar', rot=45)
    ylabel('% of replies')
    title('Time to respond')
    
def split_to_conversations(raw_txt):
    MIN_GAP = datetime.timedelta(hours=8)
    last_time = datetime.datetime(1900,1,1)
    conv_lines = []
    conversations = []
    for line in raw_txt.split('\n'):
        m = re.match(r'^([\d/, :]+?) - ', line)
        if not m:
            continue
        cur_time = dateutil.parser.parse(m.group(1))
        if cur_time - last_time > MIN_GAP and conv_lines:
            # new conversation started
            conversations.append('\n'.join(conv_lines))
            conv_lines = []
        last_time = cur_time
        conv_lines.append(line)
    return conversations

def draw_convs_by_messages_num(conversations):
    to_flip = sorted(re.findall('(?:^|\n)[\d/, :]+? - (.*?):', conversations[0]))[0]
    d = []
    for conv in conversations:
        names = re.findall('(?:^|\n)[\d/, :]+? - (.*?):', conv)
        total_msgs = len(names)
#         d.append({k: 100.0 * v / total_msgs for k, v in Counter(names).iteritems()})
#         d.append(dict(Counter(names)))
        d.append({k: v * -1 if k == to_flip else v for k, v in Counter(names).iteritems()})
    d = pd.DataFrame(d)
    ax = d.plot(kind='barh', stacked=True, grid=False, yticks=[], figsize=(5,20))
    for container in ax.containers:
        plt.setp(container, height=1)
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 -0.5, y1 + 0.25)
    ax.get_yaxis().set_visible(False)
    
#     ax = d.plot(kind='bar', stacked=True, grid=False, yticks=[], xticks=[], figsize=(15,5), position=1)
#     for container in ax.containers:
#         plt.setp(container, width=1)
#     x0, x1 = ax.get_xlim()
#     ax.set_xlim(x0 -0.5, x1 + 0.25)
#     ax.get_xaxis().set_visible(False)
    
    plt.tight_layout() 
    title('conversations by number of messages')
    
def draw_convs_by_message_ratio(conversations):
    to_flip = sorted(re.findall('(?:^|\n)[\d/, :]+? - (.*?):', conversations[0]))[0]
    d = []
    for conv in conversations:
        names = re.findall('(?:^|\n)[\d/, :]+? - (.*?):', conv)
        total_msgs = len(names)
        d.append({k: 100.0 * v / total_msgs for k, v in Counter(names).iteritems()})
    d = pd.DataFrame(d)
    ax = d.plot(kind='barh', stacked=True, grid=False, yticks=[], xticks=[], figsize=(5,20))
    for container in ax.containers:
        plt.setp(container, height=1)
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 -0.5, y1 + 0.25)
    ax.get_yaxis().set_visible(False)
    plt.tight_layout() 
    title('conversations by ratio of messages')    

