import matplotlib.pyplot as plt
import requests


def get_language_stats(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/languages"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def generate_pie_chart(language_stats):
    languages = list(language_stats.keys())
    percentages = list(language_stats.values())

    plt.pie(percentages, labels=languages, autopct='%1.1f%%')
    plt.axis('equal')
    plt.savefig('language_chart.png')  # Save the chart as a PNG file


def edit_readme_file():
    # Read the existing content of README.md
    with open('README.md', 'r') as file:
        readme_content = file.read()

    # Append the required information to README.md
    new_content = readme_content + '''
- 🌱 Hi! I am a current Software Engineering student at University Of Victoria (UVic)!
- 🌱 Relevant Coursework: CSC 111-115 (Fundamentals of Programming with Engineering Applications), SENG 265-275 (Software Development and Testing), 
     CSC 225-226 (Algorithm and Data Structures), SENG 310 (Human Computer Interaction), CSC 230 (Computer Architecture).
- 🌱 How to reach me: Email <arfazhussain@uvic.ca>; Phone: (250)-880-8402
'''

    # Save the new content to README.md
    with open('README.md', 'w') as file:
        file.write(new_content)


# Replace 'arfazhxss' with your GitHub username and 'arfazhxss' with your repository name
username = 'arfazhxss'
repo = 'arfazhxss'

# Retrieve language statistics
language_stats = get_language_stats(username, repo)

# Generate the pie chart
generate_pie_chart(language_stats)

# Edit the README.md file
edit_readme_file()
