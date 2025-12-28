<div align="Center">

<img width="1050" height="488" alt="banner" src="https://github.com/user-attachments/assets/b17d1f9c-d645-41b7-9909-f3c8117c0d62" />

  <a style="text-decoration:none">
    <img src="https://img.shields.io/github/downloads/rohankishore/Schemix/total.svg"/>
  </a>  <a href='https://ko-fi.com/V7V7QZ7GS' target='_blank'><img height='10' style='border:0px;height:22px;' src='https://storage.ko-fi.com/cdn/kofi5.png?v=3' border='1' alt='Buy Me a Coffee at ko-fi.com' /></a>
      
  <p align="center">
    An IDE for Engineers, Scientists and Students made entirely with Python
    <br />
    <a href="https://github.com/rohankishore/Schemix/wiki"><strong>Explore the docs »</strong></a>   
    <br />
    <br />
    <a href="https://github.com/rohankishore/Schemix/issues">Report Bug</a>
    ·   
    <a href="https://github.com/rohankishore/Schemix/issues/new?assignees=&labels=&projects=&template=feature_request.md&title=">Request Feature</a>

  </p>
</div>    

<br>
<hr>

<!-- ABOUT THE PROJECT -->
## 📖 About The Project

Schemix is a modern, student-focused, Qt-based study companion designed for engineering and science learners. With support for rich note-taking, graph plotting, offline periodic table, unit conversion, scientific calculations, and markdown + LaTeX rendering, Schemix aims to be your all-in-one knowledge workstation.

<br> 

<img width="1920" height="1140" alt="image" src="https://github.com/user-attachments/assets/4433adf2-87a5-440c-b794-25d5211f7675" />

<img width="1920" height="1140" alt="image" src="https://github.com/user-attachments/assets/083fa0f9-230a-43de-99c2-0bfc12c8a3ee" />

<img width="1920" height="1140" alt="image" src="https://github.com/user-attachments/assets/3aa43381-a9ad-4a58-95f7-8afb73b6723f" />

<img width="1920" height="1140" alt="image" src="https://github.com/user-attachments/assets/97ad2dec-0154-4040-946c-410093c0a232" />


<br>


***The main highlights of Schemix are:***
- Organized Boards: Create boards → subjects → chapters to manage notes and quizzes efficiently.
- Rich Text Editor:
    - Supports headings, bullet lists, numbered points
    - Inline math expressions via MathJax
    - Insert images and icons for visual notes
- Electric Circuit Analysis
- SPC Analysis
- Spring Analysis
- Chemical Reaction Balancer
- Graph Plotting: Plot mathematical equations on a real number range and insert the graph into the notes
- Built-in offline periodic table
- Wikipedia Summary Viewer: Search any topic and view its Wikipedia snippet inside the app.
- Unit Converter: Convert units across categories like length, time, temperature, etc.
-  Scientific Calculator: Fully featured calculator with keyboard input support and dockable UI.

  
<!-- GETTING STARTED -->
## 🏃 Getting Started

Let's set up Schemix on your PC!

### Prerequisites
- Windows 10 x64 or later, a Linux distro running kernel 6.x or later, or macOS High Sierra or later
- Python 3.9 or later
- Python installation is bootstrapped with pip
- (Recommended) A fresh venv created with `python -m venv venv` and activated with `venv\Scripts\activate`
- The contents of `requirements.txt` installed via `pip install -r requirements.txt`
- (If building an installer) Inno Setup 6.4.3 or later

### Installation
You can download a prebuilt installer from the Releases or build one yourself. If using prebuilt installers, just skip to the use section.

#### Building the installer
1. Clone the repo or download a tarball
2. Install all prerequisites
3. `python build.py` to compile the program first
4. Open up the `.iss` Inno Setup script and compile it via Ctrl+F9 or `Build > Compile` - installer can be found in `Output` folder

##### Using the installer
Just run the `.exe` file, duh.

### Testing
This is for people who solely just want to run without installation for mostly testing purposes.

We need the prerequisites above. After getting them, you can run the program with `pythonw main.py` to run it without flooding your terminal with logging, or you can just run with `python main.py` to troubleshoot errors and debug it.

<br>


## 🛣️ Roadmap

- Plugin Architecture
- AutoCAD support
- <strike> Electric Circuit Analysis </strike>
- <strike> SPC Analysis </strike>

<b> and much much more... </b>


<b>

<!-- CONTRIBUTING -->
## 🛂 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would improve this, please fork the repository and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contributors

<a href="https://github.com/rohankishore/Schemix/graphs/contributors">
  <img class="dark-light" src="https://contrib.rocks/image?repo=rohankishore/Schemix&anon=0&columns=25&max=100&r=true" />
</a>

<b>

<!-- LICENSE -->
## 🪪 License

Distributed under the GPLv3 License. See `LICENSE.txt` for more information.
