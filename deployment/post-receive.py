#!/usr/bin/env python

import fileinput
import logging
import os
import re
import smtplib
import subprocess
import sys


def create_logger(target_file):
    logger = logging.getLogger(__name__)
    logger.handlers = []
    logger.addHandler(logging.FileHandler(target_file))
    return logger


def find_affected_files(diff_text):
    file_list = []
    for line in diff_text.split('\n'):
        if '--- a/' in line:
            file_list.append(line.split()[1][1:])
    return file_list


def prepend_repo_name(file_list):
    for x in range(0, len(file_list)):
        file_list[x] = str(commit['repo'] + file_list[x])
    return file_list


def find_common_string(a, b):
    if len(a) < len(b):
        limit = len(a)
    else:
        limit = len(b)
    c = ''
    for x in range(0, limit):
        if a[x] == b[x]:
            c = c + a[x]
        else:
            break
    return c


def trim_filename(s):
    for x in reversed(range(0, len(s))):
        if s[x] == '/':
            p = x
            break
    p += 1
    return s[0:p]


def find_common_path(file_list):
    if len(file_list) > 1:
        a = file_list[0]
        b = file_list[1]
        shared_path = find_common_string(a, b)
        if len(file_list) > 2:
            for x in range(2, len(file_list)):
                a = shared_path
                b = file_list[x]
                shared_path = find_common_string(a, b)
    elif len(file_list) == 1:
        shared_path = file_list[0]
    else:
        return ''

    return trim_filename(shared_path)


def transform_url(url, repo, hash):
    url = url.replace('<repo>', repo)
    url = url.replace('<hash>', hash)
    return url


def git(command):
    args = ['git'] + command.split()
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    return str(p.stdout.read().strip())


def get_recipient_address():
    recipients = git('config hooks.mailinglist')
    return recipients


def git_log(format_code, ref_name):
    return git('log -n 1 --format=%s' % format_code + " " + ref_name)


def get_repo_name():
    bare = git('rev-parse --is-bare-repository')
    if bare == 'true':
        name = os.path.basename(os.getcwd())
        if name.endswith('.git'):
            name = name[:-4]
        return name
    else:
        return os.path.basename(os.path.dirname(os.getcwd()))


def send_email(message):
    sender = git('config hooks.envelopesender')
    recipients = get_recipient_address()
    try:
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, recipients, message)
    except:
        log.exception('The send_email() function encountered an error.')
        exit(1)


def create_head_data(commit):
    result = re.match('^0*$', commit['old'])

    if result:
        commit['action'] = 'create'
    else:
        result = re.match('^0*$', commit['new'])
        if result:
            commit['action'] = 'delete'
        else:
            commit['action'] = 'update'

    if commit['action'] == 'create' or commit['action'] == 'update':
        commit['hash'] = commit['new']
        commit['type'] = git("cat-file -t " + commit['new'])

    elif commit['action'] == 'delete':
        commit['hash'] = commit['old']
        commit['type'] = git("cat-file -t " + commit['old'])

    else:
        exit(1)

    commit['branch'] = commit['ref_name'].split('/heads/')[1]
    commit['url'] = transform_url(commit['url'],
                                  commit['repo'],
                                  commit['hash'])

    taglist = git('tag -l')
    commit['tag'] = 'none'
    if taglist:
        commit['tag'] = git('describe ' + commit['hash'] + ' --tags')

    commit['diff'] = ''
    if not result:
        commit['diff'] = git('diff %s..%s' % (commit['old'], commit['new'])) 

    commit['user'] = git_log('%cn', commit['ref_name'])
    commit['email'] = git_log('%ce', commit['ref_name'])
    commit['date'] = git_log('%ad', commit['ref_name'])
    commit['subject'] = git_log('%s', commit['ref_name'])
    commit['body'] = git_log('%b', commit['ref_name'])

    files = git('show --pretty=format: --name-only ' + commit['hash'])
    file_list = files.split('\\n')
    
    files = ''
    for file in file_list:
        file = str(file)
        files += '%s/%s\n' % (commit['repo'], file)
    commit['files'] = files.strip()

    file_list = files.strip().split('\n')
    commit['shared_path'] = find_common_path(file_list)

    if commit['shared_path'] == str(commit['repo'] + '/'):

        try:
            file_list = find_affected_files(commit['diff'])
            file_list = prepend_repo_name(file_list, commit['repo'])
            commit['shared_path'] = find_common_path(file_list)

        except:
            commit['shared_path'] = str(commit['repo'] + '/')

    create_head_msg(commit)


def create_head_msg(commit):

    header = """To: %(recipient)s
From: %(user)s <%(email)s>
Subject: git [%(repo)s] branch:%(branch)s path:%(shared_path)s...
""" % commit

    body = """
Repository:    %(repo)s
Branch:        %(branch)s
Tag:           %(tag)s
Committer:     %(user)s <%(email)s>
Commit Date:   %(date)s
Comment:       "%(subject)s"
%(body)s
New Hash:      %(new)s
Old Hash:      %(old)s
Shared Path:   %(shared_path)s
Files affected by this commit:
%(files)s
Crucible URL:      %(url)s
""" % commit
# Diff:
# %(diff)s
# """ % commit # TODO include Diff when mailed

    message = header + body
    # send_email(message) # TODO: use when configured
    print(message)
def create_tag_data(commit):

    commit['tag_name'] = commit['ref_name'].split('/tags/')[1]
    commit['old_tag'] = git('describe --tags %s^' % commit['ref_name'])
    commit['points_to'] = git(
        'rev-parse --verify %s^{commit}' % commit['tag_name']
    )

    commit['user'] = git_log('%cn', commit['ref_name'])
    commit['email'] = git_log('%ce', commit['ref_name'])
    commit['date'] = git_log('%ad', commit['ref_name'])
    commit['subject'] = git_log('%s', commit['ref_name'])
    commit['body'] = git_log('%b', commit['ref_name'])

    commit['url'] = transform_url(
        commit['url'],
        commit['repo'],
        commit['points_to']
    )
    create_tag_msg(commit)


def create_tag_msg(commit):

    header = """To: %(recipient)s
From: %(user)s <%(email)s>
Subject: git [%(repo)s] tag:%(tag_name)s created
""" % commit

    body = """
The following tag has been created:
Tag:        %(tag_name)s
Hash:       %(new)s
Points To:  %(points_to)s
Replaces:   %(old_tag)s
User:       %(user)s <%(email)s>
Date:       %(date)s
Comment:    %(subject)s
%(body)s
Crucible URL: %(url)s
""" % commit

    message = header + body
    # send_email(message)    # TODO: use when configured

def main():
    commit = {}
    stdin = fileinput.input().readline().split()

    commit['old'] = stdin[0]
    commit['new'] = stdin[1]
    commit['ref_name'] = stdin[2]

    commit['url'] = 'https://crucible.example.com/changelog/<repo>?cs=<hash>'
    commit['repo'] = get_repo_name()
    commit['recipient'] = get_recipient_address()
    

    if 'heads' in commit['ref_name']:
        create_head_data(commit)
    elif 'tags' in commit['ref_name']:
        create_tag_data(commit)
    else:
        m = 'Neither "heads" nor "tags" was in this ref name: %s'
        log.debug(m % ref_name)


if __name__ == '__main__':
    # log = create_logger('/var/log/git-post-receive')
    log = create_logger('../logs/git-post-receive')
    try:
        main()
    except:
        log.exception('Encountered an exception in the main loop.')