# Spoiler-alert-system
*A spoiler alert system for the [Innovaccer Summer Hacker Camp assignment](https://www.innovaccer.com/media/hackercamp/SDE-Intern-Assignment.pdf)*

This simple Python script allows you to get information about the next latest episode of your favourite TV series via email.

## How to use:

1. First you will need to store the info for your MySQL database in the **`db_login.json`** file.  
   You need to replace `localhost` with your host, `user` with your username and `ubuntu97` with your own password.
   
1. Install all the packages mentioned in the **`requirements.txt`** file using pip.

1. Next, you will need to populate the database by running  
   **`python3 spoiler_alert.py --update`**  
   Enter the email addresses along with the corresponding list of TV series. When you are done press **`Enter`** twice.
   
1. Finally, in order to send email alerts to the above entered email-id's, run the script using `--alert` option like this  
   **`python3 spoiler_alert.py --alert`**
   This will ask you to login to the email-id that will be used to send the emails. So, enter your email address and password (make sure that you allow [less secure apps on your email](https://myaccount.google.com/lesssecureapps?pli=1) otherwise Python won't be able to login to your email account.
   
*__That's it!__* 

All the recepients will now receive an email telling them about the air date of the next episode of their favourite TV series.
