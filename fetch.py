import requests
import matplotlib.pyplot as plt

# GitHub username
username = "arfazhxss"

# Fetch user's repository information
repo_url = f"https://api.github.com/users/{username}/repos"
response = requests.get(repo_url)
repos = response.json()

# Count the languages used in the repositories
languages = {}
for repo in repos:
    repo_languages_url = repo["languages_url"]
    response = requests.get(repo_languages_url)
    if response.status_code == 200:  # Check if the response is successful
        repo_languages = response.json()
        for language in repo_languages:
            if language in languages:
                languages[language] += repo_languages[language]
            else:
                languages[language] = repo_languages[language]

# Create labels and sizes for the pie chart
labels = list(languages.keys())
sizes = list(languages.values())

# Create the pie chart
fig, ax = plt.subplots()
ax.pie(sizes, labels=labels, autopct='%1.1f%%')

# Save the pie chart as an image file
plt.savefig('language_pie_chart.png')

# Close the plot to release resources
plt.close()
