### Contributing
These are instructions for setting up RetroArcher.X with a development virtual environment (separated from your main 
python install). The code below will setup the venv and run retroarcher.


* Install Python 3.9
* Download and extract the source code to the directory of your choice.
* Open terminal/command prompt
* Windows:
  ```batch
  cd <RetroArcher.X directory>
  python -m venv venv
  call venv\Scripts\activate.bat
  pip install --upgrade -r requirements.txt
  python retroarcher.py
  deactivate
  ```
* Linux/Mac:
  ```bash
  cd <RetroArcher.X directory>
  python -m venv venv
  source venv/bin/activate
  pip install --upgrade -r requirements.txt
  python retroarcher.py
  deactivate
  ```
