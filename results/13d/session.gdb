set pagination off
set confirm off
break fact
run
printf "FRAME_N=%d\n", n
print/x $pc
printf "SP_VALUE=%p\n", $sp
step
continue
printf "FRAME_N=%d\n", n
printf "SP_VALUE=%p\n", $sp
continue
printf "FRAME_N=%d\n", n
printf "SP_VALUE=%p\n", $sp
backtrace
finish
printf "BACK_IN_N=%d\n", n
printf "SP_VALUE=%p\n", $sp
finish
printf "BACK_IN_N=%d\n", n
printf "SP_VALUE=%p\n", $sp
continue
quit
