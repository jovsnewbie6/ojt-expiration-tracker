# Run these commands after installing Git and creating a GitHub repository.
# Replace <your-repo-url> with your actual GitHub repository URL.

git init
git branch -m main
git add .
git commit -m "Deploy ready"
git remote add origin <your-repo-url>
git push -u origin main

# After pushing, connect this repository to Render using render.yaml.
