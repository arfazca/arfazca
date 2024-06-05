# #!/bin/bash

# Function to escape LaTeX special characters
ESC_LATEX() {
    echo "$1" | sed -e 's/\\/\\\\/g' \
                    -e 's/{/\\{/g' \
                    -e 's/}/\\}/g' \
                    -e 's/\$/\\$/g' \
                    -e 's/&/\\&/g' \
                    -e 's/#/\\#/g' \
                    -e 's/_/\\_/g' \
                    -e 's/%/\\%/g' \
                    -e 's/\^/\\^/g' \
                    -e 's/\~/\\~/g'
}

# Prompt for variables with default values
read -p "Enter Position [Software Developer]: " position
position=${position:-Software Developer}

read -p "Enter Company Name [Some-Company]: " company_name
company_name=${company_name:-Some-Company}

read -p "Enter Company Name Suffix [Some-Corporation]: " company_suffix
company_suffix=${company_suffix:-" "}

# List of provinces
provinces=("Ontario" "Alberta" "Quebec" "Manitoba" "British Columbia" "Nova Scotia" "Remote")

# Lists of cities for each province
ontario_cities=("Toronto,Ottawa,Waterloo,Oakville,Markham,Mississauga,Brampton,Hamilton,London,Kitchener,Windsor,Guelph,Cambridge,Barrie,Kingston,Thunder Bay,Sudbury")
alberta_cities=("Edmonton,Calgary,Red Deer,Lethbridge,St. Albert,Medicine Hat,Grande Prairie,Airdrie,Spruce Grove,Leduc")
quebec_cities=("Montreal,Quebec City,Laval,Gatineau,Longueuil,Sherbrooke,Saguenay,Trois-Rivières,Terrebonne,Saint-Jean-sur-Richelieu,Repentigny,Drummondville,Saint-Jérôme,Granby,Blainville,Boucherville")
manitoba_cities=("Winnipeg,Steinbach,Brandon,Thompson,Portage la Prairie,Winkler,Selkirk,Morden,Dauphin,The Pas")
bc_cities=("Vancouver,Victoria,Surrey,Burnaby,Richmond,Abbotsford,Coquitlam,Kelowna,Langley,Saanich,Delta,Kamloops,Nanaimo,Chilliwack,Prince George,Penticton,Vernon,Courtenay,Campbell River,Port Coquitlam,New Westminster,Maple Ridge,North Vancouver")
nova_scotia_cities=("Halifax,Dartmouth,Sydney,Truro,New Glasgow,Glace Bay,Kentville,Amherst,Bridgewater,Yarmouth")
remote_cities=("Remote, Canada")

# Function to get cities for a given province
get_cities() {
    case $1 in
        "Ontario") echo "${ontario_cities[@]}" ;;
        "Alberta") echo "${alberta_cities[@]}" ;;
        "Quebec") echo "${quebec_cities[@]}" ;;
        "Manitoba") echo "${manitoba_cities[@]}" ;;
        "British Columbia") echo "${bc_cities[@]}" ;;
        "Nova Scotia") echo "${nova_scotia_cities[@]}" ;;
        "Remote") echo "${remote_cities[@]}" ;;
        *) echo "" ;;
    esac
}

# Step 1: Ask the user to select a province
province_str=$(printf "%s\n" "${provinces[@]}")
province_query="Enter Province name:";
city_query="Enter City name:";
locationState=$(echo "$province_str" | fzf --height 10% --border --prompt "$province_query ")

# Step 2: Ask the user to select a city within the selected province
if [ -n "$locationState" ]; then
    cities=$(get_cities "$locationState")
    locationCity=$(echo "$cities" | tr ',' '\n' | fzf --height 20% --border --prompt "Enter city name: ")

    [ -z "$locationCity" ] && { echo "No city selected."; exit; }
else
    echo "No province selected."
    exit
fi

echo "$province_query " "$locationState"
echo "$city_query " "$locationCity"

read -p "Enter Division [Human Resources]: " division
division=${division:-Human Resources}

read -p "Enter Terms [an 8-month]: " terms
terms=${terms:-an 8-month}

filename="Hussain, Arfaz - Placement Application - ${position} - ${company_name} ${company_suffix} - ${division}"

# Escape LaTeX special characters in variables
position=$(ESC_LATEX "$position")
company_name=$(ESC_LATEX "$company_name")
company_suffix=$(ESC_LATEX "$company_suffix")
division=$(ESC_LATEX "$division")
locationCity=$(ESC_LATEX "$locationCity")
locationState=$(ESC_LATEX "$locationState")
terms=$(ESC_LATEX "$terms")

# Generate LaTeX file content
cat <<EOL > tntx.tex
\documentclass[a4paper, 12pt]{letter}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage{lmodern}
\usepackage{xcolor}
\usepackage{adjustbox}
\usepackage{fancyhdr}
\usepackage{etoolbox}
\usepackage[left=0.75in, right=0.75in, top=0.2in, bottom=0.5in]{geometry}

% Define the new ruler command
\newcommand{\CustomRuler}{\vspace{0\baselineskip}\textcolor{black}{\rule{\linewidth}{0.5pt}}\vspace{-0.5\baselineskip}}

