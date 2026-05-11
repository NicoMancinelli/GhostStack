import paramiko
import sys
import logging

# GhostStack: Robotic Exploitation - Default Credential Auditor
#
# Attempts to authenticate via SSH using known default credentials for
# common robotic and autonomous platforms.

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Default credentials based on research (Unitree, DJI, Raspberry Pi, etc.)
DEFAULT_CREDS = [
    ('root', '12345678'),  # Unitree Go2 / Go1
    ('unitree', 'unitree'),
    ('pi', 'raspberry'),
    ('ubuntu', 'ubuntu'),
    ('admin', 'admin'),
    ('dji', 'dji'),
]

def audit_credentials(target_ip, port=22):
    print(f"[*] Auditing SSH credentials for {target_ip}:{port}...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for user, pwd in DEFAULT_CREDS:
        try:
            print(f"    - Attempting {user}:{pwd}...")
            client.connect(target_ip, port=port, username=user, password=pwd, timeout=3)
            print(f"\n[!] VULNERABILITY FOUND: SSH access granted with {user}:{pwd}")
            
            # Run a quick info command
            stdin, stdout, stderr = client.exec_command('uname -a; uptime')
            print(f"    System Info: {stdout.read().decode().strip()}")
            
            client.close()
            return (user, pwd)
        except paramiko.AuthenticationException:
            continue
        except Exception as e:
            print(f"    [-] Connection Error: {e}")
            break
            
    print("\n[-] No default credentials matched.")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 robot_credential_audit.py <target_ip>")
        sys.exit(1)
    
    audit_credentials(sys.argv[1])
