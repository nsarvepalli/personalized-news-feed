# Git Workflow Guide - Learning by Example

## 📚 Understanding Git

**GitHub = Remote Server (Cloud)** ☁️
```
Your GitHub: https://github.com/nsarvepalli/personalized-news-feed
```

**Your Computer = Local Copy** 💻
```
C:\Users\nsarv\personalized-news-feed
```

Git keeps these two in sync!

---

## 🔄 Basic Git Workflow

### **Scenario 1: You made changes and want to push to GitHub**

```
Your Computer (Local)          GitHub (Remote/Cloud)
     ↓                                ↓
  Changes                           Nothing
     ↓                                ↓
  git add .                    (Stage changes)
     ↓                                ↓
  git commit -m "msg"         (Create snapshot)
     ↓                                ↓
  git push origin main         (Upload to cloud)
     ↓                                ↓
  Changes                       Changes ✅
```

### **Scenario 2: Someone else pushed code, you want latest**

```
Your Computer (Local)          GitHub (Remote/Cloud)
     ↓                                ↓
  Old Code                      New Code ✅
     ↓                                ↓
  git pull origin main          (Download from cloud)
     ↓                                ↓
  New Code ✅                    New Code ✅
```

---

## 📤 HOW TO PUSH (Send your changes to GitHub)

### **Step 1: Check what changed**

```bash
git status
```

**Example output:**
```
On branch main
Changes not staged for commit:
  modified:   frontend/app.py
  modified:   backend/main.py

Untracked files:
  new_file.py
```

This shows:
- ✏️ `modified` = Files you changed
- ❓ `Untracked` = New files Git doesn't know about

---

### **Step 2: Stage (prepare) your changes**

```bash
git add frontend/app.py backend/main.py
```

Or add everything:
```bash
git add .
```

**What it does:** Tells git "I want to include these files in my next commit"

---

### **Step 3: Create a commit (take a snapshot)**

```bash
git commit -m "Brief description of what changed"
```

**Example:**
```bash
git commit -m "Fix: Improve delete button error handling"
```

**Good commit messages:**
- ✅ Start with action: "Fix", "Add", "Update", "Remove"
- ✅ Describe WHAT changed (not HOW)
- ✅ Keep it short (under 50 characters ideally)

**Examples:**
```bash
git commit -m "Fix: Remove button now properly deletes articles"
git commit -m "Add: New interest category for health news"
git commit -m "Update: Improve Supabase error messages"
```

---

### **Step 4: Push to GitHub**

```bash
git push origin main
```

**What it means:**
- `git push` = Upload my commits
- `origin` = GitHub (the remote server)
- `main` = Upload to main branch

**Expected output:**
```
To https://github.com/nsarvepalli/personalized-news-feed.git
   75d3b81..abc1234  main -> main
```

✅ **Success!** Your code is now on GitHub!

---

## 📥 HOW TO PULL (Get latest code from GitHub)

### **Step 1: Check your current status**

```bash
git status
```

Make sure you have no uncommitted changes. If you do:
```bash
git add .
git commit -m "Your message"
```

### **Step 2: Pull the latest code**

```bash
git pull origin main
```

**What it does:**
- Downloads latest commits from GitHub
- Merges them into your local code
- Updates all files

**Expected output:**
```
From https://github.com/nsarvepalli/personalized-news-feed
 * branch            main       -> FETCH_HEAD
Already up to date.
```

✅ You now have the latest code!

---

## 🔀 Complete Workflow Example

### **Scenario: You want to add a new feature**

#### **1. Pull latest code first (always start with this!)**
```bash
git pull origin main
```

#### **2. Make your changes**
Edit files in VS Code or your editor. Example:
- Change `frontend/app.py`
- Add new function in `backend/main.py`

#### **3. Check what changed**
```bash
git status
```

Output:
```
modified:   frontend/app.py
modified:   backend/main.py
```

#### **4. Stage your changes**
```bash
git add frontend/app.py backend/main.py
```

Or everything:
```bash
git add .
```

#### **5. Create a commit**
```bash
git commit -m "Add: New health news category filtering"
```

#### **6. Push to GitHub**
```bash
git push origin main
```

#### **7. Verify on GitHub**
Visit: https://github.com/nsarvepalli/personalized-news-feed

You'll see your new commit!

---

## 🌳 Understanding Branches (Optional but Important)

### **What's a branch?**
A branch is like a parallel copy of your code where you can experiment without affecting `main`.

### **Using branches (Professional way):**

