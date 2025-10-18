# Free-Prescription-Software
In this new era prescriptions are no longer hand written. To ensure proper follow up we also need patient database. Due to increased cost of prescription softwares it's sometimes unaffordable or causes medical expenses to rise. So I have developed this software to help my colleagues and doctors all over the world


Features:
1. Patient Database
   <img width="1280" height="719" alt="image" src="https://github.com/user-attachments/assets/b8e4f689-cf93-4a73-90bb-fcfc37f07117" />

2. Easy prescription Tab
<img width="1280" height="719" alt="image" src="https://github.com/user-attachments/assets/fc6243ea-b436-42ee-8699-c6c39f4e3b62" />
<img width="1366" height="768" alt="Screenshot from 2025-10-18 19-46-32" src="https://github.com/user-attachments/assets/0120f92e-dd2b-42f5-945a-d3922183a16f" />


3. Manage Doctor info
   <img width="1280" height="719" alt="image" src="https://github.com/user-attachments/assets/9a8a56cd-7880-423d-852a-78a04e361dbb" />


4. Drug database
   <img width="1366" height="768" alt="Screenshot from 2025-10-18 19-47-27" src="https://github.com/user-attachments/assets/559ac5a4-88ae-4de4-a3a4-960b830dc68e" />

5. Investigation Database
6. Advise Database






Installation instruction:
User Guide:

Windows 11 only. Also possible in 10 but I lack time for that. If i get time and huge response I may do.
Also runs on linux. Install necessary dependencies. (I don't feel need to mention. Linux users would figure it out by their own. THEY ARE SMART.)
!!!!!!!Internet connection needed during installation!!!!!!

Step 1: Install python 3.13 from Microsoft store
https://apps.microsoft.com/detail/9PNRBTZXMB4Z?hl=en-us&gl=BD&ocid=pdpshare

Step 2: Install GTK runtime from here
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
(exe file)

Step 3: Open Terminal (admin) 

Step 4: Copy and paste this command
{Paste every line, press enter and wait until finished)

python -m pip install --upgrade pip


pip install PyQt5 requests beautifulsoup4


pip install weasyprint


pip install cairocffi cairosvg tinycss2 cssselect2 pyphen pillow


Step 5: Paste every line. Press enter button and wait to see OK. If you get OK in 3 you're ready.


python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"


python -c "import requests, bs4; print('Requests and BeautifulSoup OK')"


python -c "from weasyprint import HTML; print('WeasyPrint OK')"


Step 6: Final one. Extract the zip file on your PC. 

Step 7: Running the software. (Don't worry you will get used to it.)
Get inside the extracted file and right click on an empty place. 
you will see an option Open in Terminal.

type
python3 main.py

You're good to go.

Every time you want to open the software you will do this STEP 7.


For any help or suggesting new features let me know in the comments
