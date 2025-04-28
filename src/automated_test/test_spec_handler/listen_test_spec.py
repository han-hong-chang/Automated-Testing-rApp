import subprocess

def listen_test_spec_from_tme():
    """Continuously monitor journalctl logs and print upon receiving a new message, then exit."""
    try:
        # Use subprocess to start journalctl and continuously monitor logs
        command = ['sudo', 'journalctl', '-u', 'flask_api.service', '-n', '0', '-f']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while True:
            # Read each line of journalctl output
            line = process.stdout.readline()
            if line:

                # If the new log contains "POST", return a message and exit the program
                if "POST" in line:
                    print("Test specification notification from TME...")
                    return "New message received"  # Return the message when a POST is found
                    break  # Exit the program after returning the message
        process.stdout.close()
        process.wait()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error: {e}"  # Return the error message if an exception occurs
