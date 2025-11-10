"""
Community Engagement ETL - Production Deployment & Automation
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Windows Server deployment with automated scheduling and monitoring
"""

import json
import smtplib
import subprocess
import shutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Health checks will be limited.")
import time
import xml.etree.ElementTree as ET


class ProductionDeployer:
    """Handles production deployment and automation"""
    
    def __init__(self, config_path: str = 'production_config.json'):
        """Initialize with production configuration"""
        self.config = self.load_production_config(config_path)
        self.performance_thresholds = {
            'max_processing_time': 1800,  # 30 minutes
            'max_memory_usage': 2048,     # 2GB
            'min_disk_space': 5120,       # 5GB
            'max_error_rate': 5           # 5% failure rate
        }
    
    def load_production_config(self, config_path: str) -> Dict[str, Any]:
        """Load production configuration with defaults"""
        default_config = {
            'email': {
                'smtp_server': 'smtp.office365.com',
                'smtp_port': 587,
                'sender_email': 'etl@hackensacknj.gov',
                'sender_password': '',  # Use environment variable
                'recipients': ['it@hackensacknj.gov']
            },
            'power_bi': {
                'workspace_id': '',
                'dataset_id': '',
                'client_id': '',
                'client_secret': ''
            },
            'backup': {
                'retention_months': 6,
                'max_backup_size_gb': 10,
                'backup_location': 'backups'
            },
            'monitoring': {
                'check_interval_hours': 1,
                'log_retention_days': 30
            }
        }
        
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
        else:
            config = default_config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config
    
    def schedule_monthly_processing(self) -> bool:
        """Create Windows Task Scheduler job for monthly processing"""
        try:
            task_name = "CommunityEngagement_ETL_Monthly"
            python_path = shutil.which('python')
            script_path = Path(__file__).parent / 'src' / 'main_processor.py'
            
            # Create Task Scheduler XML
            task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</Date>
    <Author>Community Engagement ETL</Author>
    <Description>Monthly processing of Community Engagement data</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.now().replace(day=1, hour=6, minute=0).strftime('%Y-%m-%dT%H:%M:%S')}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <Months>
          <January/><February/><March/><April/><May/><June/>
          <July/><August/><September/><October/><November/><December/>
        </Months>
        <DaysOfMonth><Day>1</Day></DaysOfMonth>
      </ScheduleByMonth>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>NT AUTHORITY\\SYSTEM</UserId>
      <LogonType>ServiceAccount</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>{script_path}</Arguments>
      <WorkingDirectory>{Path(__file__).parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
            
            # Save XML file
            xml_path = Path('task_schedule.xml')
            with open(xml_path, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # Create task using schtasks command
            cmd = f'schtasks /create /xml "{xml_path}" /tn "{task_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[SUCCESS] Monthly processing task scheduled: {task_name}")
                xml_path.unlink()  # Clean up XML file
                return True
            else:
                print(f"[ERROR] Failed to schedule task: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Task scheduling error: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring with email alerts"""
        try:
            # Create monitoring script
            monitor_script = Path('monitor_etl.py')
            monitor_code = f"""
import time
import sys
sys.path.append(r"{Path(__file__).parent}")
from deploy_production import ProductionDeployer

deployer = ProductionDeployer()
while True:
    try:
        deployer.health_check()
        time.sleep({self.config['monitoring']['check_interval_hours'] * 3600})
    except KeyboardInterrupt:
        break
    except Exception as e:
        deployer.send_alert(f"Monitoring error: {{e}}", "ERROR")
        time.sleep(300)  # Wait 5 minutes on error
"""
            
            with open(monitor_script, 'w') as f:
                f.write(monitor_code)
            
            # Create monitoring service task
            task_name = "CommunityEngagement_ETL_Monitor"
            python_path = shutil.which('python')
            
            cmd = f'schtasks /create /tn "{task_name}" /tr "{python_path} {monitor_script}" /sc onstart /ru SYSTEM'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] Monitoring service configured")
                return True
            else:
                print(f"[ERROR] Monitoring setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Monitoring setup error: {e}")
            return False
    
    def manage_backups(self) -> bool:
        """Automated backup retention and cleanup"""
        try:
            backup_dir = Path(self.config['backup']['backup_location'])
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Calculate retention cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.config['backup']['retention_months'] * 30)
            
            # Clean old backups
            cleaned_count = 0
            total_size = 0
            
            for backup_file in backup_dir.glob('*'):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    file_size = backup_file.stat().st_size / (1024**3)  # GB
                    total_size += file_size
                    
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        cleaned_count += 1
            
            # Check total backup size
            max_size_gb = self.config['backup']['max_backup_size_gb']
            if total_size > max_size_gb:
                self.send_alert(f"Backup size exceeded: {total_size:.1f}GB > {max_size_gb}GB", "WARNING")
            
            print(f"[SUCCESS] Backup cleanup: removed {cleaned_count} old files, total size: {total_size:.1f}GB")
            return True
            
        except Exception as e:
            print(f"[ERROR] Backup management error: {e}")
            self.send_alert(f"Backup management failed: {e}", "ERROR")
            return False
    
    def power_bi_integration(self) -> bool:
        """Trigger Power BI dataset refresh after processing"""
        try:
            if not all([self.config['power_bi']['workspace_id'], 
                       self.config['power_bi']['dataset_id'],
                       self.config['power_bi']['client_id']]):
                print("WARNING Power BI configuration incomplete, skipping refresh")
                return True
            
            # Get access token (simplified - production should use proper OAuth flow)
            token_url = "https://login.microsoftonline.com/common/oauth2/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.config['power_bi']['client_id'],
                'client_secret': self.config['power_bi']['client_secret'],
                'resource': 'https://analysis.windows.net/powerbi/api'
            }
            
            token_response = requests.post(token_url, data=token_data, timeout=30)
            if token_response.status_code != 200:
                raise Exception(f"Token request failed: {token_response.status_code}")
            
            access_token = token_response.json()['access_token']
            
            # Trigger dataset refresh
            refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.config['power_bi']['workspace_id']}/datasets/{self.config['power_bi']['dataset_id']}/refreshes"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            refresh_response = requests.post(refresh_url, headers=headers, json={}, timeout=30)
            
            if refresh_response.status_code == 202:
                print("[SUCCESS] Power BI dataset refresh triggered")
                return True
            else:
                raise Exception(f"Refresh failed: {refresh_response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Power BI integration error: {e}")
            self.send_alert(f"Power BI refresh failed: {e}", "WARNING")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """System validation and performance monitoring"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'HEALTHY',
            'checks': {},
            'alerts': []
        }
        
        try:
            # Check disk space (if psutil available)
            if PSUTIL_AVAILABLE:
                disk_usage = psutil.disk_usage('.')
                free_gb = disk_usage.free / (1024**3)
                health_status['checks']['disk_space_gb'] = round(free_gb, 1)
                
                if free_gb < self.performance_thresholds['min_disk_space'] / 1024:
                    health_status['status'] = 'WARNING'
                    health_status['alerts'].append(f"Low disk space: {free_gb:.1f}GB")
                
                # Check memory usage
                memory = psutil.virtual_memory()
                memory_usage_mb = (memory.total - memory.available) / (1024**2)
                health_status['checks']['memory_usage_mb'] = round(memory_usage_mb, 1)
                
                if memory_usage_mb > self.performance_thresholds['max_memory_usage']:
                    health_status['status'] = 'WARNING'
                    health_status['alerts'].append(f"High memory usage: {memory_usage_mb:.1f}MB")
            else:
                health_status['checks']['psutil_status'] = 'not_available'
            
            # Check log files for recent errors
            log_dir = Path('logs')
            if log_dir.exists():
                recent_logs = [f for f in log_dir.glob('*.log') 
                              if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 1]
                
                error_count = 0
                for log_file in recent_logs:
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read()
                            error_count += content.count('ERROR')
                    except:
                        pass
                
                health_status['checks']['recent_errors'] = error_count
                
                if error_count > 10:  # More than 10 errors in 24 hours
                    health_status['status'] = 'WARNING'
                    health_status['alerts'].append(f"High error count: {error_count} in 24 hours")
            
            # Send alerts if needed
            if health_status['alerts']:
                alert_message = "Health check alerts:\n" + "\n".join(health_status['alerts'])
                self.send_alert(alert_message, health_status['status'])
            
        except Exception as e:
            health_status['status'] = 'ERROR'
            health_status['alerts'].append(f"Health check failed: {e}")
        
        return health_status
    
    def send_alert(self, message: str, severity: str = "INFO"):
        """Send email notification"""
        try:
            if not self.config['email']['sender_password']:
                print(f"Email not configured: {severity} - {message}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['sender_email']
            msg['To'] = ', '.join(self.config['email']['recipients'])
            msg['Subject'] = f"Community Engagement ETL {severity}: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            body = f"""
