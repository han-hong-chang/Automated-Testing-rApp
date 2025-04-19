import json
import os

# 設定上一層目錄的路徑
file_path = os.path.join(os.getcwd(), '..', 'test-spec.json')

# 讀取 test-spec.json 檔案
with open(file_path, 'r') as file:
    data = json.load(file)

# 提取 expectationTargets 資料
expectation_targets = data.get("testSpecifications", [])[0].get("expectationTargets", [])

# 儲存結果
results = []
for target in expectation_targets:
    result = {
        "targetName": target.get("targetName"),
        "targetCondition": target.get("targetCondition"),
        "targetValueRange": target.get("targetValueRange"),
        "targetUnit": target.get("targetUnit"),
        "targetScope": target.get("targetScope")
    }
    results.append(result)

# 印出結果
for result in results:
    print(json.dumps(result, indent=4))


target_names = [target.get("targetName") for target in expectation_targets]



target_name_1 = expectation_targets[0].get("targetName")
target_name_2 = expectation_targets[1].get("targetName")

print("First targetName:", target_name_1)
print("Second targetName:", target_name_2)




target_value_range_1 = expectation_targets[0].get("targetValueRange")
target_value_range_2 = expectation_targets[1].get("targetValueRange")


target_value_range_1_int = int(target_value_range_1[0])
target_value_range_2_int = int(target_value_range_2[0])

print("First targetValueRange as integer:", target_value_range_1_int)
print("Second targetValueRange as integer:", target_value_range_2_int)
