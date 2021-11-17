# Deployment using bare Git repository and Git hooks

- [post-receive](post-receive):
  - saves file tree in of master and development branch in different directories (`production` and `staging`)
  - Installs python modules listed in `requirements.txt`
  - runs [post-receive.py](post-receive.py)  
    - Provides detailed output on deployment, and is prepared to send it via mail.
  
## Sources
- https://medium.com/factor1/setting-up-server-environments-for-a-seamless-git-deployment-d0b88e8d1c24
  - Create bare Git repository on Server and add post-receive hook
  - Add remote to local repository
- change destinations for the different branches/environments (see [post-receive](post-receive))
- Add required actions to run application

## Troubleshooting
- Ensure to use LF instead of windows CRLF
- Escape whitespaces in paths, or use quotation marks
- Ensure remote can be reached (ssh setup)
- Try with local setup: [tutorial](https://thehorrors.org.uk/snippets/git-local-filesystem-remotes/)
- Change `python3` to `python`, and `pip3` to `pip`. Add path to python binary if necessary
