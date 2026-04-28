# Carbon Black Health Check 

```
Reece, 

I added the thread below to the chat a couple of weeks ago. 

Screenshot 2026-03-01 at 7.28.44 PM.png

If you can change line 125 of the script to the following;

Before
("agent_config", "/api/bit9platform/restricted/agentConfig?limit=", 0),

After
("agent_config", "/api/bit9platform/v1/agentConfig?limit=", 0),

The script should run successfully afterwards. I have tested on 8.11.4.5 and was able to get it to complete sucessfully. 

I have also added the updated App_Control_Script.zip file to the folder where the SymHealth app is located on the Partner Portal if you would like to download it.

If you still receive errors after making these changes, then please send me a screenshot oif the output so I can correct.
```
