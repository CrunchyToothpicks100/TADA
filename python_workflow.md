# Python Workflow (CrunchyToothpicks100)
This is how I have set up my python runtimes, poetry, Django, and the virtual environment, just in case anyone needs to know. There are many other ways to manage all this stuff, Conda especially comes to mind. But this is my method that I like to use.

## Python Install Manager
I use something called the windows python install manager.

It's totally optional, but this makes managing versions of python much easier. Once it's fully setup, you can install, uninstall, and switch python versions with simple commands. And you won't have to worry about configuring your PATH ever again.

    - Docs: https://peps.python.org/pep-0773  
    - Installation: https://www.python.org/downloads/release/pymanager-260/  

After installing it, you can run "py install 3.14" which takes you to a CLI installation wizard. Here you can tell the wizard to automatically add this version of python to your PATH. To see all your runtimes, run ```py list```. The runtime you are currently using will be highlighted in green with an asterisk next to it.

To see all commands you can do with the python install manager, just do ```py help```.

### PATH 
This info is good to know if you are debugging or having issues with the setup process.

The executable for the python install manager lives here: '%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\py.exe'  
That folder should already be in your user PATH, so it should immediately work in powershell after installation.

When you run "where.exe python", it will show a list of different python executables. **Powershell will automatically use the python executable at the top of your list.**  

The one at the top should be 'C:\Users\USER\AppData\Local\Python\bin\python.exe'. If not, you may need to reconfigure your PATH. This is what python install manager uses whenever you type a command with "python". 

This executable is actually an alias (shim) that will run a different executable for the specific python version you selected. If you want to see where this other executable lives, run this ```py -c "import sys; print(sys.executable)"``` 

When you run a command with "py" that isn't related to managing installations, it also gets rerouted to your selected runtime. This is why commands like ```py manage.py ...``` do the exact same thing as ```python manage.py ...```


## Virtual environment
The most straightforward way to create a virtual environment is to navigate to your project directory and run ```py -m venv .venv```. The first 'venv' is the venv module that comes preinstalled with python. The second '.venv' is the name you are giving your virtual environment. You could technically name it anything. Sometimes you'll see people name it '.venv' since all their '.' files are automatically filtered out in .gitignore.  

To activate your virtual environment, you run ```.\.venv\scripts\activate``` (you sould see '(venv)' in green in your terminal)  
To deactivate your virtual environment, you run ```deactivate```  
To delete your '.venv', run ```rm .venv```  

To see a list of your pip packages, run ```pip list```

**One important thing to know:** When your '.venv' is NOT activated, and you install a package with ```pip install [package]```, this installs the package **globally**. When your '.venv' IS activated, this installs the package into your virtual environment, which is local to your project.

It's standard practice to put .venv/ in your .gitignore file so that it doesn't clutter your github repository. However, this might lead to other developers using the wrong packages or the wrong environment. There are two main ways to solve this problem.

Solution 1: Activate your '.venv' and run ```pip freeze > requirements.txt```. This makes a list of packages that you can push to github. Then, it can easily be installed with ```pip install -r requirements.txt```. Just make sure everyone is using the same version of Python.
Solution 2: Use Poetry


## Poetry
Poetry is what we are using for TADA. It is a package manager for your python virtal environments that micro-manages your dependencies. Is it necessary? No. Am I using it just to feel like a pro python developer? Probably. Has it caused random issues that made me panic? Yes. But the following info should save you from a few headaches. 

First of all, you do NOT install Poetry into your virtual environment. That was my first mistake.   

Install (global):  
```
pip install pipx
pipx install Poetry
```

It's recommended to install Poetry with pipx instead of pip so that Poetry gets its own isolated environment globally. This prevents Poetry's own dependencies from conflicting with anything else. I don't know what pipx is or how it works. I'm just trusting what I've read.

By default, Poetry creates the '.venv' inside a central cache directory, not in the project folder. I would recommend configuring Poetry to put the '.venv' inside the project directory instead:    

```poetry config virtualenvs.in-project true```

This is what most IDEs (PyCharm, VS Code) expect and auto-detect.

Instead of running ```pip install [package]``` to install specific packages, you will run ```poetry install [package]```.

Poetry mainly uses two files, 'pyproject.toml' and 'poetry.lock'. The first file automatically populates with your dependencies when you install them. Once you're done installing packages, run ```poetry lock``` to generate the lock file, which should NOT be edited.

When your fellow software dev needs to install all your packages and create their virtual environment, they can just run ```poetry install```, and poetry does both using the information from 'poetry.lock'.

Check out the Dockerfile in TADA to see how the docker container uses Poetry to automatically install packages.


## Django

It's best to install Django globally with ```pip install Django```


## Powershell
This will speed up your powershell workflow.

One really cool thing you can do in powershell is create a profile, which allows you to set aliases for commands in all powershell sessions. The possibilities are endless. In Linux, there is a similar file ~/.bashrc that does the same thing.

Try opening your normal windows powershell and run ```notepad $profile```, and if that doesn't work, it's because you don't have one yet. Use ```New-Item -Path $profile -ItemType File -Force``` to create your profile. Then run ```notepad $profile``` again, and you should be able to edit it.

Here are some useful aliases I would add to your profile:

```
# Python venv
function venvon { 
	try { .\.venv\scripts\activate }
	catch { .\venv\scripts\activate }
}
function venvoff { deactivate }
function venvmake { py -m venv .venv }
function venvdel { Remove-Item -Path .venv -Recurse -Force }

# Notepad and notepad++
function note { notepad @args }
function notepp { notepad++ @args }
function npp { notepad++ @args }

# Run Git's version of bash, if installed
function gitbash { start "C:\Program Files\Git\bin\bash.exe" }

# Find path of application in PATH, Linux style
function which { where.exe @args }

# Quick edit
function profile { note "${env:USERPROFILE}\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1" }
```

As you might have guessed, 'venvon' will activate your virtual environment. 'venvoff' will deactivate. 'venvmake' will make one. 'venvdel' will delete it. 'profile' will edit your profile.

Sometimes, for some weird reason, VSCode will use powershell 7 by default, which has its own separate profile. You can fix this by opening your profile in your VSCode and adding this one line: 

```. "${env:USERPROFILE}\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1"```  

This means it will add your powershell 5.1 profile as a source, and 'profile' will still work like normal.
