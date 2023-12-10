
# Onedrive downloader for Python
## Install Dependencies
[Microsoft Python Tutorial](https://learn.microsoft.com/en-us/graph/tutorials/python?tabs=aad&tutorial-step=2)   
   
Install python libraries for MS Graph SDK    
```bash
python3 -m pip install azure-identity
python3 -m pip install msgraph-sdk
```
It could take long time because modules have large size.   
   
## Configure Secrets   
To use OneDrive API, need client id, tenant id, graphScope.      

### Register the App
[Azure Active Directory admin Portal](https://aad.portal.azure.com/)   
[Microsoft Tutorial - Register the App in the portal](https://learn.microsoft.com/en-us/graph/tutorials/python?tabs=aad&tutorial-step=1)   

### Set config.cfg
If you complete the registration, you have client id, tenant id.
Create a file in the same directory as main.py named config.cfg and add the following code.
```
[azure]
clientId = YOUR_CLIENT_ID_HERE
tenantId = common
graphUserScopes = User.Read Mail.Read Mail.Send
```   
   
Then, set your prefer directory for download files   
```
[download]
destDir = ./
```




### 참조 문서   
[msal caching into file. (Microsoft)](https://learn.microsoft.com/en-us/python/api/msal/msal.token_cache.serializabletokencache?view=msal-py-latest)  

