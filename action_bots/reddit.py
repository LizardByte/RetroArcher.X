#!/usr/bin/env python
import os
import praw

from dotenv import load_dotenv

load_dotenv()

# load the changelog
with open('changelog.md', 'r') as f:
    lines = f.readlines()

found_version = False
title = ''
selftext = ''

# parse the changelog
for line in lines:
    if line.startswith('##'):
        if not found_version:
            title = 'Released %s' % (line.replace('##', '').strip())
            version = line.replace('##', '').strip().split(' ', 1)[0]
            selftext = '**Changelog:**'
            found_version = True
        else:
            break
    else:
        if found_version:
            if line.startswith('*'):  # this is a category, let's underline it
                selftext += '\n__%s__' % (line[1:].strip())
            else:
                selftext += '\n%s' % (line.strip())

# add the download link
if title != '':
    try:
        embedUrl = 'https://github.com/%s/releases/%s' % (os.environ['GITHUB_REPOSITORY'], version)
        selftext += '\n[Download](%s)' % (embedUrl)
    except KeyError:
        embedUrl = 'https://github.com/RetroArcher'

try:
    agent = os.environ['RUNNER_OS']
except KeyError:
    agent = 'linux'

# reddit
reddit = praw.Reddit(
    user_agent='%s:RetroArcher_releases:%s by u/RetroArcherX' % (agent, version),
    client_id=os.environ['REDDIT_CLIENT_ID'],
    client_secret=os.environ['REDDIT_CLIENT_SECRET'],
    username=os.environ['REDDIT_USERNAME'],
    password=os.environ['REDDIT_PASSWORD'],
)

reddit.validate_on_submit = True
subreddit = reddit.subreddit(os.environ['REDDIT_SUBREDDIT'])

# make post
if title != '':
    subreddit.submit(title, selftext=selftext)
