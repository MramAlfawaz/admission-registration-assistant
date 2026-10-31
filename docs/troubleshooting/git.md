# git

## "Please tell me who you are" on the first commit
**Fix:** `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.

## `.DS_Store` files appear in `git status`
**Why:** macOS writes them in every folder opened in Finder.
**Fix:** they are ignored (`.gitignore`); if one was committed earlier: `git rm --cached path/.DS_Store`.
