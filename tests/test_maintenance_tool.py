from tools.maintenance_tools import get_maintenance_history


result = get_maintenance_history("L001")

print("========================================")
print("       MAINTENANCE HISTORY")
print("========================================")

if result["success"]:
    print(f"Loom ID      : {result['loom_id']}")
    print(f"Records found: {result['record_count']}")

    print("\nPrevious Maintenance Events:")

    for record in result["records"]:
        print("\n----------------------------------------")
        print(f"Date       : {record['date']}")
        print(f"Issue      : {record['issue']}")
        print(f"Action     : {record['action_taken']}")
        print(f"Technician : {record['technician']}")
        print(f"Downtime   : {record['downtime_hours']} hours")
else:
    print(result["message"])