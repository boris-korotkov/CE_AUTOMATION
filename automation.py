import os
import time

def main():
    # Print a greeting
    print("Hello! This is a test script to demonstrate an executable.")
    
    # Get the current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Create a log file
    log_file = os.path.join(cwd, "automation_log.txt")
    
    with open(log_file, "w") as file:
        file.write("=== Automation Test Log ===\n")
        file.write(f"Script started at: {time.ctime()}\n")
        file.write(f"Working directory: {cwd}\n")
        file.write("This script successfully created a log file.\n")
        file.write("Thank you for testing!\n")
        file.write(f"Script ended at: {time.ctime()}\n")
    
    # Notify the user
    print(f"Log file created: {log_file}")

if __name__ == "__main__":
    main()
