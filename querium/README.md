# Querium Corp Open edX Customizations

## social_core
This folder contains oAuth code for facilitating single sign-on to Openstax.org.

## Guide for working with Git
![Git Work Flow](https://github.com/QueriumCorp/edx-platform.roverplatform.com/blob/querium.dev/querium/doc/git-workflow.png)


### Work with a feature branch off querium.dev
```
# Create querium.dev/oauth branch off querium.dev
git checkout -b querium.dev-oauth querium.dev
git branch --set-upstream-to=origin/querium.dev-oauth querium.dev-oauth

# Merge features into querium.dev
git checkout querium.dev
git merge querium.dev-oauth

# Alternative merge, without Fast-forward
git checkout querium.dev
git merge --no-ff querium.dev-oauth

# Push your changes to Github
git push origin querium.dev
git push origin querium.dev-oauth

```

### Update your feature branch with the current contents of querium.dev
```
# first, update your local repository with the current contents of querium.dev
git checkout querium.dev
git pull

# next, merge querium.dev into your feature branch
git checkout querium.dev-oauth
git merge querium.dev
```


### Consolidate superfluous commits
```
git checkout querium.dev/[FEATURE-BRANCH]

# Review the local commit log, identify the quantity and keys of the commits to "squash"
git log

# Suppose you've determined that you want to squash the last 5 commits ....
git reset --soft HEAD~5 &&
git commit
```

### Deploy querium.dev to querium.master
```
# ensure that your local querium.master is up to date
git checkout querium.master
git pull

# step 1:merge querium.master into querium.dev, check for merge conflicts
git checkout querium.dev
git pull
git merge querium.master
git push origin querium.dev


# * resolve any conflicts that might have surfaced *

# step 2: deploy to querium.master
git checkout querium.master
git pull
git merge querium.dev
git push origin querium.master

```
