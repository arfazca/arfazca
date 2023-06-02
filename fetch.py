import requests
import pygal

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
    repo_languages = response.json()
    for language in repo_languages:
        if language in languages:
            languages[language] += repo_languages[language]
        else:
            languages[language] = repo_languages[language]

# Generate the pie chart
chart = pygal.Pie()
for language in languages:
    chart.add(language, languages[language])

chart.title = "GitHub Language Statistics"
chart.render_to_file("language_pie_chart.svg")

# Generate the README.md file content
readme_content = "# GitHub Language Statistics\n\n"
for language in languages:
    readme_content += f"- {language}: {languages[language]}\n"

# Write the content to the README.md file
with open("README.md", "w") as readme_file:
    readme_file.write(readme_content)
