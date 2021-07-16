#!/usr/bin/env python
import os
import facebook

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
                if line.startswith('*'):  # this is a category
                    selftext += '\n%s' % (line[1:].strip())
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
    page_access_token = os.environ['FACEBOOK_ACCESS_TOKEN']
    graph = facebook.GraphAPI(page_access_token)
    pages_groups_ids = []
    pages_groups_ids.append(os.environ['FACEBOOK_PAGE_ID'])
    pages_groups_ids.append(os.environ['FACEBOOK_GROUP_ID'])

    title, version, selftext, embedUrl = changelog()

    fb_message = '%s\n\n%s' % (title, selftext)

    for fb_ids in pages_groups_ids:
        graph.put_object(fb_ids, "feed", message=fb_message, link=embedUrl)


if __name__ == "__main__":
    load_dotenv()
    main()
