# DFT实验实际故障检测矩阵

| 故障 | 正常IO检测 | 扫描检测 |
| --- | --- | --- |
| q[0] stuck-0 | True | True |
| q[0] stuck-1 | True | True |
| q[1] stuck-0 | False | True |
| q[1] stuck-1 | False | True |
| q[2] stuck-0 | False | True |
| q[2] stuck-1 | False | True |
| q[3] stuck-0 | False | True |
| q[3] stuck-1 | False | True |

| RAM故障 | March检测 | 读不匹配数 |
| --- | --- | --- |
| data[0] stuck-0 | True | 32 |
| data[0] stuck-1 | True | 48 |
| data[1] stuck-0 | True | 32 |
| data[1] stuck-1 | True | 48 |
| data[2] stuck-0 | True | 32 |
| data[2] stuck-1 | True | 48 |
| data[3] stuck-0 | True | 32 |
| data[3] stuck-1 | True | 48 |
| address[0] forced-0 alias | True | 32 |
| address[1] forced-0 alias | True | 32 |
| address[2] forced-0 alias | True | 32 |
| address[3] forced-0 alias | True | 32 |
