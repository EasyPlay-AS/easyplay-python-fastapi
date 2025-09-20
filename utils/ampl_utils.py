import os
from amplpy import modules


def activate_ampl_license():
    """Activate AMPL license using environment variable"""
    license_uuid = os.getenv("AMPL_LICENSE_UUID")
    if license_uuid:
        try:
            modules.activate(license_uuid)
            print(f"AMPL license activated successfully: {license_uuid}")
        except Exception as e:
            print(f"Failed to activate AMPL license: {e}")
    else:
        print("No AMPL_LICENSE_UUID found in environment variables")
