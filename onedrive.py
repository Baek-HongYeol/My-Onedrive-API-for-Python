import asyncio
import configparser
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from graph import Graph
from msgraph.generated.models.drive import Drive
from azure.core.exceptions import ClientAuthenticationError
import json
import requests
import os, sys
from urllib import parse
import logging



def input_path(msg):
    path = input(msg)
    if len(path)>0 and path[0] == '/':
        path = path[1:]
    if len(path)>0 and path[-1] == '/':
        path = path[:-1]
    return path

async def main():
    global config, destDir
    config = configparser.ConfigParser()
    config.read(['config.cfg', 'config.dev.cfg'])
    azure_settings = config['azure']
    
    logging.basicConfig(filename='onedrive.log', format='"time": "%(asctime)s", \n"msg": "%(message)s"', filemode='a', level=logging.INFO)

    graph: Graph = Graph(azure_settings)

    destDir = config['download']['destDir']

    choice = -1

    while choice != 0:
        print('\nPlease choose one of the following options:')
        print('0. Exit')
        print('1. Display access token')
        print('2. List OneDrive Dirs')
        print('3. Download directory')
        print('4. Download file')
        print('5. Get File Info')

        try:
            choice = int(input('>> '))
        except ValueError:
            choice = -1

        try:
            if choice == 0:
                print('Goodbye...')
            elif choice == 1:
                await display_access_token(graph)
            elif choice == 2:
                await list_directory(graph)
            elif choice == 3:
                await download_directory(graph)
            elif choice == 4:
                await download_file(graph)
            elif choice == 5:
                await get_fileInfo(graph)
            else:
                print('Invalid choice!\n')
        except ODataError as odata_error:
            print('Error:')
            if odata_error.error:
                print(odata_error.error.code, odata_error.error.message)
        except FileNotFoundError:
            print("Requested Resource does not exist.")
        except ClientAuthenticationError as e:
            print(e.message)
        except Exception as e:
            print(e)



async def display_access_token(graph: Graph):
    token = await graph.get_user_token()
    print('User token:', token, '\n')

async def list_directory(graph: Graph):
    path = input_path('type the target directory path: ')
    encoded_path = parse.quote(path) + ':/children'
    items = await graph.make_graph_call(encoded_path, "?select=id,name")
    if len(items)>0:
        print("Items in", path, ": ")
    else:
        print("No Item in", path)
    for entries in range(len(items)):
        print('\t', items[entries]['name'])
    

async def get_fileInfo(graph: Graph, path=None):
    if path is None:
        path = input_path("type the target file path: ")
    encoded_path = parse.quote(path)

    print("try to get the file information...")
    items = await graph.make_graph_call(encoded_path, "?select=id,name,@microsoft.graph.downloadUrl,file,size")
    filtered = [item for item in items if 'file' in item]
    if len(filtered)==0:
        print("No Files in", path)
        return
    for k, v in items.items():
        print(k, " : ", v)

async def download_directory(graph: Graph):
    path = input_path('type the target directory path: ')
    encoded_path = parse.quote(path)

    items = await graph.make_graph_call(encoded_path+":/children", "?select=id,name,@microsoft.graph.downloadUrl,file,size")
    filtered = [item for item in items['value'] if 'file' in item]
    if len(filtered)>0:
        print("Files in", path, ":", len(filtered))
    else:
        print("No Files in", path)
    for entries in range(len(filtered)):
        item = filtered[entries]
        await download(item['@microsoft.graph.downloadUrl'], item['name'])
        with open(destDir + item['name'], 'rb') as f:
            f.seek(0, os.SEEK_END)
            if f.tell == item['size']:
                logging.info(f"{item['name']} saved! try to delete...")
            else:
                logging.info(f"{item['name']} not completed!")
                return

async def download_file(graph:Graph, path = None):
    if not path:
        path = input_path('type the target file path: ')
    encoded_path = parse.quote(path)

    print("try to get the file information...")
    items = await graph.make_graph_call(encoded_path, "?select=id,name,@microsoft.graph.downloadUrl,file,size")
    filtered = [item for item in items if 'file' in item]
    if len(filtered)==0:
        print("No Files in", path)
        return
    await download(graph, items['@microsoft.graph.downloadUrl'], items['name'])
    with open(destDir + items['name'], 'rb') as f:
        f.seek(0, os.SEEK_END)
        if f.tell == items['size']:
            logging.info(f"{items['name']} saved! try to delete...")
        else:
            logging.info(f"{items['name']} not completed!")
            return

    delete_file(graph, items['id'])

async def download(graph: Graph, download_url, filename):
    HEADERS = {'Authorization': 'Bearer ' + await graph.get_user_token()}
    chunk_size = 4096
    print('download Start -', filename)
    if not os.path.exists(destDir):
        os.mkdir(destDir)
    elif os.path.exists(destDir+filename):
        logging.info(destDir+filename+" already Exists. Download canceled")
        raise FileExistsError(destDir+filename)
    with requests.get(download_url, stream=True, headers=HEADERS) as r:
        with open(destDir+filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size): 
                if chunk:
                    f.write(chunk)
            

async def delete_file(graph: Graph, id, file_path = None):

    await graph.user_client.me.drive.items.by_drive_item_id('driveItem-id').delete()

#graphClient = GetAuthenticatedGraphClient(...)
# get user's files and folders in the root
#oneDriveRoot = graphClient.Me.Drive.Root.Children.Request().GetAsync().Result
# display the results
#for driveItem in results:
#  Console.WriteLine(driveItem.Id + ": " + driveItem.Name);

if __name__ == '__main__':
    asyncio.run(main())