#### **1. Create a feature branch**
```bash
git checkout -b feature/add-email-notifications
```

**Means:** Create and switch to new branch named `feature/add-email-notifications`

#### **2. Make changes on your branch**
```bash
git add .
git commit -m "Add email notification feature"
```

#### **3. Push your branch to GitHub**
```bash
git push origin feature/add-email-notifications
```

#### **4. Create a Pull Request on GitHub**
- Go to: https://github.com/nsarvepalli/personalized-news-feed
- Click "Pull requests" tab
- Click "New Pull Request"
- Select your branch
- Write description
- Submit!

#### **5. Merge when ready**
- GitHub shows all changes
- Reviewers can comment
- Click "Merge" when approved

#### **6. Delete the branch**
```bash
git branch -d feature/add-email-notifications
```

---

## 📋 Quick Command Reference

### **Essential Commands**

```bash
# Check status
git status

# Stage changes
git add filename.py          # Single file
git add .                    # All changes

# Create commit
git commit -m "Your message"

# Push to GitHub
git push origin main

# Pull from GitHub
git pull origin main

# See commit history
git log --oneline            # Short version
git log                      # Detailed version

# See what changed in a file
git diff filename.py
```

### **Branch Commands**

```bash
# See all branches
git branch -a

# Create new branch
git checkout -b feature/name

# Switch branches
git checkout main
git checkout feature/name

# Delete branch
git branch -d feature/name
```

---

## ⚠️ Common Mistakes & How to Fix

### **Mistake 1: "I committed but forgot to add a file"**

```bash
git add forgotten_file.py
git commit --amend --no-edit
```

This adds the file to your last commit without changing the message.

---

### **Mistake 2: "I want to undo my last commit"**

```bash
git reset --soft HEAD~1
```

This undoes the commit but keeps your changes.

---

### **Mistake 3: "I pushed to main but should have used a branch"**

Don't worry! Just:
1. Create a new branch from current main
2. Create a Pull Request
3. Next time use branches first

---

### **Mistake 4: "Pull says conflict"**

Example error:
```
CONFLICT (content merge): Merge conflict in frontend/app.py
```

This means GitHub and your local copy have different changes to the same line.

**Fix:**
```bash
# Open the file and look for:
<<<<<<< HEAD
  Your local code
=======
  Code from GitHub
>>>>>>> origin/main

# Choose which version you want, delete the markers, save
git add .
git commit -m "Resolved merge conflict"
git push origin main
```

---

## 🎯 Practice Workflow (Try This!)

### **Your Task: Add a comment to a file**

#### **Step 1: Pull latest**
```bash
cd C:\Users\nsarv\personalized-news-feed
git pull origin main
```

#### **Step 2: Make a tiny change**
Open `frontend/app.py`, add a comment at the top:
```python
# This app searches and summarizes news articles using AI
```

#### **Step 3: Check status**
```bash
git status
```

#### **Step 4: Stage the file**
```bash
git add frontend/app.py
```

#### **Step 5: Create commit**
```bash
git commit -m "Add: Comment explaining app purpose"
```

#### **Step 6: Push to GitHub**
```bash
git push origin main
```

#### **Step 7: Check GitHub**
Visit: https://github.com/nsarvepalli/personalized-news-feed/commits/main

You'll see your new commit! 🎉

---

## 📝 Summary: The Three Magic Commands

```bash
# 1. Before starting work
git pull origin main

# 2. After making changes
git add .
git commit -m "Describe what you changed"

# 3. Send to GitHub
git push origin main
```

Repeat this workflow for every change!

---

## 🚀 Next Level: Working with Branches

When you're comfortable, use this workflow:

```bash
# 1. Pull latest main
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes
# (edit files...)

# 4. Commit to your branch
git add .
git commit -m "Add your feature"

# 5. Push branch to GitHub
git push origin feature/your-feature-name

# 6. Go to GitHub, create Pull Request
# 7. Review, then merge to main
```

This keeps main always stable! ✅

---

## 💡 Tips

- **Always pull before starting work** - Gets latest code
- **Commit often** - Small commits are easier to understand
- **Write good messages** - Future you will thank you
- **Push regularly** - Backup your code to cloud
- **Use branches** - Keeps main clean and stable

---

## 🆘 Need Help?

Run this to see all your commits:
```bash
git log --oneline
```

Run this to see uncommitted changes:
```bash
git status
```

Run this to see what changed in a file:
```bash
git diff filename.py
```

Good luck! You're learning git like a pro! 🎉
