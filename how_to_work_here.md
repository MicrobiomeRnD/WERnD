# everytime you start working on this folder, work like this:


## 1. Sync the main branch
```powershell
git checkout main
git pull origin main
```

## 2. Create a branch to contain your today's new update 
### Name a branch. Freely, but descriptively. Do not use other than regular alphabets and '-' and '_'.
### In the examples below, I assume that I created a new branch with a name 'update-research-page'
```powershell
git checkout -b update-research-page
```

## 3. Commit after you make changes. Do this in small chunks.
```powershell
git add .
git commit -m "move research page scripts"
```

## 4. Push the branch you made to the online repository
```powershell
git push -u origin update-research-page
```

## 5. Go to the github repository web page (https://github.com/MicrobiomeRnD/WERnD)
## and merge the Pull Request into main.
## When you finish the merge Pull Request, delete the branch you created today (ex.  update-research-page).

# Now 1 cylce of update is over. 
# For the next update, s tart from the step number 1.
```powershell
git checkout main
git pull origin main
```

