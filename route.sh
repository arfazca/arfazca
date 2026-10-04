#!/bin/bash

breakStrSize=50
breakStrIter=$(printf '_%.0s' $(seq 1 "$breakStrSize"))

cd "$(dirname "$0")" || exit 1

function versionCheck() {
  git config advice.addIgnoredFile false
  if [ ! -d .git ]; then
    echo -e "No Version Control History Found\nInitializing Git Version Control"
    git --version
    git init
  else
    echo -e "\nVersion Control History found"
  fi
}

function syncBranch() {
  echo -e "YES'ED\n${breakStrIter}"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    git stash push -q -m "route.sh backup $(date +'%Y-%m-%d %H:%M')"
    echo "Local changes saved as: $(git stash list -1 --format=%gs)"
  fi
  git pull --rebase --quiet
  echo -e "${breakStrIter}\n\t\tYour Repository is synced\n\t\twith the latest commit :)\n${breakStrIter}"
}

function pushChanges() {
  local currentBranch
  currentBranch=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$branch" == "generated" ]]; then
    echo "Error: 'generated' is written by CI only (the banner and its frames). Push to main instead."
    return 1
  fi
  if [[ "$currentBranch" != "$branch" ]]; then
    echo "Error: Current branch ($currentBranch) and push target branch ($branch) are different."
    return 1
  fi

  git add -A
  if git diff --cached --quiet; then
    echo "Nothing to commit."
    return 0
  fi
  echo -e "${breakStrIter}\nCommitting:"
  git status -s
  git commit -q -m "$CommitMessage"$'\n\nCommit by @arfazca on '"$(date +'%a %d %b %Y')"

  if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
    git pull --rebase --quiet || { echo "Rebase stopped on a conflict: fix it, then run git rebase --continue"; return 1; }
  fi

  if git push --set-upstream origin "$branch" --quiet; then
    echo -e "${breakStrIter}\n\t\tYour changes have been pushed\n\t\tto the repository :)\n${breakStrIter}"
  else
    echo -e "${breakStrIter}\n\t\tError: Failed to push changes to the repository\n${breakStrIter}"
    return 1
  fi
}

function gitWorkflow() {
  find . -name ".DS_Store" -type f -delete
  versionCheck
  echo -e "\n${breakStrIter}\n\n\t\tDELETE LOCAL CHANGES? (YES) \n\t\t\tOR\n\t\tPUSH LOCAL CHANGES (ENTER)\n"
  read -r -s -n 3 -p "(yes/ENTER): " answer

  if [[ $answer == "yes" || $answer == "Yes" || $answer == "YES" ]]; then
    syncBranch
  else
    echo -e "ENTER'ED\n${breakStrIter}"
    read -r -p "Your Commit Message: " CommitMessage
    if [[ -z "$CommitMessage" || ${#CommitMessage} -lt 3 ]]; then
      CommitMessage="Routine Commit"
    fi
    echo "For your information, the branch you're in is: {$(git rev-parse --abbrev-ref HEAD)}"
    read -r -p "Enter the branch to push the code to (default: main): " branch
    branch=${branch:-main}
    pushChanges
  fi
}

gitWorkflow
