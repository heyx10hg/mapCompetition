import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import s03_clean_classify as s03


class ClassificationRuleTests(unittest.TestCase):
    def test_claypot_rice_is_local_traditional_signal(self):
        self.assertEqual(s03.classify("老广州煲仔饭"), "traditional")
        self.assertEqual(s03.classify("滑鸡煲仔饭"), "traditional")

    def test_generic_roast_chicken_defaults_modern(self):
        self.assertEqual(s03.classify("炭火烧鸡"), "modern")
        self.assertEqual(s03.classify("招牌烧鸡"), "modern")

    def test_local_context_keeps_roast_chicken_traditional(self):
        self.assertEqual(s03.classify("客家烧鸡"), "traditional")
        self.assertEqual(s03.classify("荔枝木烧鸡"), "traditional")
        self.assertEqual(s03.classify("窑鸡"), "traditional")

    def test_fast_food_chicken_signals_are_modern(self):
        self.assertEqual(s03.classify("麦当劳|麦辣鸡腿堡"), "modern")
        self.assertEqual(s03.classify("广州麦当劳|板烧鸡腿堡"), "modern")
        self.assertEqual(s03.classify("广州赛百味|日式照烧鸡三明治"), "modern")
        self.assertEqual(s03.classify("汉堡王|鸡块"), "modern")
        self.assertEqual(s03.classify("华莱士全鸡汉堡"), "modern")

    def test_pizza_chicken_signals_are_modern(self):
        self.assertEqual(s03.classify("尊宝比萨|奥尔良烤鸡"), "modern")
        self.assertEqual(s03.classify("达美乐比萨|黑松露风味菌菇鸡肉比萨"), "modern")

    def test_other_boundary_rules(self):
        self.assertEqual(s03.classify("竹筒饭"), "modern")
        self.assertEqual(s03.classify("从化农家菜烧鸡竹筒饭"), "modern")
        self.assertEqual(s03.classify("卤鸡腿"), "modern")
        self.assertEqual(s03.classify("火锅|鸡肉"), "other_chicken")

    def test_clean_uses_original_name_context_before_parentheses_are_removed(self):
        records = [{
            "id": "B-test",
            "name": "自力农庄(农家乐.农家小炒.粤菜 走地鸡.瘦身鲩鱼)",
            "adname": "从化区",
            "typecode": "050000",
            "type": "餐饮服务;餐饮相关场所;餐饮相关",
            "address": "溪头村三194号",
            "location": "113.870020,23.713166",
            "tag": [],
        }]

        rows, _stats = s03.clean(records, keep_gcj02=True, districts=s03.GUANGZHOU_DISTRICTS)

        self.assertEqual(rows[0]["label"], "traditional")
        self.assertEqual(rows[0]["match_source"], "招牌")


if __name__ == "__main__":
    unittest.main()
