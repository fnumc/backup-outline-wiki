import http.client
import json
import time
import os
from datetime import datetime
import urllib.parse

class APIError(Exception):
    pass

def request_export(host, token, format="outline-markdown"):
    conn = http.client.HTTPSConnection(host)
    
    payload = json.dumps({"format": format})
    
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {token}"
    }
    
    conn.request("POST", "/api/collections.export_all", payload, headers)
    
    res = conn.getresponse()
    
    if res.status != 200:
        raise APIError(f"Export request failed. Status code: {res.status}, Response: {res.read().decode('utf-8')}")
    
    data = res.read()
    return json.loads(data.decode("utf-8"))

def check_export_status(host, token, file_operation_id):
    conn = http.client.HTTPSConnection(host)
    
    payload = json.dumps({"id": file_operation_id})
    
    headers = {
        'Content-Type': "application/json",
        'Authorization': f"Bearer {token}"
    }
    
    conn.request("POST", "/api/fileOperations.info", payload, headers)
    
    res = conn.getresponse()
    
    if res.status != 200:
        raise APIError(f"Status check failed. Status code: {res.status}, Response: {res.read().decode('utf-8')}")
    
    data = res.read()
    return json.loads(data.decode("utf-8"))

def save_file(data, backup_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.zip"
    output_path = os.path.join(backup_dir, filename)
    
    os.makedirs(backup_dir, exist_ok=True)
    
    with open(output_path, 'wb') as file:
        file.write(data)
    print(f"File saved successfully to: {output_path}")
    return output_path

def download_file(host, token, file_operation_id, backup_dir):
    conn = http.client.HTTPSConnection(host)
    
    headers = {
        'Authorization': f"Bearer {token}"
    }
    
    conn.request("GET", f"/api/fileOperations.redirect?id={file_operation_id}", headers=headers)
    
    res = conn.getresponse()
    
    if res.status == 302:
        location = res.getheader('Location')
        if location:
            parsed_url = urllib.parse.urlparse(location)
            new_host = parsed_url.netloc
            new_path = parsed_url.path + '?' + parsed_url.query
            
            new_conn = http.client.HTTPSConnection(new_host)
            new_conn.request("GET", new_path, headers=headers)
            
            file_res = new_conn.getresponse()
            
            if file_res.status == 200:
                data = file_res.read()
                return save_file(data, backup_dir)
            else:
                raise APIError(f"File download failed. Status code: {file_res.status}, Response: {file_res.read().decode('utf-8')}")
        else:
            raise APIError("Redirect location not found in headers")
    else:
        raise APIError(f"Expected 302 redirect, got {res.status}. Response: {res.read().decode('utf-8')}")

def process_export(host, token, backup_dir):
    try:
        # Request export
        response = request_export(host, token)
        file_operation = response["data"]["fileOperation"]
        file_operation_id = file_operation['id']
        current_state = file_operation['state']
        
        print(f"Export job created with ID: {file_operation_id}")
        print(f"Initial state: {current_state}")
        
        if current_state == "complete":
            print("Export is already complete. Downloading immediately.")
            return download_file(host, token, file_operation_id, backup_dir)
        
        # Check status every 300ms
        while True:
            time.sleep(0.3)  # 300ms delay
            
            status_response = check_export_status(host, token, file_operation_id)
            current_state = status_response["data"]["state"]
            
            print(f"Current state: {current_state}")
            
            if current_state == "complete":
                print("Export completed successfully!")
                return download_file(host, token, file_operation_id, backup_dir)
            elif current_state == "error":
                raise APIError("Export failed on the server side.")
    
    except APIError as e:
        print(f"An error occurred: {str(e)}")
        return None

def main():
    # Enter your secret here
    host = "" #hostname
    token = "" # accessToken included in the cookie
    backup_dir = "" # file path to save the backup file

    downloaded_file = process_export(host, token, backup_dir)
    if downloaded_file:
        print(f"Backup saved to: {downloaded_file}")
    else:
        print("Failed to create backup.")

if __name__ == "__main__":
    main()
