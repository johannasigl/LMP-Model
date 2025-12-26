---
applyTo: "**/*.py"
---

In agent mode, always create the following files for a project
- main.py
    - contains the main parameters of the script, defined in a dictionary called param
    - contains the overall workflow
    - its logic should be easy to follow
    - must not contain definitions of functions or classes
- func.py
  - contains the logic of the project, i.e. the heart of the code
- plot.py
  - contains all code related to visualization of data and results
  - always plot using the library plotting_standards (assumed to be installed)
- data.py
  - contains all code that collects, stores, loads and manages data

Strictly implement the following DO-NOTS:
- do not create virtual environments
- do not create dummy data unless asked for
- do not build in checks such as try except unless explicitly asked for

In addition, always follow these best practices:
- always comment your code with docstrings for functions and classes
- always convert time stamped data to datetime
- if using pandas dataframes or series always set the index to datetime
- follow the PEP 8 style guide for Python
- always prioritize readability and clarity