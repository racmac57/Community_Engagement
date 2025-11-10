
import time
import sys
sys.path.append(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment")
from deploy_production import ProductionDeployer

deployer = ProductionDeployer()
while True:
    try:
        deployer.health_check()
        time.sleep(3600)
    except KeyboardInterrupt:
        break
    except Exception as e:
        deployer.send_alert(f"Monitoring error: {e}", "ERROR")
        time.sleep(300)  # Wait 5 minutes on error
