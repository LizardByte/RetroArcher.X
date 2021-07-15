#!/usr/bin/env python
import os
import sys
import tweepy

from dotenv import load_dotenv


def changelog():
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

    return title, version, selftext, embedUrl


def main():
    twitter_auth_keys = {
        "consumer_key": os.environ['TWITTER_API_KEY'],
        "consumer_secret": os.environ['TWITTER_API_SECRET'],
        "access_token": os.environ['TWITTER_ACCESS_TOKEN'],
        "access_token_secret": os.environ['TWITTER_ACCESS_TOKEN_SECRET']
    }

    auth = tweepy.OAuthHandler(
        twitter_auth_keys['consumer_key'],
        twitter_auth_keys['consumer_secret']
    )

    auth.set_access_token(
        twitter_auth_keys['access_token'],
        twitter_auth_keys['access_token_secret']
    )

    api = tweepy.API(auth)
    title, version, selftext, embedUrl = changelog()

    if embedUrl == 'https://github.com/RetroArcher':
        sys.exit()

    tweet = embedUrl

    status = api.update_status(status=tweet)
    print(status)


if __name__ == "__main__":
    load_dotenv()
    main()
