# 13B 边界扫描实验

PASS：SAMPLE、预装载、EXTEST、逐位激励、故障读回与释放。

|场景|输出|采样|与正常值异或|
|---|---|---|---|
|sample-functional|—|170|—|
|preload-then-extest|—|1|—|
|healthy|1|1|0|
|healthy|2|2|0|
|healthy|4|4|0|
|healthy|8|8|0|
|healthy|15|15|0|
|healthy|0|0|0|
|stuck-low-bit1|1|1|0|
|stuck-low-bit1|2|0|2|
|stuck-low-bit1|4|4|0|
|stuck-low-bit1|8|8|0|
|stuck-low-bit1|15|13|2|
|stuck-low-bit1|0|0|0|
|wired-or-short-bits01|1|3|2|
|wired-or-short-bits01|2|3|1|
|wired-or-short-bits01|4|4|0|
|wired-or-short-bits01|8|8|0|
|wired-or-short-bits01|15|15|0|
|wired-or-short-bits01|0|0|0|
|release-functional|—|10|—|
