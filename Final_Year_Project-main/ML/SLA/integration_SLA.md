# NFS Setup and Machine Learning Integration Guide

This guide outlines the steps to configure an NFS server on `vboxuser` (IP: `10.10.80.73`) and an NFS client on `charlie` (IP: `10.10.80.68`) for sharing Wazuh logs, integrating with a machine learning model, and visualizing results in Kibana. Each command is presented individually in its own code block for clarity.

### Network & Software
- Both systems must be on the same network or routable.
- **Ports:** Allow `2049`, `111`, and dynamic NFS ports.
- **Packages:**
  - Server (`vboxuser`): `nfs-kernel-server`
  - Client (`charlie`): `nfs-common`
  - Python 3.13, `pandas`, `scikit-learn`, `elasticsearch` (in a virtual environment)

## 3. NFS Setup on Wazuh Server (`vboxuser`, `10.10.80.73`)

### 3.1 Install NFS Server
Update package lists:
```bash
sudo apt-get update
```
Install NFS server:
```bash
sudo apt-get install nfs-kernel-server
```

### 3.2 Configure NFS Exports
Edit exports file:
```bash
sudo nano /etc/exports
```
Add to `/etc/exports`:
```
/var/ossec/logs/archives 10.10.80.0/24(rw,sync,no_subtree_check)
```

### 3.3 Set Permissions
Change ownership of archives.json:
```bash
sudo chown nobody:nogroup /var/ossec/logs/archives/archives.json
```
Set permissions for archives.json:
```bash
sudo chmod 664 /var/ossec/logs/archives/archives.json
```
Verify permissions:
```bash
ls -l /var/ossec/logs/archives/archives.json
```

### 3.4 Start NFS Service
Export NFS shares:
```bash
sudo exportfs -a
```
Restart NFS service:
```bash
sudo systemctl restart nfs-kernel-server
```
Enable NFS service on boot:
```bash
sudo systemctl enable nfs-kernel-server
```
Verify exports:
```bash
exportfs -v
```

### 3.5 Configure Firewall
Allow NFS port 2049:
```bash
sudo ufw allow from 10.10.80.0/24 to any port 2049
```
Allow NFS port 111:
```bash
sudo ufw allow from 10.10.80.0/24 to any port 111
```
Check firewall status:
```bash
sudo ufw status
```

## 4. NFS Setup on Client (`charlie`, `10.10.80.68`)

### 4.1 Install NFS Client
Update package lists:
```bash
sudo apt-get update
```
Install NFS client:
```bash
sudo apt-get install nfs-common
```

### 4.2 Create Mount Point
Create mount directory:
```bash
sudo mkdir -p /mnt/wazuh_logs
```
Set ownership of mount point:
```bash
sudo chown vboxuser:vboxuser /mnt/wazuh_logs
```
Set permissions for mount point:
```bash
sudo chmod 755 /mnt/wazuh_logs
```

### 4.3 Mount NFS Share
Test NFS mount:
```bash
sudo mount -t nfs 10.10.80.73:/var/ossec/logs/archives /mnt/wazuh_logs
```
Verify mount:
```bash
mount | grep /mnt/wazuh_logs
```
Check mounted file:
```bash
ls -l /mnt/wazuh_logs/archives.json
```
Edit fstab for persistent mount:
```bash
sudo nano /etc/fstab
```
Add to `/etc/fstab`:
```
10.10.80.73:/var/ossec/logs/archives /mnt/wazuh_logs nfs rw,sync,hard,intr 0 0
```
Unmount for testing:
```bash
sudo umount /mnt/wazuh_logs
```
Mount all fstab entries:
```bash
sudo mount -a
```
Verify persistent mount:
```bash
mount | grep /mnt/wazuh_logs
```

### 4.4 Verify Access as `vboxuser`
Switch to vboxuser:
```bash
su - vboxuser
```
Read first two lines of mounted file:
```bash
cat /mnt/wazuh_logs/archives.json | head -n 2
```

## 5. Model Integration with NFS-Mounted Logs

### 5.1 Check `process_logs.py` Paths
Check log_file path in script:
```bash
grep "log_file" /home/vboxuser/ml_model/scripts/process_logs.py
```
Check joblib.load path in script:
```bash
grep "joblib.load" /home/vboxuser/ml_model/scripts/process_logs.py
```

### 5.2 Test the Script
Switch to vboxuser:
```bash
su - vboxuser
```
Activate virtual environment:
```bash
source /home/vboxuser/ml_model/env/bin/activate
```
Change to scripts directory:
```bash
cd /home/vboxuser/ml_model/scripts
```
Run the script:
```bash
python3 process_logs.py
```
Check process logs:
```bash
tail -n 20 /home/vboxuser/ml_model/logs/process_logs.log
```
Check detected anomalies:
```bash
cat /home/vboxuser/ml_model/logs/detected_anomalies.json
```

### 5.3 Generate Test Logs
SSH to server:
```bash
ssh wazuh@10.10.80.73
```
Verify specific rule in logs:
```bash
tail -n 10 /var/ossec/logs/archives/archives.json | grep '"rule":{".*id":"5715"'
```

## 6. Security Considerations
- Restrict NFS to specific IPs in `/etc/exports`.
- Use Kerberos (`sec=krb5`) for production environments.
- Secure Elasticsearch with SSL.
- Limit permissions for `/mnt/wazuh_logs` and `/home/vboxuser/ml_model`.

## 7. Verification Commands

### On Server (`vboxuser`)
Verify exports:
```bash
exportfs -v
```
Check file permissions:
```bash
ls -l /var/ossec/logs/archives/archives.json
```
Check NFS service status:
```bash
systemctl status nfs-kernel-server
```

### On Client (`charlie`)
Verify mount:
```bash
mount | grep /mnt/wazuh_logs
```
Check mounted file:
```bash
ls -l /mnt/wazuh_logs/archives.json
```
Verify access as vboxuser:
```bash
su - vboxuser -c 'cat /mnt/wazuh_logs/archives.json | head -n 2'
```
Run the ML script:
```bash
python3 /home/vboxuser/ml_model/scripts/process_logs.py
```
Check process logs:
```bash
tail -n 20 /home/vboxuser/ml_model/logs/process_logs.log
```

## 8. Kibana: Creating and Visualizing Index Patterns
1. Open **Wazuh dashboard** → Click ☰ → Go to **Management > Stack Management**.
2. In **Stack Management**, click ☰ → Go to **Kibana > Index Patterns**.
3. Click **Create index pattern**.
4. Enter the **index name** created by the ML model, then click **Create index pattern**.
5. Go to ☰ → **Analytics > Discover**. Select your new index to visualize the data.

## 9. Done!
You’re set up for automated log anomaly detection with Wazuh logs, NFS sharing, ML model integration, and Kibana visualization.