Community Engagement ETL Alert

Severity: {severity}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

Message:
{message}

System: {Path(__file__).parent}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['sender_email'], self.config['email']['sender_password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def deploy_production(self) -> bool:
        """Complete production deployment"""
        print("=== Community Engagement ETL Production Deployment ===\n")
        
        success_count = 0
        total_tasks = 5
        
        # Schedule monthly processing
        if self.schedule_monthly_processing():
            success_count += 1
        
        # Setup monitoring
        if self.setup_monitoring():
            success_count += 1
        
        # Configure backup management
        if self.manage_backups():
            success_count += 1
        
        # Test Power BI integration
        if self.power_bi_integration():
            success_count += 1
        
        # Run health check
        health_results = self.health_check()
        if health_results['status'] != 'ERROR':
            success_count += 1
        
        deployment_success = success_count >= 4  # Allow one failure
        
        print(f"\n=== Deployment Summary ===")
        print(f"Tasks completed: {success_count}/{total_tasks}")
        print(f"Status: {'SUCCESS' if deployment_success else 'FAILED'}")
        
        # Send deployment notification
        self.send_alert(
            f"Production deployment {'completed' if deployment_success else 'failed'}: {success_count}/{total_tasks} tasks successful",
            "INFO" if deployment_success else "ERROR"
        )
        
        return deployment_success


if __name__ == "__main__":
    deployer = ProductionDeployer()
    deployer.deploy_production()