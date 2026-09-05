from tools.machine_tools import get_machine_status


result = get_machine_status("L001")

print("========================================")
print("       TEXTILE MACHINE STATUS")
print("========================================")

if result["success"]:
    for key, value in result.items():
        if key != "success":
            print(f"{key:20}: {value}")
else:
    print(result["message"])