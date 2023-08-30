## Workflow Logic

The `mode` variable in the `config` file controls the logic between functions.

1. Function `verify_on_galxe` (Requests + Selenium):
    1. Logs into the Galxe website.
    2. Creates a username with a random nickname.
    3. Requests the GID of this user from Galxe.
    4. Posts a tweet for verification on Galxe using Selenium.
    5. Links the Twitter account to Galxe.

2. Function `complete_social_tasks` (Requests):
   1. Completes all social tasks specified in the config - currently, Polyhedra tasks are there (can be changed to other projects, you just need to find the credential ID of the task).
   ![img.png](img.png)
   2. Works asynchronously; you can specify the number of threads (`wallets_in_batch`) in the config file.

3. Function `claim_points` (Requests):
   1. Works asynchronously and claims tasks specified in data/tasks_for_claim.
   2. Any failed claims will be recorded in the table.
   3. **Private keys are not required here - only addresses in the keys.txt file**.

## How to Run
1. Install Python 3.10.
2. Open a terminal, navigate to the folder with the files, and execute the command "pip install -r requirements.txt".
3. Open the file "data/config.py" with any text editor and adjust the randomization settings. Explanations for the settings are provided in comments within the file.
4. Open the file "data/profile_ids.py" with any text editor and input your profiles (1 profile per line).
5. Open the file "data/twitter_handles.txt" and input your Twitter usernames, matching the accounts listed in "data/profile_ids.py".
6. Open the "data/proxies" file and input proxies in the format user:pass@ip:port (without http).
7. Open the "data/keys" file and input private keys of accounts you want to link to Galxe.
8. Open the "data/tasks_for_claim" file and input links for claiming tasks.
9. In the terminal, navigate to the project folder and execute the command "python3 main.py" then press ENTER.

## Change 'W' Value to your own
**You need to change the value to your own in the "data/config" file (instructions below)**
![image](https://user-images.githubusercontent.com/117441696/210056890-bc69281a-a7aa-4681-9722-4d65fd07c957.png)