% Define color for hyperlinks
\definecolor{linkblue}{HTML}{0000FF} % Blue color

% Set up hyperref package
\hypersetup{
    colorlinks=true,
    linkcolor=linkblue, % Color of internal links
    urlcolor=linkblue, % Color of URLs
}

% Redefine footer style to remove page number
\fancypagestyle{plain}{
    \fancyhf{} % Clear header and footer
    \renewcommand{\headrulewidth}{0pt}
}

% Define variables
\newcommand{\Position}{$position}
\newcommand{\CompanyName}{$company_name}
\newcommand{\CompanyNameSuffix}{$company_suffix}
\newcommand{\Division}{$division}
\newcommand{\LocationCity}{$locationCity}
\newcommand{\LocationState}{$locationState}
\newcommand{\Terms}{$terms}

\begin{document}
\pagestyle{empty}

% Header with name and links
\noindent
\begin{minipage}[t]{0.5\textwidth}
    \raggedright
    \vspace{3pt}
    {\fontsize{30}{34}\selectfont Arfaz Hossain} \\\\
    \vspace{2pt}
    {\fontsize{12}{14}\selectfont Victoria, British Columbia}
\end{minipage}%
\begin{minipage}[t]{0.5\textwidth}
    \raggedleft
    \vspace{1pt}
    \href{https://www.github.com/arfazhxss}{\fontsize{12}{14}\selectfont www.github.com/arfazhxss} \\\\
    \href{https://www.linkedin.com/in/arfazhussain}{\fontsize{12}{14}\selectfont www.linkedin.com/in/arfazhussain} \\\\
    \href{https://arfazhxss.ca/resume.pdf}{\fontsize{12}{14}\selectfont arfazhxss.ca/resume.pdf}
\end{minipage}

\CustomRuler

\vspace{10pt} \today

\vspace{5pt}
% Letter details
\textbf{\CompanyName}\textbf{ \CompanyNameSuffix} \\\\
\text{Division: \Division} \\\\
\text{Location: \LocationCity}, \text{\LocationState} \\\\

\vspace{-5pt}

\text{Dear Hiring Manager,}

\vspace{3pt}
I am excited to apply for the {\fontsize{11}{11.5}\selectfont \bfseries \Position} Co-op Placement at {\fontsize{11}{11.5}\selectfont \bfseries \CompanyName}. I am a software engineering student at the University of Victoria in British Columbia. I am eager to learn and grow in the field of computer and software engineering, and I believe that this role will help me gain valuable work experience related to my interests and help me acquire a practical understanding in a real-world setting.

{\fontsize{11}{11.5}\selectfont \bfseries I have a fascination for developing web and mobile applications, and I am continually learning new skills through personal projects outside school.} I have been involved in more than 13 software development projects, including developing an iOS weather application in Swift Programming Language, creating a 3D graphical simulation of a Rubik’s Cube in OpenGL and C++, and developing web development projects in React, JavaScript, and TypeScript. I have been an active member of the Engineering Students Society and UVic Students Society, where I have worked as a mentor during my second year and volunteered in multiple events while engaging in software development projects throughout my time.

{\fontsize{11}{11.5}\selectfont \bfseries Throughout my academic endeavours, I have had the chance to learn the basic concepts of object-oriented programming, software architecture and development, testing and evolution, data structures and algorithms.} I have actively contributed to UVic Rocketry and VikeLabs as a full-stack web developer, where I have spent much of my time collaborating and developing solutions to issues while reviewing code mostly written in TypeScript and Python. My experience includes developing schemas in both MongoDB and PostgreSQL using Atlas, as well as other database tools and services such as Prisma, PlanetScale, and Mongoose. Throughout my projects, I have used automation and testing frameworks such as Selenium, Puppeteer, JUnit, Maven, and Gradle. While working in teams at UVic Rocketry, I used ticketing tools such as Jira and Kanban. I plan to specialize in visual computing and data mining, involved in projects that are closely tied to my interests. My strength lies in my ability to work independently, collaborate, adapt to new environments, and gain familiarity with new tools necessary to excel in this role.

{\fontsize{11}{11.5}\selectfont \bfseries I am currently available for \Terms\ work term and would be open to the possibility of participating in more than two consecutive terms.} Thank you for considering my application. I look forward to the opportunity to further discuss my skills and experience with \CompanyName.

\vspace{10pt}
\text{Most Sincerely,}

\vspace{-25pt}
\begin{flushleft}
    \hspace*{-1cm}\includegraphics[width=10cm]{../../9.1 PreProcessed/signature.png}\vspace{-1cm}
\end{flushleft}


\vspace{-10pt}
\ps{\textbf{Arfaz Hossain} (He/Him)\\\\
Software Engineering Student,\\\\
University of Victoria}

\end{document}
EOL

echo "$filename"
mv tntx.tex "9.2 PostProcessed/tex-outputs/" || exit
cd "9.2 PostProcessed/tex-outputs"
pdflatex tntx.tex && mv tntx.pdf "$filename.pdf"
cp "$filename.pdf" ../
cp "$filename.pdf" ../../1\ jne\ 10/
shopt -s extglob
rm -f !(*.tex)
cd ../../ || exit

echo "Cover letter generated and saved as $filename.pdf"