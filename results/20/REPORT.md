# 20 验证工作包结果

PASS implemented checks; production freeze OPEN

| 案例 | 状态 |
| --- | --- |
| cold | PASS |
| repeated-reset | PASS |
| reset-during-ram | PASS |
| reset-before-timer | PASS |
| fault-ram-data | PASS expected failure detected |
| fault-no-ack | PASS expected failure detected |
| fault-irq-masked | PASS expected failure detected |
| fault-gpio | PASS expected failure detected |
| generic-cold-and-warm | PASS |
| mapped-cold-and-warm | PASS |
| peripheral-random-1 | PASS |
| peripheral-random-7 | PASS |
| peripheral-random-19 | PASS |

纯行覆盖和时钟连接详见coverage-summary.json、clock-domain-audit.json；具体缺项见summary.json。
