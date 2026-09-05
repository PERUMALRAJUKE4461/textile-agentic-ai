from tools.diagnostic_tools import diagnose_machine


result = diagnose_machine("L001")

print("========================================")
print("        TEXTILE MACHINE DIAGNOSIS")
print("========================================")

print(f"Loom ID       : {result['loom_id']}")
print(f"Status        : {result['machine_status']}")
print(f"Fault Type    : {result['fault_type']}")

print("\nDetected Issues:")

if result["issues"]:
    for issue in result["issues"]:
        print(f"  - {issue}")
else:
    print("  No issues detected")

print(f"\nDiagnosis     : {result['diagnosis']}")
