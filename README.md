Setup Instructions ....

Requirements
1. Install python with versioin 3.6+. You can follow the instructions from this --> () article if you don't know how to do that..

2. Install the required packages fot the bot to run using pip command.
    a. Open a terminal.
    b. Change directory to the folder where you have all the file of the bot using "cd" command.
    c. Now run command "pip install -r requirements.txt" and it should install all the required packages for the bot.

3. Now install mongodb on windows machine. You can follow this link --> (https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/) to do this.

4. Setup google developer account and download the client_secret.json file. You can follow this --> (https://www.youtube.com/watch?v=6bzzpda63H0) video to do this.

5. Put the client_secret file at the location.
    a. Press Windows+R button and it should bring run dialog.
    b. Type %APPDATA% in the run dialog and press enter and it should open a folder.
    c. Create a new folder named gspread in that folder.
    d. Open the gspread folder and paste the client_secret.json file in that folder.

6. Now run the mongodb server. Instructions are here to run (https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/).

7. Now again open the terminal and go to the bot folder where all the file are, And type the command "python main.py" and bot should be up in seconds.

8. Now open the web browser and type 0.0.0.0:8000 in the address bar and it should open the login page for the control panel.

9. Use "admin" and "pass" as the username and password to login...


10. Let me know about any issues during setup...
