import os
import time
from datetime import datetime
from api_client import OutlineAPIClient, APIError

def save_file(data: bytes, backup_dir: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.zip"
    output_path = os.path.join(backup_dir, filename)

    os.makedirs(backup_dir, exist_ok=True)

    with open(output_path, 'wb') as file:
        file.write(data)
    print(f"File saved successfully to: {output_path}")
    return output_path


def process_export(client: OutlineAPIClient, backup_dir: str) -> str:
    response = client.request_export()
    file_operation = response["data"]["fileOperation"]
    file_operation_id = file_operation['id']
    current_state = file_operation['state']

    print(f"Export job created with ID: {file_operation_id}")
    print(f"Initial state: {current_state}")

    if current_state == "complete":
        print("Export is already complete. Downloading immediately.")
        file_data = client.download_file(file_operation_id)
        return save_file(file_data, backup_dir)

    while True:
        time.sleep(0.3)  # 300ms delay

        status_response = client.check_export_status(file_operation_id)
        current_state = status_response["data"]["state"]

        print(f"Current state: {current_state}")

        if current_state == "complete":
            print("Export completed successfully!")
            file_data = client.download_file(file_operation_id)
            return save_file(file_data, backup_dir)
        elif current_state == "error":
            raise APIError("Export failed on the server side.")

def main():
    host = ""  # hostname
    token = ""  # accessToken included in the cookie
    backup_dir = ""  # file path to save the backup file

    client = OutlineAPIClient(host, token)

    try:
        downloaded_file = process_export(client, backup_dir)
        print(f"Backup saved to: {downloaded_file}")
    except APIError as e:
        print(f"An error occurred: {str(e)}")
        print("Failed to create backup.")

if __name__ == "__main__":
    main()
