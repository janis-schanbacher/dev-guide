# Deployment using bare Git repository and Git hooks

- Follow [this Tutorial](https://medium.com/factor1/setting-up-server-environments-for-a-seamless-git-deployment-d0b88e8d1c24). Contents:
  - Create bare Git repository on Server and add post-receive hook
  - Add remote to local repository
- change destinations for the different branches/environments (see [post-receive](post-receive))
- Add required actions to run application

## Troubleshooting
- Ensure to use LF instead of windows CRLF
- Escape whitespaces in paths, or use quotation marks
- Ensure remote can be reached (ssh setup)
