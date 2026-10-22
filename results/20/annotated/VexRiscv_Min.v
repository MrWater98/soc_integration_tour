//      // verilator_coverage annotation
        // Generator : SpinalHDL v1.9.4    git head : 270018552577f3bb8e5339ee2583c9c22d324215
        // Component : VexRiscv
        // Git hash  : 8542a5786b26857f3ef830ae9e72eec031df42d3
        
        `timescale 1ns/1ps
        
        module VexRiscv (
          input  wire [31:0]   externalResetVector,
          input  wire          timerInterrupt,
          input  wire          softwareInterrupt,
          input  wire [31:0]   externalInterruptArray,
          output wire          iBusWishbone_CYC,
          output wire          iBusWishbone_STB,
          input  wire          iBusWishbone_ACK,
          output wire          iBusWishbone_WE,
          output wire [29:0]   iBusWishbone_ADR,
          input  wire [31:0]   iBusWishbone_DAT_MISO,
          output wire [31:0]   iBusWishbone_DAT_MOSI,
          output wire [3:0]    iBusWishbone_SEL,
          input  wire          iBusWishbone_ERR,
          output wire [2:0]    iBusWishbone_CTI,
          output wire [1:0]    iBusWishbone_BTE,
          output wire          dBusWishbone_CYC,
          output wire          dBusWishbone_STB,
          input  wire          dBusWishbone_ACK,
          output wire          dBusWishbone_WE,
          output wire [29:0]   dBusWishbone_ADR,
          input  wire [31:0]   dBusWishbone_DAT_MISO,
          output wire [31:0]   dBusWishbone_DAT_MOSI,
          output reg  [3:0]    dBusWishbone_SEL,
          input  wire          dBusWishbone_ERR,
          output wire [2:0]    dBusWishbone_CTI,
          output wire [1:0]    dBusWishbone_BTE,
          input  wire          clk,
          input  wire          reset
        );
          localparam EnvCtrlEnum_NONE = 2'd0;
          localparam EnvCtrlEnum_XRET = 2'd1;
          localparam EnvCtrlEnum_ECALL = 2'd2;
          localparam BranchCtrlEnum_INC = 2'd0;
          localparam BranchCtrlEnum_B = 2'd1;
          localparam BranchCtrlEnum_JAL = 2'd2;
          localparam BranchCtrlEnum_JALR = 2'd3;
          localparam ShiftCtrlEnum_DISABLE_1 = 2'd0;
          localparam ShiftCtrlEnum_SLL_1 = 2'd1;
          localparam ShiftCtrlEnum_SRL_1 = 2'd2;
          localparam ShiftCtrlEnum_SRA_1 = 2'd3;
          localparam AluBitwiseCtrlEnum_XOR_1 = 2'd0;
          localparam AluBitwiseCtrlEnum_OR_1 = 2'd1;
          localparam AluBitwiseCtrlEnum_AND_1 = 2'd2;
          localparam Src2CtrlEnum_RS = 2'd0;
          localparam Src2CtrlEnum_IMI = 2'd1;
          localparam Src2CtrlEnum_IMS = 2'd2;
          localparam Src2CtrlEnum_PC = 2'd3;
          localparam AluCtrlEnum_ADD_SUB = 2'd0;
          localparam AluCtrlEnum_SLT_SLTU = 2'd1;
          localparam AluCtrlEnum_BITWISE = 2'd2;
          localparam Src1CtrlEnum_RS = 2'd0;
          localparam Src1CtrlEnum_IMU = 2'd1;
          localparam Src1CtrlEnum_PC_INCREMENT = 2'd2;
          localparam Src1CtrlEnum_URS1 = 2'd3;
        
          wire                IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_ready;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_c_io_flush;
          reg        [31:0]   _zz_RegFilePlugin_regFile_port0;
          reg        [31:0]   _zz_RegFilePlugin_regFile_port1;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_c_io_push_ready;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_valid;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_error;
          wire       [31:0]   IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_inst;
          wire       [0:0]    IBusSimplePlugin_rspJoin_rspBuffer_c_io_occupancy;
          wire       [0:0]    IBusSimplePlugin_rspJoin_rspBuffer_c_io_availability;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_1;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_2;
          wire                _zz_decode_LEGAL_INSTRUCTION_3;
          wire       [0:0]    _zz_decode_LEGAL_INSTRUCTION_4;
          wire       [11:0]   _zz_decode_LEGAL_INSTRUCTION_5;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_6;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_7;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_8;
          wire                _zz_decode_LEGAL_INSTRUCTION_9;
          wire       [0:0]    _zz_decode_LEGAL_INSTRUCTION_10;
          wire       [5:0]    _zz_decode_LEGAL_INSTRUCTION_11;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_12;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_13;
          wire       [31:0]   _zz_decode_LEGAL_INSTRUCTION_14;
          wire                _zz_decode_LEGAL_INSTRUCTION_15;
          wire                _zz_decode_LEGAL_INSTRUCTION_16;
          wire       [1:0]    _zz_IBusSimplePlugin_jump_pcLoad_payload_1;
          wire       [1:0]    _zz_IBusSimplePlugin_jump_pcLoad_payload_2;
          wire       [31:0]   _zz_IBusSimplePlugin_fetchPc_pc;
          wire       [2:0]    _zz_IBusSimplePlugin_fetchPc_pc_1;
          wire       [2:0]    _zz_IBusSimplePlugin_pending_next;
          wire       [2:0]    _zz_IBusSimplePlugin_pending_next_1;
          wire       [0:0]    _zz_IBusSimplePlugin_pending_next_2;
          wire       [2:0]    _zz_IBusSimplePlugin_pending_next_3;
          wire       [0:0]    _zz_IBusSimplePlugin_pending_next_4;
          wire       [2:0]    _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter;
          wire       [0:0]    _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_1;
          wire       [2:0]    _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_2;
          wire       [0:0]    _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_3;
          wire       [2:0]    _zz_DBusSimplePlugin_memoryExceptionPort_payload_code;
          wire       [31:0]   _zz__zz_decode_IS_CSR;
          wire                _zz__zz_decode_IS_CSR_1;
          wire                _zz__zz_decode_IS_CSR_2;
          wire       [0:0]    _zz__zz_decode_IS_CSR_3;
          wire       [0:0]    _zz__zz_decode_IS_CSR_4;
          wire       [31:0]   _zz__zz_decode_IS_CSR_5;
          wire       [0:0]    _zz__zz_decode_IS_CSR_6;
          wire       [31:0]   _zz__zz_decode_IS_CSR_7;
          wire                _zz__zz_decode_IS_CSR_8;
          wire       [31:0]   _zz__zz_decode_IS_CSR_9;
          wire       [31:0]   _zz__zz_decode_IS_CSR_10;
          wire       [0:0]    _zz__zz_decode_IS_CSR_11;
          wire       [0:0]    _zz__zz_decode_IS_CSR_12;
          wire       [31:0]   _zz__zz_decode_IS_CSR_13;
          wire       [0:0]    _zz__zz_decode_IS_CSR_14;
          wire       [31:0]   _zz__zz_decode_IS_CSR_15;
          wire       [18:0]   _zz__zz_decode_IS_CSR_16;
          wire       [1:0]    _zz__zz_decode_IS_CSR_17;
          wire       [31:0]   _zz__zz_decode_IS_CSR_18;
          wire       [31:0]   _zz__zz_decode_IS_CSR_19;
          wire       [31:0]   _zz__zz_decode_IS_CSR_20;
          wire       [31:0]   _zz__zz_decode_IS_CSR_21;
          wire                _zz__zz_decode_IS_CSR_22;
          wire       [31:0]   _zz__zz_decode_IS_CSR_23;
          wire       [31:0]   _zz__zz_decode_IS_CSR_24;
          wire       [0:0]    _zz__zz_decode_IS_CSR_25;
          wire                _zz__zz_decode_IS_CSR_26;
          wire       [15:0]   _zz__zz_decode_IS_CSR_27;
          wire       [1:0]    _zz__zz_decode_IS_CSR_28;
          wire       [31:0]   _zz__zz_decode_IS_CSR_29;
          wire       [31:0]   _zz__zz_decode_IS_CSR_30;
          wire       [31:0]   _zz__zz_decode_IS_CSR_31;
          wire       [31:0]   _zz__zz_decode_IS_CSR_32;
          wire                _zz__zz_decode_IS_CSR_33;
          wire                _zz__zz_decode_IS_CSR_34;
          wire                _zz__zz_decode_IS_CSR_35;
          wire       [0:0]    _zz__zz_decode_IS_CSR_36;
          wire       [0:0]    _zz__zz_decode_IS_CSR_37;
          wire       [31:0]   _zz__zz_decode_IS_CSR_38;
          wire       [1:0]    _zz__zz_decode_IS_CSR_39;
          wire       [31:0]   _zz__zz_decode_IS_CSR_40;
          wire       [31:0]   _zz__zz_decode_IS_CSR_41;
          wire       [12:0]   _zz__zz_decode_IS_CSR_42;
          wire       [0:0]    _zz__zz_decode_IS_CSR_43;
          wire       [31:0]   _zz__zz_decode_IS_CSR_44;
          wire                _zz__zz_decode_IS_CSR_45;
          wire       [31:0]   _zz__zz_decode_IS_CSR_46;
          wire       [31:0]   _zz__zz_decode_IS_CSR_47;
          wire       [0:0]    _zz__zz_decode_IS_CSR_48;
          wire       [9:0]    _zz__zz_decode_IS_CSR_49;
          wire       [5:0]    _zz__zz_decode_IS_CSR_50;
          wire       [31:0]   _zz__zz_decode_IS_CSR_51;
          wire       [31:0]   _zz__zz_decode_IS_CSR_52;
          wire                _zz__zz_decode_IS_CSR_53;
          wire       [0:0]    _zz__zz_decode_IS_CSR_54;
          wire       [1:0]    _zz__zz_decode_IS_CSR_55;
          wire       [31:0]   _zz__zz_decode_IS_CSR_56;
          wire       [31:0]   _zz__zz_decode_IS_CSR_57;
          wire       [31:0]   _zz__zz_decode_IS_CSR_58;
          wire       [31:0]   _zz__zz_decode_IS_CSR_59;
          wire                _zz__zz_decode_IS_CSR_60;
          wire       [31:0]   _zz__zz_decode_IS_CSR_61;
          wire       [31:0]   _zz__zz_decode_IS_CSR_62;
          wire       [0:0]    _zz__zz_decode_IS_CSR_63;
          wire                _zz__zz_decode_IS_CSR_64;
          wire       [6:0]    _zz__zz_decode_IS_CSR_65;
          wire       [0:0]    _zz__zz_decode_IS_CSR_66;
          wire       [31:0]   _zz__zz_decode_IS_CSR_67;
          wire       [0:0]    _zz__zz_decode_IS_CSR_68;
          wire       [31:0]   _zz__zz_decode_IS_CSR_69;
          wire       [0:0]    _zz__zz_decode_IS_CSR_70;
          wire       [31:0]   _zz__zz_decode_IS_CSR_71;
          wire                _zz__zz_decode_IS_CSR_72;
          wire                _zz__zz_decode_IS_CSR_73;
          wire       [0:0]    _zz__zz_decode_IS_CSR_74;
          wire       [1:0]    _zz__zz_decode_IS_CSR_75;
          wire       [31:0]   _zz__zz_decode_IS_CSR_76;
          wire       [31:0]   _zz__zz_decode_IS_CSR_77;
          wire       [31:0]   _zz__zz_decode_IS_CSR_78;
          wire       [31:0]   _zz__zz_decode_IS_CSR_79;
          wire       [0:0]    _zz__zz_decode_IS_CSR_80;
          wire                _zz__zz_decode_IS_CSR_81;
          wire       [2:0]    _zz__zz_decode_IS_CSR_82;
          wire       [2:0]    _zz__zz_decode_IS_CSR_83;
          wire       [31:0]   _zz__zz_decode_IS_CSR_84;
          wire       [31:0]   _zz__zz_decode_IS_CSR_85;
          wire                _zz__zz_decode_IS_CSR_86;
          wire                _zz__zz_decode_IS_CSR_87;
          wire                _zz__zz_decode_IS_CSR_88;
          wire                _zz__zz_decode_IS_CSR_89;
          wire                _zz__zz_decode_IS_CSR_90;
          wire                _zz__zz_decode_IS_CSR_91;
          wire                _zz_RegFilePlugin_regFile_port;
          wire                _zz_decode_RegFilePlugin_rs1Data;
          wire                _zz_RegFilePlugin_regFile_port_1;
          wire                _zz_decode_RegFilePlugin_rs2Data;
          wire       [0:0]    _zz__zz_execute_REGFILE_WRITE_DATA;
          wire       [2:0]    _zz__zz_execute_SRC1;
          wire       [4:0]    _zz__zz_execute_SRC1_1;
          wire       [11:0]   _zz__zz_execute_SRC2_2;
          wire       [31:0]   _zz_execute_SrcPlugin_addSub;
          wire       [31:0]   _zz_execute_SrcPlugin_addSub_1;
          wire       [31:0]   _zz_execute_SrcPlugin_addSub_2;
          wire       [31:0]   _zz_execute_SrcPlugin_addSub_3;
          wire       [31:0]   _zz_execute_SrcPlugin_addSub_4;
          wire       [31:0]   _zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1;
          wire       [32:0]   _zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1_1;
          wire       [19:0]   _zz__zz_execute_BranchPlugin_branch_src2;
          wire       [11:0]   _zz__zz_execute_BranchPlugin_branch_src2_4;
          wire       [1:0]    _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1;
          wire       [1:0]    _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1_1;
          wire                _zz_when;
          wire       [31:0]   memory_MEMORY_READ_DATA;
          wire       [31:0]   execute_BRANCH_CALC;
          wire                execute_BRANCH_DO;
          wire       [31:0]   writeBack_REGFILE_WRITE_DATA;
          wire       [31:0]   execute_REGFILE_WRITE_DATA;
          wire       [1:0]    memory_MEMORY_ADDRESS_LOW;
          wire       [1:0]    execute_MEMORY_ADDRESS_LOW;
          wire                decode_CSR_READ_OPCODE;
          wire                decode_CSR_WRITE_OPCODE;
          wire                decode_SRC2_FORCE_ZERO;
          wire       [31:0]   decode_RS2;
          wire       [31:0]   decode_RS1;
          wire       [1:0]    _zz_memory_to_writeBack_ENV_CTRL;
          wire       [1:0]    _zz_memory_to_writeBack_ENV_CTRL_1;
          wire       [1:0]    _zz_execute_to_memory_ENV_CTRL;
          wire       [1:0]    _zz_execute_to_memory_ENV_CTRL_1;
          wire       [1:0]    decode_ENV_CTRL;
          wire       [1:0]    _zz_decode_ENV_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ENV_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ENV_CTRL_1;
          wire                decode_IS_CSR;
          wire       [1:0]    decode_BRANCH_CTRL;
          wire       [1:0]    _zz_decode_BRANCH_CTRL;
          wire       [1:0]    _zz_decode_to_execute_BRANCH_CTRL;
          wire       [1:0]    _zz_decode_to_execute_BRANCH_CTRL_1;
          wire       [1:0]    decode_SHIFT_CTRL;
          wire       [1:0]    _zz_decode_SHIFT_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SHIFT_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SHIFT_CTRL_1;
          wire       [1:0]    decode_ALU_BITWISE_CTRL;
          wire       [1:0]    _zz_decode_ALU_BITWISE_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ALU_BITWISE_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ALU_BITWISE_CTRL_1;
          wire                decode_SRC_LESS_UNSIGNED;
          wire                decode_MEMORY_STORE;
          wire                execute_BYPASSABLE_MEMORY_STAGE;
          wire                decode_BYPASSABLE_MEMORY_STAGE;
          wire                decode_BYPASSABLE_EXECUTE_STAGE;
          wire       [1:0]    decode_SRC2_CTRL;
          wire       [1:0]    _zz_decode_SRC2_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SRC2_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SRC2_CTRL_1;
          wire       [1:0]    decode_ALU_CTRL;
          wire       [1:0]    _zz_decode_ALU_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ALU_CTRL;
          wire       [1:0]    _zz_decode_to_execute_ALU_CTRL_1;
          wire                decode_MEMORY_ENABLE;
          wire       [1:0]    decode_SRC1_CTRL;
          wire       [1:0]    _zz_decode_SRC1_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SRC1_CTRL;
          wire       [1:0]    _zz_decode_to_execute_SRC1_CTRL_1;
          wire       [31:0]   writeBack_FORMAL_PC_NEXT;
          wire       [31:0]   memory_FORMAL_PC_NEXT;
          wire       [31:0]   execute_FORMAL_PC_NEXT;
          wire       [31:0]   decode_FORMAL_PC_NEXT;
          wire       [31:0]   memory_PC;
          wire                execute_CSR_READ_OPCODE;
          wire                execute_CSR_WRITE_OPCODE;
          wire                execute_IS_CSR;
          wire       [1:0]    memory_ENV_CTRL;
          wire       [1:0]    _zz_memory_ENV_CTRL;
          wire       [1:0]    execute_ENV_CTRL;
          wire       [1:0]    _zz_execute_ENV_CTRL;
          wire       [1:0]    writeBack_ENV_CTRL;
          wire       [1:0]    _zz_writeBack_ENV_CTRL;
          wire       [31:0]   memory_BRANCH_CALC;
          wire                memory_BRANCH_DO;
          wire       [31:0]   execute_PC;
          wire       [31:0]   execute_RS1;
          wire       [1:0]    execute_BRANCH_CTRL;
          wire       [1:0]    _zz_execute_BRANCH_CTRL;
          wire                decode_RS2_USE;
          wire                decode_RS1_USE;
          wire                execute_REGFILE_WRITE_VALID;
          wire                execute_BYPASSABLE_EXECUTE_STAGE;
          wire                memory_REGFILE_WRITE_VALID;
          wire       [31:0]   memory_INSTRUCTION;
          wire                memory_BYPASSABLE_MEMORY_STAGE;
          wire                writeBack_REGFILE_WRITE_VALID;
          reg        [31:0]   _zz_execute_to_memory_REGFILE_WRITE_DATA;
          wire       [1:0]    execute_SHIFT_CTRL;
          wire       [1:0]    _zz_execute_SHIFT_CTRL;
          wire                execute_SRC_LESS_UNSIGNED;
          wire                execute_SRC2_FORCE_ZERO;
          wire                execute_SRC_USE_SUB_LESS;
          wire       [31:0]   _zz_execute_to_memory_PC;
          wire       [1:0]    execute_SRC2_CTRL;
          wire       [1:0]    _zz_execute_SRC2_CTRL;
          wire       [1:0]    execute_SRC1_CTRL;
          wire       [1:0]    _zz_execute_SRC1_CTRL;
          wire                decode_SRC_USE_SUB_LESS;
          wire                decode_SRC_ADD_ZERO;
          wire       [31:0]   execute_SRC_ADD_SUB;
          wire                execute_SRC_LESS;
          wire       [1:0]    execute_ALU_CTRL;
          wire       [1:0]    _zz_execute_ALU_CTRL;
          wire       [31:0]   execute_SRC2;
          wire       [31:0]   execute_SRC1;
          wire       [1:0]    execute_ALU_BITWISE_CTRL;
          wire       [1:0]    _zz_execute_ALU_BITWISE_CTRL;
          wire       [31:0]   _zz_lastStageRegFileWrite_payload_address;
          wire                _zz_lastStageRegFileWrite_valid;
          reg                 _zz_1;
          wire       [31:0]   decode_INSTRUCTION_ANTICIPATED;
          reg                 decode_REGFILE_WRITE_VALID;
          wire                decode_LEGAL_INSTRUCTION;
          wire       [1:0]    _zz_decode_ENV_CTRL_1;
          wire       [1:0]    _zz_decode_BRANCH_CTRL_1;
          wire       [1:0]    _zz_decode_SHIFT_CTRL_1;
          wire       [1:0]    _zz_decode_ALU_BITWISE_CTRL_1;
          wire       [1:0]    _zz_decode_SRC2_CTRL_1;
          wire       [1:0]    _zz_decode_ALU_CTRL_1;
          wire       [1:0]    _zz_decode_SRC1_CTRL_1;
          reg        [31:0]   _zz_lastStageRegFileWrite_payload_data;
          wire                writeBack_MEMORY_ENABLE;
          wire       [1:0]    writeBack_MEMORY_ADDRESS_LOW;
          wire       [31:0]   writeBack_MEMORY_READ_DATA;
          wire                memory_ALIGNEMENT_FAULT;
          wire       [31:0]   memory_REGFILE_WRITE_DATA;
          wire                memory_MEMORY_STORE;
          wire                memory_MEMORY_ENABLE;
          wire       [31:0]   execute_SRC_ADD;
          wire       [31:0]   execute_RS2;
          wire       [31:0]   execute_INSTRUCTION;
          wire                execute_MEMORY_STORE;
          wire                execute_MEMORY_ENABLE;
          wire                execute_ALIGNEMENT_FAULT;
          reg        [31:0]   _zz_memory_to_writeBack_FORMAL_PC_NEXT;
          wire       [31:0]   decode_PC;
          wire       [31:0]   decode_INSTRUCTION;
          wire       [31:0]   writeBack_PC;
          wire       [31:0]   writeBack_INSTRUCTION;
          wire                decode_arbitration_haltItself;
          reg                 decode_arbitration_haltByOther;
          reg                 decode_arbitration_removeIt;
          wire                decode_arbitration_flushIt;
          reg                 decode_arbitration_flushNext;
          reg                 decode_arbitration_isValid;
          wire                decode_arbitration_isStuck;
          wire                decode_arbitration_isStuckByOthers;
          wire                decode_arbitration_isFlushed;
          wire                decode_arbitration_isMoving;
          wire                decode_arbitration_isFiring;
          reg                 execute_arbitration_haltItself;
          wire                execute_arbitration_haltByOther;
          reg                 execute_arbitration_removeIt;
          wire                execute_arbitration_flushIt;
          reg                 execute_arbitration_flushNext;
          reg                 execute_arbitration_isValid;
          wire                execute_arbitration_isStuck;
          wire                execute_arbitration_isStuckByOthers;
          wire                execute_arbitration_isFlushed;
          wire                execute_arbitration_isMoving;
          wire                execute_arbitration_isFiring;
          reg                 memory_arbitration_haltItself;
          wire                memory_arbitration_haltByOther;
          reg                 memory_arbitration_removeIt;
          wire                memory_arbitration_flushIt;
          reg                 memory_arbitration_flushNext;
          reg                 memory_arbitration_isValid;
          wire                memory_arbitration_isStuck;
          wire                memory_arbitration_isStuckByOthers;
          wire                memory_arbitration_isFlushed;
          wire                memory_arbitration_isMoving;
          wire                memory_arbitration_isFiring;
          wire                writeBack_arbitration_haltItself;
          wire                writeBack_arbitration_haltByOther;
          reg                 writeBack_arbitration_removeIt;
          wire                writeBack_arbitration_flushIt;
          reg                 writeBack_arbitration_flushNext;
          reg                 writeBack_arbitration_isValid;
          wire                writeBack_arbitration_isStuck;
          wire                writeBack_arbitration_isStuckByOthers;
          wire                writeBack_arbitration_isFlushed;
          wire                writeBack_arbitration_isMoving;
          wire                writeBack_arbitration_isFiring;
          wire       [31:0]   lastStageInstruction /* verilator public */ ;
          wire       [31:0]   lastStagePc /* verilator public */ ;
          wire                lastStageIsValid /* verilator public */ ;
          wire                lastStageIsFiring /* verilator public */ ;
          reg                 IBusSimplePlugin_fetcherHalt;
          wire                IBusSimplePlugin_forceNoDecodeCond;
          reg                 IBusSimplePlugin_incomingInstruction;
          wire                IBusSimplePlugin_pcValids_0;
          wire                IBusSimplePlugin_pcValids_1;
          wire                IBusSimplePlugin_pcValids_2;
          wire                IBusSimplePlugin_pcValids_3;
          wire                iBus_cmd_valid;
          reg                 iBus_cmd_ready;
          wire       [31:0]   iBus_cmd_payload_pc;
          wire                iBus_rsp_valid;
          wire                iBus_rsp_payload_error;
          wire       [31:0]   iBus_rsp_payload_inst;
          reg                 DBusSimplePlugin_memoryExceptionPort_valid;
          reg        [3:0]    DBusSimplePlugin_memoryExceptionPort_payload_code;
          wire       [31:0]   DBusSimplePlugin_memoryExceptionPort_payload_badAddr;
          wire                decodeExceptionPort_valid;
          wire       [3:0]    decodeExceptionPort_payload_code;
          wire       [31:0]   decodeExceptionPort_payload_badAddr;
          wire                BranchPlugin_jumpInterface_valid;
          wire       [31:0]   BranchPlugin_jumpInterface_payload;
          wire                BranchPlugin_branchExceptionPort_valid;
          wire       [3:0]    BranchPlugin_branchExceptionPort_payload_code;
          wire       [31:0]   BranchPlugin_branchExceptionPort_payload_badAddr;
          wire                BranchPlugin_inDebugNoFetchFlag;
          wire       [31:0]   CsrPlugin_csrMapping_readDataSignal;
          wire       [31:0]   CsrPlugin_csrMapping_readDataInit;
          wire       [31:0]   CsrPlugin_csrMapping_writeDataSignal;
          reg                 CsrPlugin_csrMapping_allowCsrSignal;
          wire                CsrPlugin_csrMapping_hazardFree;
          wire                CsrPlugin_csrMapping_doForceFailCsr;
          wire                CsrPlugin_inWfi /* verilator public */ ;
          wire                CsrPlugin_thirdPartyWake;
          reg                 CsrPlugin_jumpInterface_valid;
          reg        [31:0]   CsrPlugin_jumpInterface_payload;
          wire                CsrPlugin_exceptionPendings_0;
          wire                CsrPlugin_exceptionPendings_1;
          wire                CsrPlugin_exceptionPendings_2;
          wire                CsrPlugin_exceptionPendings_3;
          wire                externalInterrupt;
          wire                contextSwitching;
          reg        [1:0]    CsrPlugin_privilege;
          wire                CsrPlugin_forceMachineWire;
          reg                 CsrPlugin_selfException_valid;
          reg        [3:0]    CsrPlugin_selfException_payload_code;
          wire       [31:0]   CsrPlugin_selfException_payload_badAddr;
          wire                CsrPlugin_allowInterrupts;
          wire                CsrPlugin_allowException;
          wire                CsrPlugin_allowEbreakException;
          wire                CsrPlugin_xretAwayFromMachine;
          wire                IBusSimplePlugin_externalFlush;
          wire                IBusSimplePlugin_jump_pcLoad_valid;
          wire       [31:0]   IBusSimplePlugin_jump_pcLoad_payload;
          wire       [1:0]    _zz_IBusSimplePlugin_jump_pcLoad_payload;
          wire                IBusSimplePlugin_fetchPc_output_valid;
          wire                IBusSimplePlugin_fetchPc_output_ready;
          wire       [31:0]   IBusSimplePlugin_fetchPc_output_payload;
          reg        [31:0]   IBusSimplePlugin_fetchPc_pcReg /* verilator public */ ;
          reg                 IBusSimplePlugin_fetchPc_correction;
          reg                 IBusSimplePlugin_fetchPc_correctionReg;
          wire                IBusSimplePlugin_fetchPc_output_fire;
          wire                IBusSimplePlugin_fetchPc_corrected;
          reg                 IBusSimplePlugin_fetchPc_pcRegPropagate;
          reg                 IBusSimplePlugin_fetchPc_booted;
          reg                 IBusSimplePlugin_fetchPc_inc;
          wire                when_Fetcher_l133;
          wire                when_Fetcher_l133_1;
          reg        [31:0]   IBusSimplePlugin_fetchPc_pc;
          reg                 IBusSimplePlugin_fetchPc_flushed;
          wire                when_Fetcher_l160;
          wire                IBusSimplePlugin_iBusRsp_redoFetch;
          wire                IBusSimplePlugin_iBusRsp_stages_0_input_valid;
          wire                IBusSimplePlugin_iBusRsp_stages_0_input_ready;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_stages_0_input_payload;
          wire                IBusSimplePlugin_iBusRsp_stages_0_output_valid;
          wire                IBusSimplePlugin_iBusRsp_stages_0_output_ready;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_stages_0_output_payload;
          reg                 IBusSimplePlugin_iBusRsp_stages_0_halt;
          wire                IBusSimplePlugin_iBusRsp_stages_1_input_valid;
          wire                IBusSimplePlugin_iBusRsp_stages_1_input_ready;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_stages_1_input_payload;
          wire                IBusSimplePlugin_iBusRsp_stages_1_output_valid;
          wire                IBusSimplePlugin_iBusRsp_stages_1_output_ready;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_stages_1_output_payload;
          wire                IBusSimplePlugin_iBusRsp_stages_1_halt;
          wire                _zz_IBusSimplePlugin_iBusRsp_stages_0_input_ready;
          wire                _zz_IBusSimplePlugin_iBusRsp_stages_1_input_ready;
          wire                IBusSimplePlugin_iBusRsp_flush;
          wire                _zz_IBusSimplePlugin_iBusRsp_stages_0_output_ready;
          wire                _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid;
          reg                 _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid_1;
          reg                 IBusSimplePlugin_iBusRsp_readyForError;
          wire                IBusSimplePlugin_iBusRsp_output_valid;
          wire                IBusSimplePlugin_iBusRsp_output_ready;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_output_payload_pc;
          wire                IBusSimplePlugin_iBusRsp_output_payload_rsp_error;
          wire       [31:0]   IBusSimplePlugin_iBusRsp_output_payload_rsp_inst;
          wire                IBusSimplePlugin_iBusRsp_output_payload_isRvc;
          wire                IBusSimplePlugin_injector_decodeInput_valid;
          wire                IBusSimplePlugin_injector_decodeInput_ready;
          wire       [31:0]   IBusSimplePlugin_injector_decodeInput_payload_pc;
          wire                IBusSimplePlugin_injector_decodeInput_payload_rsp_error;
          wire       [31:0]   IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
          wire                IBusSimplePlugin_injector_decodeInput_payload_isRvc;
          reg                 _zz_IBusSimplePlugin_injector_decodeInput_valid;
          reg        [31:0]   _zz_IBusSimplePlugin_injector_decodeInput_payload_pc;
          reg                 _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_error;
          reg        [31:0]   _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
          reg                 _zz_IBusSimplePlugin_injector_decodeInput_payload_isRvc;
          wire                when_Fetcher_l322;
          reg                 IBusSimplePlugin_injector_nextPcCalc_valids_0;
          wire                when_Fetcher_l331;
          reg                 IBusSimplePlugin_injector_nextPcCalc_valids_1;
          wire                when_Fetcher_l331_1;
          reg                 IBusSimplePlugin_injector_nextPcCalc_valids_2;
          wire                when_Fetcher_l331_2;
          reg                 IBusSimplePlugin_injector_nextPcCalc_valids_3;
          wire                when_Fetcher_l331_3;
          reg                 IBusSimplePlugin_injector_nextPcCalc_valids_4;
          wire                when_Fetcher_l331_4;
          reg        [31:0]   IBusSimplePlugin_injector_formal_rawInDecode;
          wire                IBusSimplePlugin_cmd_valid;
          wire                IBusSimplePlugin_cmd_ready;
          wire       [31:0]   IBusSimplePlugin_cmd_payload_pc;
          wire                IBusSimplePlugin_pending_inc;
          wire                IBusSimplePlugin_pending_dec;
          reg        [2:0]    IBusSimplePlugin_pending_value;
          wire       [2:0]    IBusSimplePlugin_pending_next;
          wire                IBusSimplePlugin_cmdFork_canEmit;
          wire                when_IBusSimplePlugin_l305;
          wire                IBusSimplePlugin_cmd_fire;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_output_valid;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_output_ready;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_output_payload_error;
          wire       [31:0]   IBusSimplePlugin_rspJoin_rspBuffer_output_payload_inst;
          reg        [2:0]    IBusSimplePlugin_rspJoin_rspBuffer_discardCounter;
          wire                iBus_rsp_toStream_valid;
          wire                iBus_rsp_toStream_ready;
          wire                iBus_rsp_toStream_payload_error;
          wire       [31:0]   iBus_rsp_toStream_payload_inst;
          wire                IBusSimplePlugin_rspJoin_rspBuffer_flush;
          wire                toplevel_IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_fire;
          wire       [31:0]   IBusSimplePlugin_rspJoin_fetchRsp_pc;
          reg                 IBusSimplePlugin_rspJoin_fetchRsp_rsp_error;
          wire       [31:0]   IBusSimplePlugin_rspJoin_fetchRsp_rsp_inst;
          wire                IBusSimplePlugin_rspJoin_fetchRsp_isRvc;
          wire                when_IBusSimplePlugin_l376;
          wire                IBusSimplePlugin_rspJoin_join_valid;
          wire                IBusSimplePlugin_rspJoin_join_ready;
          wire       [31:0]   IBusSimplePlugin_rspJoin_join_payload_pc;
          wire                IBusSimplePlugin_rspJoin_join_payload_rsp_error;
          wire       [31:0]   IBusSimplePlugin_rspJoin_join_payload_rsp_inst;
          wire                IBusSimplePlugin_rspJoin_join_payload_isRvc;
          wire                IBusSimplePlugin_rspJoin_exceptionDetected;
          wire                IBusSimplePlugin_rspJoin_join_fire;
          wire                _zz_IBusSimplePlugin_iBusRsp_output_valid;
          wire                dBus_cmd_valid;
          wire                dBus_cmd_ready;
          wire                dBus_cmd_payload_wr;
          wire       [31:0]   dBus_cmd_payload_address;
          wire       [31:0]   dBus_cmd_payload_data;
          wire       [1:0]    dBus_cmd_payload_size;
          wire                dBus_rsp_ready;
          wire                dBus_rsp_error;
          wire       [31:0]   dBus_rsp_data;
          wire                _zz_dBus_cmd_valid;
          reg                 execute_DBusSimplePlugin_skipCmd;
          reg        [31:0]   _zz_dBus_cmd_payload_data;
          wire                when_DBusSimplePlugin_l436;
          reg        [3:0]    _zz_execute_DBusSimplePlugin_formalMask;
          wire       [3:0]    execute_DBusSimplePlugin_formalMask;
          wire                when_DBusSimplePlugin_l490;
          wire                when_DBusSimplePlugin_l497;
          wire                when_DBusSimplePlugin_l523;
          reg        [31:0]   writeBack_DBusSimplePlugin_rspShifted;
          wire       [1:0]    switch_Misc_l232;
          wire                _zz_writeBack_DBusSimplePlugin_rspFormated;
          reg        [31:0]   _zz_writeBack_DBusSimplePlugin_rspFormated_1;
          wire                _zz_writeBack_DBusSimplePlugin_rspFormated_2;
          reg        [31:0]   _zz_writeBack_DBusSimplePlugin_rspFormated_3;
          reg        [31:0]   writeBack_DBusSimplePlugin_rspFormated;
          wire                when_DBusSimplePlugin_l566;
          wire       [25:0]   _zz_decode_IS_CSR;
          wire                _zz_decode_IS_CSR_1;
          wire                _zz_decode_IS_CSR_2;
          wire                _zz_decode_IS_CSR_3;
          wire                _zz_decode_IS_CSR_4;
          wire                _zz_decode_IS_CSR_5;
          wire       [1:0]    _zz_decode_SRC1_CTRL_2;
          wire       [1:0]    _zz_decode_ALU_CTRL_2;
          wire       [1:0]    _zz_decode_SRC2_CTRL_2;
          wire       [1:0]    _zz_decode_ALU_BITWISE_CTRL_2;
          wire       [1:0]    _zz_decode_SHIFT_CTRL_2;
          wire       [1:0]    _zz_decode_BRANCH_CTRL_2;
          wire       [1:0]    _zz_decode_ENV_CTRL_2;
          wire                when_RegFilePlugin_l63;
          wire       [4:0]    decode_RegFilePlugin_regFileReadAddress1;
          wire       [4:0]    decode_RegFilePlugin_regFileReadAddress2;
          wire       [31:0]   decode_RegFilePlugin_rs1Data;
          wire       [31:0]   decode_RegFilePlugin_rs2Data;
          reg                 lastStageRegFileWrite_valid /* verilator public */ ;
          reg        [4:0]    lastStageRegFileWrite_payload_address /* verilator public */ ;
          reg        [31:0]   lastStageRegFileWrite_payload_data /* verilator public */ ;
          reg                 _zz_5;
          reg        [31:0]   execute_IntAluPlugin_bitwise;
          reg        [31:0]   _zz_execute_REGFILE_WRITE_DATA;
          reg        [31:0]   _zz_execute_SRC1;
          wire                _zz_execute_SRC2;
          reg        [19:0]   _zz_execute_SRC2_1;
          wire                _zz_execute_SRC2_2;
          reg        [19:0]   _zz_execute_SRC2_3;
          reg        [31:0]   _zz_execute_SRC2_4;
          reg        [31:0]   execute_SrcPlugin_addSub;
          wire                execute_SrcPlugin_less;
          reg                 execute_LightShifterPlugin_isActive;
          wire                execute_LightShifterPlugin_isShift;
          reg        [4:0]    execute_LightShifterPlugin_amplitudeReg;
          wire       [4:0]    execute_LightShifterPlugin_amplitude;
          wire       [31:0]   execute_LightShifterPlugin_shiftInput;
          wire                execute_LightShifterPlugin_done;
          wire                when_ShiftPlugins_l169;
          reg        [31:0]   _zz_execute_to_memory_REGFILE_WRITE_DATA_1;
          wire                when_ShiftPlugins_l175;
          wire                when_ShiftPlugins_l184;
          reg                 HazardSimplePlugin_src0Hazard;
          reg                 HazardSimplePlugin_src1Hazard;
          wire                HazardSimplePlugin_writeBackWrites_valid;
          wire       [4:0]    HazardSimplePlugin_writeBackWrites_payload_address;
          wire       [31:0]   HazardSimplePlugin_writeBackWrites_payload_data;
          reg                 HazardSimplePlugin_writeBackBuffer_valid;
          reg        [4:0]    HazardSimplePlugin_writeBackBuffer_payload_address;
          reg        [31:0]   HazardSimplePlugin_writeBackBuffer_payload_data;
          wire                HazardSimplePlugin_addr0Match;
          wire                HazardSimplePlugin_addr1Match;
          wire                when_HazardSimplePlugin_l59;
          wire                when_HazardSimplePlugin_l62;
          wire                when_HazardSimplePlugin_l57;
          wire                when_HazardSimplePlugin_l58;
          wire                when_HazardSimplePlugin_l59_1;
          wire                when_HazardSimplePlugin_l62_1;
          wire                when_HazardSimplePlugin_l57_1;
          wire                when_HazardSimplePlugin_l58_1;
          wire                when_HazardSimplePlugin_l59_2;
          wire                when_HazardSimplePlugin_l62_2;
          wire                when_HazardSimplePlugin_l57_2;
          wire                when_HazardSimplePlugin_l58_2;
          wire                when_HazardSimplePlugin_l105;
          wire                when_HazardSimplePlugin_l108;
          wire                when_HazardSimplePlugin_l113;
          wire                execute_BranchPlugin_eq;
          wire       [2:0]    switch_Misc_l232_1;
          reg                 _zz_execute_BRANCH_DO;
          reg                 _zz_execute_BRANCH_DO_1;
          wire       [31:0]   execute_BranchPlugin_branch_src1;
          wire                _zz_execute_BranchPlugin_branch_src2;
          reg        [10:0]   _zz_execute_BranchPlugin_branch_src2_1;
          wire                _zz_execute_BranchPlugin_branch_src2_2;
          reg        [19:0]   _zz_execute_BranchPlugin_branch_src2_3;
          wire                _zz_execute_BranchPlugin_branch_src2_4;
          reg        [18:0]   _zz_execute_BranchPlugin_branch_src2_5;
          reg        [31:0]   _zz_execute_BranchPlugin_branch_src2_6;
          wire       [31:0]   execute_BranchPlugin_branch_src2;
          wire       [31:0]   execute_BranchPlugin_branchAdder;
          wire       [1:0]    CsrPlugin_misa_base;
          wire       [25:0]   CsrPlugin_misa_extensions;
          reg        [1:0]    CsrPlugin_mtvec_mode;
          reg        [29:0]   CsrPlugin_mtvec_base;
          reg        [31:0]   CsrPlugin_mepc;
          reg                 CsrPlugin_mstatus_MIE;
          reg                 CsrPlugin_mstatus_MPIE;
          reg        [1:0]    CsrPlugin_mstatus_MPP;
          reg                 CsrPlugin_mip_MEIP;
          reg                 CsrPlugin_mip_MTIP;
          reg                 CsrPlugin_mip_MSIP;
          reg                 CsrPlugin_mie_MEIE;
          reg                 CsrPlugin_mie_MTIE;
          reg                 CsrPlugin_mie_MSIE;
          reg                 CsrPlugin_mcause_interrupt;
          reg        [3:0]    CsrPlugin_mcause_exceptionCode;
          reg        [31:0]   CsrPlugin_mtval;
          reg        [63:0]   CsrPlugin_mcycle;
          reg        [63:0]   CsrPlugin_minstret;
          wire                _zz_when_CsrPlugin_l1302;
          wire                _zz_when_CsrPlugin_l1302_1;
          wire                _zz_when_CsrPlugin_l1302_2;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValids_decode;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValids_execute;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValids_memory;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory;
          reg                 CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack;
          reg        [3:0]    CsrPlugin_exceptionPortCtrl_exceptionContext_code;
          reg        [31:0]   CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr;
          wire       [1:0]    CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilegeUncapped;
          wire       [1:0]    CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilege;
          wire       [1:0]    _zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code;
          wire                _zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1;
          wire                when_CsrPlugin_l1259;
          wire                when_CsrPlugin_l1259_1;
          wire                when_CsrPlugin_l1259_2;
          wire                when_CsrPlugin_l1259_3;
          wire                when_CsrPlugin_l1272;
          reg                 CsrPlugin_interrupt_valid;
          reg        [3:0]    CsrPlugin_interrupt_code /* verilator public */ ;
          reg        [1:0]    CsrPlugin_interrupt_targetPrivilege;
          wire                when_CsrPlugin_l1296;
          wire                when_CsrPlugin_l1302;
          wire                when_CsrPlugin_l1302_1;
          wire                when_CsrPlugin_l1302_2;
          wire                CsrPlugin_exception;
          wire                CsrPlugin_lastStageWasWfi;
          reg                 CsrPlugin_pipelineLiberator_pcValids_0;
          reg                 CsrPlugin_pipelineLiberator_pcValids_1;
          reg                 CsrPlugin_pipelineLiberator_pcValids_2;
          wire                CsrPlugin_pipelineLiberator_active;
          wire                when_CsrPlugin_l1335;
          wire                when_CsrPlugin_l1335_1;
          wire                when_CsrPlugin_l1335_2;
          wire                when_CsrPlugin_l1340;
          reg                 CsrPlugin_pipelineLiberator_done;
          wire                when_CsrPlugin_l1346;
          wire                CsrPlugin_interruptJump /* verilator public */ ;
          reg                 CsrPlugin_hadException /* verilator public */ ;
          reg        [1:0]    CsrPlugin_targetPrivilege;
          reg        [3:0]    CsrPlugin_trapCause;
          wire                CsrPlugin_trapCauseEbreakDebug;
          reg        [1:0]    CsrPlugin_xtvec_mode;
          reg        [29:0]   CsrPlugin_xtvec_base;
          wire                CsrPlugin_trapEnterDebug;
          wire                when_CsrPlugin_l1390;
          wire                when_CsrPlugin_l1398;
          wire                when_CsrPlugin_l1456;
          wire       [1:0]    switch_CsrPlugin_l1460;
          reg                 execute_CsrPlugin_wfiWake;
          wire                when_CsrPlugin_l1527;
          wire                execute_CsrPlugin_blockedBySideEffects;
          reg                 execute_CsrPlugin_illegalAccess;
          reg                 execute_CsrPlugin_illegalInstruction;
          wire                when_CsrPlugin_l1547;
          wire                when_CsrPlugin_l1548;
          wire                when_CsrPlugin_l1555;
          reg                 execute_CsrPlugin_writeInstruction;
          reg                 execute_CsrPlugin_readInstruction;
          wire                execute_CsrPlugin_writeEnable;
          wire                execute_CsrPlugin_readEnable;
          wire       [31:0]   execute_CsrPlugin_readToWriteData;
          wire                switch_Misc_l232_2;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_writeDataSignal;
          wire                when_CsrPlugin_l1587;
          wire                when_CsrPlugin_l1591;
          wire       [11:0]   execute_CsrPlugin_csrAddress;
          reg        [31:0]   externalInterruptArray_regNext;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit;
          wire       [31:0]   _zz_externalInterrupt;
          wire                when_Pipeline_l124;
          reg        [31:0]   decode_to_execute_PC;
          wire                when_Pipeline_l124_1;
          reg        [31:0]   execute_to_memory_PC;
          wire                when_Pipeline_l124_2;
          reg        [31:0]   memory_to_writeBack_PC;
          wire                when_Pipeline_l124_3;
          reg        [31:0]   decode_to_execute_INSTRUCTION;
          wire                when_Pipeline_l124_4;
          reg        [31:0]   execute_to_memory_INSTRUCTION;
          wire                when_Pipeline_l124_5;
          reg        [31:0]   memory_to_writeBack_INSTRUCTION;
          wire                when_Pipeline_l124_6;
          reg        [31:0]   decode_to_execute_FORMAL_PC_NEXT;
          wire                when_Pipeline_l124_7;
          reg        [31:0]   execute_to_memory_FORMAL_PC_NEXT;
          wire                when_Pipeline_l124_8;
          reg        [31:0]   memory_to_writeBack_FORMAL_PC_NEXT;
          wire                when_Pipeline_l124_9;
          reg        [1:0]    decode_to_execute_SRC1_CTRL;
          wire                when_Pipeline_l124_10;
          reg                 decode_to_execute_SRC_USE_SUB_LESS;
          wire                when_Pipeline_l124_11;
          reg                 decode_to_execute_MEMORY_ENABLE;
          wire                when_Pipeline_l124_12;
          reg                 execute_to_memory_MEMORY_ENABLE;
          wire                when_Pipeline_l124_13;
          reg                 memory_to_writeBack_MEMORY_ENABLE;
          wire                when_Pipeline_l124_14;
          reg        [1:0]    decode_to_execute_ALU_CTRL;
          wire                when_Pipeline_l124_15;
          reg        [1:0]    decode_to_execute_SRC2_CTRL;
          wire                when_Pipeline_l124_16;
          reg                 decode_to_execute_REGFILE_WRITE_VALID;
          wire                when_Pipeline_l124_17;
          reg                 execute_to_memory_REGFILE_WRITE_VALID;
          wire                when_Pipeline_l124_18;
          reg                 memory_to_writeBack_REGFILE_WRITE_VALID;
          wire                when_Pipeline_l124_19;
          reg                 decode_to_execute_BYPASSABLE_EXECUTE_STAGE;
          wire                when_Pipeline_l124_20;
          reg                 decode_to_execute_BYPASSABLE_MEMORY_STAGE;
          wire                when_Pipeline_l124_21;
          reg                 execute_to_memory_BYPASSABLE_MEMORY_STAGE;
          wire                when_Pipeline_l124_22;
          reg                 decode_to_execute_MEMORY_STORE;
          wire                when_Pipeline_l124_23;
          reg                 execute_to_memory_MEMORY_STORE;
          wire                when_Pipeline_l124_24;
          reg                 decode_to_execute_SRC_LESS_UNSIGNED;
          wire                when_Pipeline_l124_25;
          reg        [1:0]    decode_to_execute_ALU_BITWISE_CTRL;
          wire                when_Pipeline_l124_26;
          reg        [1:0]    decode_to_execute_SHIFT_CTRL;
          wire                when_Pipeline_l124_27;
          reg        [1:0]    decode_to_execute_BRANCH_CTRL;
          wire                when_Pipeline_l124_28;
          reg                 decode_to_execute_IS_CSR;
          wire                when_Pipeline_l124_29;
          reg        [1:0]    decode_to_execute_ENV_CTRL;
          wire                when_Pipeline_l124_30;
          reg        [1:0]    execute_to_memory_ENV_CTRL;
          wire                when_Pipeline_l124_31;
          reg        [1:0]    memory_to_writeBack_ENV_CTRL;
          wire                when_Pipeline_l124_32;
          reg        [31:0]   decode_to_execute_RS1;
          wire                when_Pipeline_l124_33;
          reg        [31:0]   decode_to_execute_RS2;
          wire                when_Pipeline_l124_34;
          reg                 decode_to_execute_SRC2_FORCE_ZERO;
          wire                when_Pipeline_l124_35;
          reg                 decode_to_execute_CSR_WRITE_OPCODE;
          wire                when_Pipeline_l124_36;
          reg                 decode_to_execute_CSR_READ_OPCODE;
          wire                when_Pipeline_l124_37;
          reg                 execute_to_memory_ALIGNEMENT_FAULT;
          wire                when_Pipeline_l124_38;
          reg        [1:0]    execute_to_memory_MEMORY_ADDRESS_LOW;
          wire                when_Pipeline_l124_39;
          reg        [1:0]    memory_to_writeBack_MEMORY_ADDRESS_LOW;
          wire                when_Pipeline_l124_40;
          reg        [31:0]   execute_to_memory_REGFILE_WRITE_DATA;
          wire                when_Pipeline_l124_41;
          reg        [31:0]   memory_to_writeBack_REGFILE_WRITE_DATA;
          wire                when_Pipeline_l124_42;
          reg                 execute_to_memory_BRANCH_DO;
          wire                when_Pipeline_l124_43;
          reg        [31:0]   execute_to_memory_BRANCH_CALC;
          wire                when_Pipeline_l124_44;
          reg        [31:0]   memory_to_writeBack_MEMORY_READ_DATA;
          wire                when_Pipeline_l151;
          wire                when_Pipeline_l154;
          wire                when_Pipeline_l151_1;
          wire                when_Pipeline_l154_1;
          wire                when_Pipeline_l151_2;
          wire                when_Pipeline_l154_2;
          wire                when_CsrPlugin_l1669;
          reg                 execute_CsrPlugin_csr_768;
          wire                when_CsrPlugin_l1669_1;
          reg                 execute_CsrPlugin_csr_836;
          wire                when_CsrPlugin_l1669_2;
          reg                 execute_CsrPlugin_csr_772;
          wire                when_CsrPlugin_l1669_3;
          reg                 execute_CsrPlugin_csr_773;
          wire                when_CsrPlugin_l1669_4;
          reg                 execute_CsrPlugin_csr_833;
          wire                when_CsrPlugin_l1669_5;
          reg                 execute_CsrPlugin_csr_834;
          wire                when_CsrPlugin_l1669_6;
          reg                 execute_CsrPlugin_csr_835;
          wire                when_CsrPlugin_l1669_7;
          reg                 execute_CsrPlugin_csr_3008;
          wire                when_CsrPlugin_l1669_8;
          reg                 execute_CsrPlugin_csr_4032;
          wire       [1:0]    switch_CsrPlugin_l1031;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_1;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_2;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_3;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_4;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_5;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_6;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_7;
          reg        [31:0]   _zz_CsrPlugin_csrMapping_readDataInit_8;
          wire                when_CsrPlugin_l1702;
          wire       [11:0]   _zz_when_CsrPlugin_l1709;
          wire                when_CsrPlugin_l1709;
          reg                 when_CsrPlugin_l1719;
          wire                when_CsrPlugin_l1717;
          wire                when_CsrPlugin_l1725;
          wire                iBus_cmd_m2sPipe_valid;
          wire                iBus_cmd_m2sPipe_ready;
          wire       [31:0]   iBus_cmd_m2sPipe_payload_pc;
          reg                 iBus_cmd_rValid;
          reg        [31:0]   iBus_cmd_rData_pc;
          wire                when_Stream_l369;
          wire                dBus_cmd_halfPipe_valid;
          wire                dBus_cmd_halfPipe_ready;
          wire                dBus_cmd_halfPipe_payload_wr;
          wire       [31:0]   dBus_cmd_halfPipe_payload_address;
          wire       [31:0]   dBus_cmd_halfPipe_payload_data;
          wire       [1:0]    dBus_cmd_halfPipe_payload_size;
          reg                 dBus_cmd_rValid;
          wire                dBus_cmd_halfPipe_fire;
          reg                 dBus_cmd_rData_wr;
          reg        [31:0]   dBus_cmd_rData_address;
          reg        [31:0]   dBus_cmd_rData_data;
          reg        [1:0]    dBus_cmd_rData_size;
          reg        [3:0]    _zz_dBusWishbone_SEL;
          wire                when_DBusSimplePlugin_l196;
          `ifndef SYNTHESIS
          reg [39:0] _zz_memory_to_writeBack_ENV_CTRL_string;
          reg [39:0] _zz_memory_to_writeBack_ENV_CTRL_1_string;
          reg [39:0] _zz_execute_to_memory_ENV_CTRL_string;
          reg [39:0] _zz_execute_to_memory_ENV_CTRL_1_string;
          reg [39:0] decode_ENV_CTRL_string;
          reg [39:0] _zz_decode_ENV_CTRL_string;
          reg [39:0] _zz_decode_to_execute_ENV_CTRL_string;
          reg [39:0] _zz_decode_to_execute_ENV_CTRL_1_string;
          reg [31:0] decode_BRANCH_CTRL_string;
          reg [31:0] _zz_decode_BRANCH_CTRL_string;
          reg [31:0] _zz_decode_to_execute_BRANCH_CTRL_string;
          reg [31:0] _zz_decode_to_execute_BRANCH_CTRL_1_string;
          reg [71:0] decode_SHIFT_CTRL_string;
          reg [71:0] _zz_decode_SHIFT_CTRL_string;
          reg [71:0] _zz_decode_to_execute_SHIFT_CTRL_string;
          reg [71:0] _zz_decode_to_execute_SHIFT_CTRL_1_string;
          reg [39:0] decode_ALU_BITWISE_CTRL_string;
          reg [39:0] _zz_decode_ALU_BITWISE_CTRL_string;
          reg [39:0] _zz_decode_to_execute_ALU_BITWISE_CTRL_string;
          reg [39:0] _zz_decode_to_execute_ALU_BITWISE_CTRL_1_string;
          reg [23:0] decode_SRC2_CTRL_string;
          reg [23:0] _zz_decode_SRC2_CTRL_string;
          reg [23:0] _zz_decode_to_execute_SRC2_CTRL_string;
          reg [23:0] _zz_decode_to_execute_SRC2_CTRL_1_string;
          reg [63:0] decode_ALU_CTRL_string;
          reg [63:0] _zz_decode_ALU_CTRL_string;
          reg [63:0] _zz_decode_to_execute_ALU_CTRL_string;
          reg [63:0] _zz_decode_to_execute_ALU_CTRL_1_string;
          reg [95:0] decode_SRC1_CTRL_string;
          reg [95:0] _zz_decode_SRC1_CTRL_string;
          reg [95:0] _zz_decode_to_execute_SRC1_CTRL_string;
          reg [95:0] _zz_decode_to_execute_SRC1_CTRL_1_string;
          reg [39:0] memory_ENV_CTRL_string;
          reg [39:0] _zz_memory_ENV_CTRL_string;
          reg [39:0] execute_ENV_CTRL_string;
          reg [39:0] _zz_execute_ENV_CTRL_string;
          reg [39:0] writeBack_ENV_CTRL_string;
          reg [39:0] _zz_writeBack_ENV_CTRL_string;
          reg [31:0] execute_BRANCH_CTRL_string;
          reg [31:0] _zz_execute_BRANCH_CTRL_string;
          reg [71:0] execute_SHIFT_CTRL_string;
          reg [71:0] _zz_execute_SHIFT_CTRL_string;
          reg [23:0] execute_SRC2_CTRL_string;
          reg [23:0] _zz_execute_SRC2_CTRL_string;
          reg [95:0] execute_SRC1_CTRL_string;
          reg [95:0] _zz_execute_SRC1_CTRL_string;
          reg [63:0] execute_ALU_CTRL_string;
          reg [63:0] _zz_execute_ALU_CTRL_string;
          reg [39:0] execute_ALU_BITWISE_CTRL_string;
          reg [39:0] _zz_execute_ALU_BITWISE_CTRL_string;
          reg [39:0] _zz_decode_ENV_CTRL_1_string;
          reg [31:0] _zz_decode_BRANCH_CTRL_1_string;
          reg [71:0] _zz_decode_SHIFT_CTRL_1_string;
          reg [39:0] _zz_decode_ALU_BITWISE_CTRL_1_string;
          reg [23:0] _zz_decode_SRC2_CTRL_1_string;
          reg [63:0] _zz_decode_ALU_CTRL_1_string;
          reg [95:0] _zz_decode_SRC1_CTRL_1_string;
          reg [95:0] _zz_decode_SRC1_CTRL_2_string;
          reg [63:0] _zz_decode_ALU_CTRL_2_string;
          reg [23:0] _zz_decode_SRC2_CTRL_2_string;
          reg [39:0] _zz_decode_ALU_BITWISE_CTRL_2_string;
          reg [71:0] _zz_decode_SHIFT_CTRL_2_string;
          reg [31:0] _zz_decode_BRANCH_CTRL_2_string;
          reg [39:0] _zz_decode_ENV_CTRL_2_string;
          reg [95:0] decode_to_execute_SRC1_CTRL_string;
          reg [63:0] decode_to_execute_ALU_CTRL_string;
          reg [23:0] decode_to_execute_SRC2_CTRL_string;
          reg [39:0] decode_to_execute_ALU_BITWISE_CTRL_string;
          reg [71:0] decode_to_execute_SHIFT_CTRL_string;
          reg [31:0] decode_to_execute_BRANCH_CTRL_string;
          reg [39:0] decode_to_execute_ENV_CTRL_string;
          reg [39:0] execute_to_memory_ENV_CTRL_string;
          reg [39:0] memory_to_writeBack_ENV_CTRL_string;
          `endif
        
          (* no_rw_check , ram_style = "block" *) reg [31:0] RegFilePlugin_regFile [0:31] /* verilator public */ ;
        
          assign _zz_when = ({BranchPlugin_branchExceptionPort_valid,DBusSimplePlugin_memoryExceptionPort_valid} != 2'b00);
          assign _zz_IBusSimplePlugin_jump_pcLoad_payload_1 = (_zz_IBusSimplePlugin_jump_pcLoad_payload & (~ _zz_IBusSimplePlugin_jump_pcLoad_payload_2));
          assign _zz_IBusSimplePlugin_jump_pcLoad_payload_2 = (_zz_IBusSimplePlugin_jump_pcLoad_payload - 2'b01);
          assign _zz_IBusSimplePlugin_fetchPc_pc_1 = {IBusSimplePlugin_fetchPc_inc,2'b00};
          assign _zz_IBusSimplePlugin_fetchPc_pc = {29'd0, _zz_IBusSimplePlugin_fetchPc_pc_1};
          assign _zz_IBusSimplePlugin_pending_next = (IBusSimplePlugin_pending_value + _zz_IBusSimplePlugin_pending_next_1);
          assign _zz_IBusSimplePlugin_pending_next_2 = IBusSimplePlugin_pending_inc;
          assign _zz_IBusSimplePlugin_pending_next_1 = {2'd0, _zz_IBusSimplePlugin_pending_next_2};
          assign _zz_IBusSimplePlugin_pending_next_4 = IBusSimplePlugin_pending_dec;
          assign _zz_IBusSimplePlugin_pending_next_3 = {2'd0, _zz_IBusSimplePlugin_pending_next_4};
          assign _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_1 = (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_valid && (IBusSimplePlugin_rspJoin_rspBuffer_discardCounter != 3'b000));
          assign _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter = {2'd0, _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_1};
          assign _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_3 = IBusSimplePlugin_pending_dec;
          assign _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_2 = {2'd0, _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_3};
          assign _zz_DBusSimplePlugin_memoryExceptionPort_payload_code = (memory_MEMORY_STORE ? 3'b110 : 3'b100);
          assign _zz__zz_execute_REGFILE_WRITE_DATA = execute_SRC_LESS;
          assign _zz__zz_execute_SRC1 = 3'b100;
          assign _zz__zz_execute_SRC1_1 = execute_INSTRUCTION[19 : 15];
          assign _zz__zz_execute_SRC2_2 = {execute_INSTRUCTION[31 : 25],execute_INSTRUCTION[11 : 7]};
          assign _zz_execute_SrcPlugin_addSub = ($signed(_zz_execute_SrcPlugin_addSub_1) + $signed(_zz_execute_SrcPlugin_addSub_4));
          assign _zz_execute_SrcPlugin_addSub_1 = ($signed(_zz_execute_SrcPlugin_addSub_2) + $signed(_zz_execute_SrcPlugin_addSub_3));
          assign _zz_execute_SrcPlugin_addSub_2 = execute_SRC1;
          assign _zz_execute_SrcPlugin_addSub_3 = (execute_SRC_USE_SUB_LESS ? (~ execute_SRC2) : execute_SRC2);
          assign _zz_execute_SrcPlugin_addSub_4 = (execute_SRC_USE_SUB_LESS ? 32'h00000001 : 32'h00000000);
          assign _zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1 = (_zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1_1 >>> 1'd1);
          assign _zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1_1 = {((execute_SHIFT_CTRL == ShiftCtrlEnum_SRA_1) && execute_LightShifterPlugin_shiftInput[31]),execute_LightShifterPlugin_shiftInput};
          assign _zz__zz_execute_BranchPlugin_branch_src2 = {{{execute_INSTRUCTION[31],execute_INSTRUCTION[19 : 12]},execute_INSTRUCTION[20]},execute_INSTRUCTION[30 : 21]};
          assign _zz__zz_execute_BranchPlugin_branch_src2_4 = {{{execute_INSTRUCTION[31],execute_INSTRUCTION[7]},execute_INSTRUCTION[30 : 25]},execute_INSTRUCTION[11 : 8]};
          assign _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1 = (_zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code & (~ _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1_1));
          assign _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1_1 = (_zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code - 2'b01);
          assign _zz_decode_RegFilePlugin_rs1Data = 1'b1;
          assign _zz_decode_RegFilePlugin_rs2Data = 1'b1;
          assign _zz_decode_LEGAL_INSTRUCTION = 32'h0000207f;
          assign _zz_decode_LEGAL_INSTRUCTION_1 = (decode_INSTRUCTION & 32'h0000407f);
          assign _zz_decode_LEGAL_INSTRUCTION_2 = 32'h00004063;
          assign _zz_decode_LEGAL_INSTRUCTION_3 = ((decode_INSTRUCTION & 32'h0000207f) == 32'h00002013);
          assign _zz_decode_LEGAL_INSTRUCTION_4 = ((decode_INSTRUCTION & 32'h0000107f) == 32'h00000013);
          assign _zz_decode_LEGAL_INSTRUCTION_5 = {((decode_INSTRUCTION & 32'h0000603f) == 32'h00000023),{((decode_INSTRUCTION & 32'h0000207f) == 32'h00000003),{((decode_INSTRUCTION & _zz_decode_LEGAL_INSTRUCTION_6) == 32'h00000003),{(_zz_decode_LEGAL_INSTRUCTION_7 == _zz_decode_LEGAL_INSTRUCTION_8),{_zz_decode_LEGAL_INSTRUCTION_9,{_zz_decode_LEGAL_INSTRUCTION_10,_zz_decode_LEGAL_INSTRUCTION_11}}}}}};
          assign _zz_decode_LEGAL_INSTRUCTION_6 = 32'h0000505f;
          assign _zz_decode_LEGAL_INSTRUCTION_7 = (decode_INSTRUCTION & 32'h0000707b);
          assign _zz_decode_LEGAL_INSTRUCTION_8 = 32'h00000063;
          assign _zz_decode_LEGAL_INSTRUCTION_9 = ((decode_INSTRUCTION & 32'h0000607f) == 32'h0000000f);
          assign _zz_decode_LEGAL_INSTRUCTION_10 = ((decode_INSTRUCTION & 32'hfe00007f) == 32'h00000033);
          assign _zz_decode_LEGAL_INSTRUCTION_11 = {((decode_INSTRUCTION & 32'hbe00705f) == 32'h00005013),{((decode_INSTRUCTION & 32'hfe00305f) == 32'h00001013),{((decode_INSTRUCTION & _zz_decode_LEGAL_INSTRUCTION_12) == 32'h00000033),{(_zz_decode_LEGAL_INSTRUCTION_13 == _zz_decode_LEGAL_INSTRUCTION_14),{_zz_decode_LEGAL_INSTRUCTION_15,_zz_decode_LEGAL_INSTRUCTION_16}}}}};
          assign _zz_decode_LEGAL_INSTRUCTION_12 = 32'hbe00707f;
          assign _zz_decode_LEGAL_INSTRUCTION_13 = (decode_INSTRUCTION & 32'hdfffffff);
          assign _zz_decode_LEGAL_INSTRUCTION_14 = 32'h10200073;
          assign _zz_decode_LEGAL_INSTRUCTION_15 = ((decode_INSTRUCTION & 32'hffffffff) == 32'h10500073);
          assign _zz_decode_LEGAL_INSTRUCTION_16 = ((decode_INSTRUCTION & 32'hffffffff) == 32'h00000073);
          assign _zz__zz_decode_IS_CSR = 32'h10403050;
          assign _zz__zz_decode_IS_CSR_1 = ((decode_INSTRUCTION & 32'h00001050) == 32'h00001050);
          assign _zz__zz_decode_IS_CSR_2 = ((decode_INSTRUCTION & 32'h00002050) == 32'h00002050);
          assign _zz__zz_decode_IS_CSR_3 = _zz_decode_IS_CSR_5;
          assign _zz__zz_decode_IS_CSR_4 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_5) == 32'h00000004);
          assign _zz__zz_decode_IS_CSR_6 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_7) == 32'h00000040);
          assign _zz__zz_decode_IS_CSR_8 = (|(_zz__zz_decode_IS_CSR_9 == _zz__zz_decode_IS_CSR_10));
          assign _zz__zz_decode_IS_CSR_11 = (|{_zz__zz_decode_IS_CSR_12,_zz__zz_decode_IS_CSR_14});
          assign _zz__zz_decode_IS_CSR_16 = {(|_zz__zz_decode_IS_CSR_17),{_zz__zz_decode_IS_CSR_22,{_zz__zz_decode_IS_CSR_25,_zz__zz_decode_IS_CSR_27}}};
          assign _zz__zz_decode_IS_CSR_5 = 32'h0000001c;
          assign _zz__zz_decode_IS_CSR_7 = 32'h00000058;
          assign _zz__zz_decode_IS_CSR_9 = (decode_INSTRUCTION & 32'h00007054);
          assign _zz__zz_decode_IS_CSR_10 = 32'h00005010;
          assign _zz__zz_decode_IS_CSR_12 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_13) == 32'h40001010);
          assign _zz__zz_decode_IS_CSR_14 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_15) == 32'h00001010);
          assign _zz__zz_decode_IS_CSR_17 = {(_zz__zz_decode_IS_CSR_18 == _zz__zz_decode_IS_CSR_19),(_zz__zz_decode_IS_CSR_20 == _zz__zz_decode_IS_CSR_21)};
          assign _zz__zz_decode_IS_CSR_22 = (|(_zz__zz_decode_IS_CSR_23 == _zz__zz_decode_IS_CSR_24));
          assign _zz__zz_decode_IS_CSR_25 = (|_zz__zz_decode_IS_CSR_26);
          assign _zz__zz_decode_IS_CSR_27 = {(|_zz__zz_decode_IS_CSR_28),{_zz__zz_decode_IS_CSR_33,{_zz__zz_decode_IS_CSR_36,_zz__zz_decode_IS_CSR_42}}};
          assign _zz__zz_decode_IS_CSR_13 = 32'h40003054;
          assign _zz__zz_decode_IS_CSR_15 = 32'h00007054;
          assign _zz__zz_decode_IS_CSR_18 = (decode_INSTRUCTION & 32'h00000064);
          assign _zz__zz_decode_IS_CSR_19 = 32'h00000024;
          assign _zz__zz_decode_IS_CSR_20 = (decode_INSTRUCTION & 32'h00003054);
          assign _zz__zz_decode_IS_CSR_21 = 32'h00001010;
          assign _zz__zz_decode_IS_CSR_23 = (decode_INSTRUCTION & 32'h00001000);
          assign _zz__zz_decode_IS_CSR_24 = 32'h00001000;
          assign _zz__zz_decode_IS_CSR_26 = ((decode_INSTRUCTION & 32'h00003000) == 32'h00002000);
          assign _zz__zz_decode_IS_CSR_28 = {(_zz__zz_decode_IS_CSR_29 == _zz__zz_decode_IS_CSR_30),(_zz__zz_decode_IS_CSR_31 == _zz__zz_decode_IS_CSR_32)};
          assign _zz__zz_decode_IS_CSR_33 = (|{_zz__zz_decode_IS_CSR_34,_zz__zz_decode_IS_CSR_35});
          assign _zz__zz_decode_IS_CSR_36 = (|{_zz__zz_decode_IS_CSR_37,_zz__zz_decode_IS_CSR_39});
          assign _zz__zz_decode_IS_CSR_42 = {(|_zz__zz_decode_IS_CSR_43),{_zz__zz_decode_IS_CSR_45,{_zz__zz_decode_IS_CSR_48,_zz__zz_decode_IS_CSR_49}}};
          assign _zz__zz_decode_IS_CSR_29 = (decode_INSTRUCTION & 32'h00002010);
          assign _zz__zz_decode_IS_CSR_30 = 32'h00002000;
          assign _zz__zz_decode_IS_CSR_31 = (decode_INSTRUCTION & 32'h00005000);
          assign _zz__zz_decode_IS_CSR_32 = 32'h00001000;
          assign _zz__zz_decode_IS_CSR_34 = ((decode_INSTRUCTION & 32'h00000034) == 32'h00000020);
          assign _zz__zz_decode_IS_CSR_35 = ((decode_INSTRUCTION & 32'h00000064) == 32'h00000020);
          assign _zz__zz_decode_IS_CSR_37 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_38) == 32'h00000040);
          assign _zz__zz_decode_IS_CSR_39 = {_zz_decode_IS_CSR_2,(_zz__zz_decode_IS_CSR_40 == _zz__zz_decode_IS_CSR_41)};
          assign _zz__zz_decode_IS_CSR_43 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_44) == 32'h00000020);
          assign _zz__zz_decode_IS_CSR_45 = (|(_zz__zz_decode_IS_CSR_46 == _zz__zz_decode_IS_CSR_47));
          assign _zz__zz_decode_IS_CSR_48 = (|_zz_decode_IS_CSR_4);
          assign _zz__zz_decode_IS_CSR_49 = {(|_zz__zz_decode_IS_CSR_50),{_zz__zz_decode_IS_CSR_60,{_zz__zz_decode_IS_CSR_63,_zz__zz_decode_IS_CSR_65}}};
          assign _zz__zz_decode_IS_CSR_38 = 32'h00000050;
          assign _zz__zz_decode_IS_CSR_40 = (decode_INSTRUCTION & 32'h00403040);
          assign _zz__zz_decode_IS_CSR_41 = 32'h00000040;
          assign _zz__zz_decode_IS_CSR_44 = 32'h00000020;
          assign _zz__zz_decode_IS_CSR_46 = (decode_INSTRUCTION & 32'h00000010);
          assign _zz__zz_decode_IS_CSR_47 = 32'h00000010;
          assign _zz__zz_decode_IS_CSR_50 = {_zz_decode_IS_CSR_5,{(_zz__zz_decode_IS_CSR_51 == _zz__zz_decode_IS_CSR_52),{_zz__zz_decode_IS_CSR_53,{_zz__zz_decode_IS_CSR_54,_zz__zz_decode_IS_CSR_55}}}};
          assign _zz__zz_decode_IS_CSR_60 = (|{_zz_decode_IS_CSR_3,(_zz__zz_decode_IS_CSR_61 == _zz__zz_decode_IS_CSR_62)});
          assign _zz__zz_decode_IS_CSR_63 = (|{_zz_decode_IS_CSR_3,_zz__zz_decode_IS_CSR_64});
          assign _zz__zz_decode_IS_CSR_65 = {(|{_zz__zz_decode_IS_CSR_66,_zz__zz_decode_IS_CSR_68}),{(|_zz__zz_decode_IS_CSR_70),{_zz__zz_decode_IS_CSR_72,{_zz__zz_decode_IS_CSR_80,_zz__zz_decode_IS_CSR_82}}}};
          assign _zz__zz_decode_IS_CSR_51 = (decode_INSTRUCTION & 32'h00001010);
          assign _zz__zz_decode_IS_CSR_52 = 32'h00001010;
          assign _zz__zz_decode_IS_CSR_53 = ((decode_INSTRUCTION & 32'h00002010) == 32'h00002010);
          assign _zz__zz_decode_IS_CSR_54 = _zz_decode_IS_CSR_4;
          assign _zz__zz_decode_IS_CSR_55 = {(_zz__zz_decode_IS_CSR_56 == _zz__zz_decode_IS_CSR_57),(_zz__zz_decode_IS_CSR_58 == _zz__zz_decode_IS_CSR_59)};
          assign _zz__zz_decode_IS_CSR_61 = (decode_INSTRUCTION & 32'h00000070);
          assign _zz__zz_decode_IS_CSR_62 = 32'h00000020;
          assign _zz__zz_decode_IS_CSR_64 = ((decode_INSTRUCTION & 32'h00000020) == 32'h00000000);
          assign _zz__zz_decode_IS_CSR_66 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_67) == 32'h00006000);
          assign _zz__zz_decode_IS_CSR_68 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_69) == 32'h00004010);
          assign _zz__zz_decode_IS_CSR_70 = ((decode_INSTRUCTION & _zz__zz_decode_IS_CSR_71) == 32'h00002010);
          assign _zz__zz_decode_IS_CSR_72 = (|{_zz__zz_decode_IS_CSR_73,{_zz__zz_decode_IS_CSR_74,_zz__zz_decode_IS_CSR_75}});
          assign _zz__zz_decode_IS_CSR_80 = (|_zz__zz_decode_IS_CSR_81);
          assign _zz__zz_decode_IS_CSR_82 = {(|_zz__zz_decode_IS_CSR_83),{_zz__zz_decode_IS_CSR_88,_zz__zz_decode_IS_CSR_90}};
          assign _zz__zz_decode_IS_CSR_56 = (decode_INSTRUCTION & 32'h0000000c);
          assign _zz__zz_decode_IS_CSR_57 = 32'h00000004;
          assign _zz__zz_decode_IS_CSR_58 = (decode_INSTRUCTION & 32'h00000028);
          assign _zz__zz_decode_IS_CSR_59 = 32'h00000000;
          assign _zz__zz_decode_IS_CSR_67 = 32'h00006004;
          assign _zz__zz_decode_IS_CSR_69 = 32'h00005014;
          assign _zz__zz_decode_IS_CSR_71 = 32'h00006014;
          assign _zz__zz_decode_IS_CSR_73 = ((decode_INSTRUCTION & 32'h00000044) == 32'h00000000);
          assign _zz__zz_decode_IS_CSR_74 = _zz_decode_IS_CSR_2;
          assign _zz__zz_decode_IS_CSR_75 = {(_zz__zz_decode_IS_CSR_76 == _zz__zz_decode_IS_CSR_77),(_zz__zz_decode_IS_CSR_78 == _zz__zz_decode_IS_CSR_79)};
          assign _zz__zz_decode_IS_CSR_81 = ((decode_INSTRUCTION & 32'h00000058) == 32'h00000000);
          assign _zz__zz_decode_IS_CSR_83 = {(_zz__zz_decode_IS_CSR_84 == _zz__zz_decode_IS_CSR_85),{_zz__zz_decode_IS_CSR_86,_zz__zz_decode_IS_CSR_87}};
          assign _zz__zz_decode_IS_CSR_88 = (|{_zz__zz_decode_IS_CSR_89,_zz_decode_IS_CSR_1});
          assign _zz__zz_decode_IS_CSR_90 = (|{_zz__zz_decode_IS_CSR_91,_zz_decode_IS_CSR_1});
          assign _zz__zz_decode_IS_CSR_76 = (decode_INSTRUCTION & 32'h00006004);
          assign _zz__zz_decode_IS_CSR_77 = 32'h00002000;
          assign _zz__zz_decode_IS_CSR_78 = (decode_INSTRUCTION & 32'h00005004);
          assign _zz__zz_decode_IS_CSR_79 = 32'h00001000;
          assign _zz__zz_decode_IS_CSR_84 = (decode_INSTRUCTION & 32'h00000044);
          assign _zz__zz_decode_IS_CSR_85 = 32'h00000040;
          assign _zz__zz_decode_IS_CSR_86 = ((decode_INSTRUCTION & 32'h00002014) == 32'h00002010);
          assign _zz__zz_decode_IS_CSR_87 = ((decode_INSTRUCTION & 32'h40004034) == 32'h40000030);
          assign _zz__zz_decode_IS_CSR_89 = ((decode_INSTRUCTION & 32'h00000014) == 32'h00000004);
          assign _zz__zz_decode_IS_CSR_91 = ((decode_INSTRUCTION & 32'h00000044) == 32'h00000004);
 004341   always @(posedge clk) begin
~004341     if(_zz_decode_RegFilePlugin_rs1Data) begin
 004341       _zz_RegFilePlugin_regFile_port0 <= RegFilePlugin_regFile[decode_RegFilePlugin_regFileReadAddress1];
            end
          end
        
 004341   always @(posedge clk) begin
~004341     if(_zz_decode_RegFilePlugin_rs2Data) begin
 004341       _zz_RegFilePlugin_regFile_port1 <= RegFilePlugin_regFile[decode_RegFilePlugin_regFileReadAddress2];
            end
          end
        
 004341   always @(posedge clk) begin
 003741     if(_zz_1) begin
 000600       RegFilePlugin_regFile[lastStageRegFileWrite_payload_address] <= lastStageRegFileWrite_payload_data;
            end
          end
        
          StreamFifoLowLatency IBusSimplePlugin_rspJoin_rspBuffer_c (
            .io_push_valid         (iBus_rsp_toStream_valid                                       ), //i
            .io_push_ready         (IBusSimplePlugin_rspJoin_rspBuffer_c_io_push_ready            ), //o
            .io_push_payload_error (iBus_rsp_toStream_payload_error                               ), //i
            .io_push_payload_inst  (iBus_rsp_toStream_payload_inst[31:0]                          ), //i
            .io_pop_valid          (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_valid             ), //o
            .io_pop_ready          (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_ready             ), //i
            .io_pop_payload_error  (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_error     ), //o
            .io_pop_payload_inst   (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_inst[31:0]), //o
            .io_flush              (IBusSimplePlugin_rspJoin_rspBuffer_c_io_flush                 ), //i
            .io_occupancy          (IBusSimplePlugin_rspJoin_rspBuffer_c_io_occupancy             ), //o
            .io_availability       (IBusSimplePlugin_rspJoin_rspBuffer_c_io_availability          ), //o
            .clk                   (clk                                                           ), //i
            .reset                 (reset                                                         )  //i
          );
          `ifndef SYNTHESIS
 004342   always @(*) begin
 004342     case(_zz_memory_to_writeBack_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_memory_to_writeBack_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_memory_to_writeBack_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_memory_to_writeBack_ENV_CTRL_string = "ECALL";
%000000       default : _zz_memory_to_writeBack_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_memory_to_writeBack_ENV_CTRL_1)
 004341       EnvCtrlEnum_NONE : _zz_memory_to_writeBack_ENV_CTRL_1_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_memory_to_writeBack_ENV_CTRL_1_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_memory_to_writeBack_ENV_CTRL_1_string = "ECALL";
%000000       default : _zz_memory_to_writeBack_ENV_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_to_memory_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_execute_to_memory_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_execute_to_memory_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_execute_to_memory_ENV_CTRL_string = "ECALL";
%000000       default : _zz_execute_to_memory_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_to_memory_ENV_CTRL_1)
 004341       EnvCtrlEnum_NONE : _zz_execute_to_memory_ENV_CTRL_1_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_execute_to_memory_ENV_CTRL_1_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_execute_to_memory_ENV_CTRL_1_string = "ECALL";
%000000       default : _zz_execute_to_memory_ENV_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : decode_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : decode_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : decode_ENV_CTRL_string = "ECALL";
%000000       default : decode_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_decode_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_decode_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_decode_ENV_CTRL_string = "ECALL";
%000000       default : _zz_decode_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_decode_to_execute_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_decode_to_execute_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_decode_to_execute_ENV_CTRL_string = "ECALL";
%000000       default : _zz_decode_to_execute_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ENV_CTRL_1)
 004341       EnvCtrlEnum_NONE : _zz_decode_to_execute_ENV_CTRL_1_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_decode_to_execute_ENV_CTRL_1_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_decode_to_execute_ENV_CTRL_1_string = "ECALL";
%000000       default : _zz_decode_to_execute_ENV_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_BRANCH_CTRL)
 002975       BranchCtrlEnum_INC : decode_BRANCH_CTRL_string = "INC ";
 001207       BranchCtrlEnum_B : decode_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : decode_BRANCH_CTRL_string = "JAL ";
 000088       BranchCtrlEnum_JALR : decode_BRANCH_CTRL_string = "JALR";
%000000       default : decode_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_BRANCH_CTRL)
 002975       BranchCtrlEnum_INC : _zz_decode_BRANCH_CTRL_string = "INC ";
 001207       BranchCtrlEnum_B : _zz_decode_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_decode_BRANCH_CTRL_string = "JAL ";
 000088       BranchCtrlEnum_JALR : _zz_decode_BRANCH_CTRL_string = "JALR";
%000000       default : _zz_decode_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_BRANCH_CTRL)
 002975       BranchCtrlEnum_INC : _zz_decode_to_execute_BRANCH_CTRL_string = "INC ";
 001207       BranchCtrlEnum_B : _zz_decode_to_execute_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_decode_to_execute_BRANCH_CTRL_string = "JAL ";
 000088       BranchCtrlEnum_JALR : _zz_decode_to_execute_BRANCH_CTRL_string = "JALR";
%000000       default : _zz_decode_to_execute_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_BRANCH_CTRL_1)
 002975       BranchCtrlEnum_INC : _zz_decode_to_execute_BRANCH_CTRL_1_string = "INC ";
 001207       BranchCtrlEnum_B : _zz_decode_to_execute_BRANCH_CTRL_1_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_decode_to_execute_BRANCH_CTRL_1_string = "JAL ";
 000088       BranchCtrlEnum_JALR : _zz_decode_to_execute_BRANCH_CTRL_1_string = "JALR";
%000000       default : _zz_decode_to_execute_BRANCH_CTRL_1_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : decode_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : decode_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : decode_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : decode_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : decode_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_decode_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_decode_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_decode_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_decode_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : _zz_decode_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_decode_to_execute_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_decode_to_execute_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_decode_to_execute_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_decode_to_execute_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : _zz_decode_to_execute_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SHIFT_CTRL_1)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_decode_to_execute_SHIFT_CTRL_1_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_decode_to_execute_SHIFT_CTRL_1_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_decode_to_execute_SHIFT_CTRL_1_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_decode_to_execute_SHIFT_CTRL_1_string = "SRA_1    ";
%000000       default : _zz_decode_to_execute_SHIFT_CTRL_1_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_ALU_BITWISE_CTRL)
 001776       AluBitwiseCtrlEnum_XOR_1 : decode_ALU_BITWISE_CTRL_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : decode_ALU_BITWISE_CTRL_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : decode_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : decode_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_BITWISE_CTRL)
 001776       AluBitwiseCtrlEnum_XOR_1 : _zz_decode_ALU_BITWISE_CTRL_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : _zz_decode_ALU_BITWISE_CTRL_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : _zz_decode_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : _zz_decode_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ALU_BITWISE_CTRL)
 001776       AluBitwiseCtrlEnum_XOR_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : _zz_decode_to_execute_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ALU_BITWISE_CTRL_1)
 001776       AluBitwiseCtrlEnum_XOR_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_1_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_1_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : _zz_decode_to_execute_ALU_BITWISE_CTRL_1_string = "AND_1";
%000000       default : _zz_decode_to_execute_ALU_BITWISE_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_SRC2_CTRL)
 001591       Src2CtrlEnum_RS : decode_SRC2_CTRL_string = "RS ";
 001815       Src2CtrlEnum_IMI : decode_SRC2_CTRL_string = "IMI";
 000449       Src2CtrlEnum_IMS : decode_SRC2_CTRL_string = "IMS";
 000487       Src2CtrlEnum_PC : decode_SRC2_CTRL_string = "PC ";
%000000       default : decode_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC2_CTRL)
 001591       Src2CtrlEnum_RS : _zz_decode_SRC2_CTRL_string = "RS ";
 001815       Src2CtrlEnum_IMI : _zz_decode_SRC2_CTRL_string = "IMI";
 000449       Src2CtrlEnum_IMS : _zz_decode_SRC2_CTRL_string = "IMS";
 000487       Src2CtrlEnum_PC : _zz_decode_SRC2_CTRL_string = "PC ";
%000000       default : _zz_decode_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SRC2_CTRL)
 001591       Src2CtrlEnum_RS : _zz_decode_to_execute_SRC2_CTRL_string = "RS ";
 001815       Src2CtrlEnum_IMI : _zz_decode_to_execute_SRC2_CTRL_string = "IMI";
 000449       Src2CtrlEnum_IMS : _zz_decode_to_execute_SRC2_CTRL_string = "IMS";
 000487       Src2CtrlEnum_PC : _zz_decode_to_execute_SRC2_CTRL_string = "PC ";
%000000       default : _zz_decode_to_execute_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SRC2_CTRL_1)
 001591       Src2CtrlEnum_RS : _zz_decode_to_execute_SRC2_CTRL_1_string = "RS ";
 001815       Src2CtrlEnum_IMI : _zz_decode_to_execute_SRC2_CTRL_1_string = "IMI";
 000449       Src2CtrlEnum_IMS : _zz_decode_to_execute_SRC2_CTRL_1_string = "IMS";
 000487       Src2CtrlEnum_PC : _zz_decode_to_execute_SRC2_CTRL_1_string = "PC ";
%000000       default : _zz_decode_to_execute_SRC2_CTRL_1_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : decode_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : decode_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : decode_ALU_CTRL_string = "BITWISE ";
%000000       default : decode_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : _zz_decode_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_decode_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_decode_ALU_CTRL_string = "BITWISE ";
%000000       default : _zz_decode_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : _zz_decode_to_execute_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_decode_to_execute_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_decode_to_execute_ALU_CTRL_string = "BITWISE ";
%000000       default : _zz_decode_to_execute_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_ALU_CTRL_1)
 004243       AluCtrlEnum_ADD_SUB : _zz_decode_to_execute_ALU_CTRL_1_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_decode_to_execute_ALU_CTRL_1_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_decode_to_execute_ALU_CTRL_1_string = "BITWISE ";
%000000       default : _zz_decode_to_execute_ALU_CTRL_1_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_SRC1_CTRL)
 003855       Src1CtrlEnum_RS : decode_SRC1_CTRL_string = "RS          ";
 000327       Src1CtrlEnum_IMU : decode_SRC1_CTRL_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : decode_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : decode_SRC1_CTRL_string = "URS1        ";
%000000       default : decode_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC1_CTRL)
 003855       Src1CtrlEnum_RS : _zz_decode_SRC1_CTRL_string = "RS          ";
 000327       Src1CtrlEnum_IMU : _zz_decode_SRC1_CTRL_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : _zz_decode_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_decode_SRC1_CTRL_string = "URS1        ";
%000000       default : _zz_decode_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SRC1_CTRL)
 003855       Src1CtrlEnum_RS : _zz_decode_to_execute_SRC1_CTRL_string = "RS          ";
 000327       Src1CtrlEnum_IMU : _zz_decode_to_execute_SRC1_CTRL_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : _zz_decode_to_execute_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_decode_to_execute_SRC1_CTRL_string = "URS1        ";
%000000       default : _zz_decode_to_execute_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_to_execute_SRC1_CTRL_1)
 003855       Src1CtrlEnum_RS : _zz_decode_to_execute_SRC1_CTRL_1_string = "RS          ";
 000327       Src1CtrlEnum_IMU : _zz_decode_to_execute_SRC1_CTRL_1_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : _zz_decode_to_execute_SRC1_CTRL_1_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_decode_to_execute_SRC1_CTRL_1_string = "URS1        ";
%000000       default : _zz_decode_to_execute_SRC1_CTRL_1_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(memory_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : memory_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : memory_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : memory_ENV_CTRL_string = "ECALL";
%000000       default : memory_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_memory_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_memory_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_memory_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_memory_ENV_CTRL_string = "ECALL";
%000000       default : _zz_memory_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : execute_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : execute_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : execute_ENV_CTRL_string = "ECALL";
%000000       default : execute_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_execute_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_execute_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_execute_ENV_CTRL_string = "ECALL";
%000000       default : _zz_execute_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(writeBack_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : writeBack_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : writeBack_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : writeBack_ENV_CTRL_string = "ECALL";
%000000       default : writeBack_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_writeBack_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : _zz_writeBack_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_writeBack_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_writeBack_ENV_CTRL_string = "ECALL";
%000000       default : _zz_writeBack_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_BRANCH_CTRL)
 003035       BranchCtrlEnum_INC : execute_BRANCH_CTRL_string = "INC ";
 001148       BranchCtrlEnum_B : execute_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : execute_BRANCH_CTRL_string = "JAL ";
 000087       BranchCtrlEnum_JALR : execute_BRANCH_CTRL_string = "JALR";
%000000       default : execute_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_BRANCH_CTRL)
 003035       BranchCtrlEnum_INC : _zz_execute_BRANCH_CTRL_string = "INC ";
 001148       BranchCtrlEnum_B : _zz_execute_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_execute_BRANCH_CTRL_string = "JAL ";
 000087       BranchCtrlEnum_JALR : _zz_execute_BRANCH_CTRL_string = "JALR";
%000000       default : _zz_execute_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : execute_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : execute_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : execute_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : execute_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : execute_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_execute_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_execute_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_execute_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_execute_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : _zz_execute_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_SRC2_CTRL)
 001565       Src2CtrlEnum_RS : execute_SRC2_CTRL_string = "RS ";
 001842       Src2CtrlEnum_IMI : execute_SRC2_CTRL_string = "IMI";
 000451       Src2CtrlEnum_IMS : execute_SRC2_CTRL_string = "IMS";
 000484       Src2CtrlEnum_PC : execute_SRC2_CTRL_string = "PC ";
%000000       default : execute_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_SRC2_CTRL)
 001565       Src2CtrlEnum_RS : _zz_execute_SRC2_CTRL_string = "RS ";
 001842       Src2CtrlEnum_IMI : _zz_execute_SRC2_CTRL_string = "IMI";
 000451       Src2CtrlEnum_IMS : _zz_execute_SRC2_CTRL_string = "IMS";
 000484       Src2CtrlEnum_PC : _zz_execute_SRC2_CTRL_string = "PC ";
%000000       default : _zz_execute_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_SRC1_CTRL)
 003858       Src1CtrlEnum_RS : execute_SRC1_CTRL_string = "RS          ";
 000325       Src1CtrlEnum_IMU : execute_SRC1_CTRL_string = "IMU         ";
 000159       Src1CtrlEnum_PC_INCREMENT : execute_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : execute_SRC1_CTRL_string = "URS1        ";
%000000       default : execute_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_SRC1_CTRL)
 003858       Src1CtrlEnum_RS : _zz_execute_SRC1_CTRL_string = "RS          ";
 000325       Src1CtrlEnum_IMU : _zz_execute_SRC1_CTRL_string = "IMU         ";
 000159       Src1CtrlEnum_PC_INCREMENT : _zz_execute_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_execute_SRC1_CTRL_string = "URS1        ";
%000000       default : _zz_execute_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : execute_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : execute_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : execute_ALU_CTRL_string = "BITWISE ";
%000000       default : execute_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : _zz_execute_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_execute_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_execute_ALU_CTRL_string = "BITWISE ";
%000000       default : _zz_execute_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_ALU_BITWISE_CTRL)
 001806       AluBitwiseCtrlEnum_XOR_1 : execute_ALU_BITWISE_CTRL_string = "XOR_1";
 001133       AluBitwiseCtrlEnum_OR_1 : execute_ALU_BITWISE_CTRL_string = "OR_1 ";
 001403       AluBitwiseCtrlEnum_AND_1 : execute_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : execute_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_execute_ALU_BITWISE_CTRL)
 001806       AluBitwiseCtrlEnum_XOR_1 : _zz_execute_ALU_BITWISE_CTRL_string = "XOR_1";
 001133       AluBitwiseCtrlEnum_OR_1 : _zz_execute_ALU_BITWISE_CTRL_string = "OR_1 ";
 001403       AluBitwiseCtrlEnum_AND_1 : _zz_execute_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : _zz_execute_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ENV_CTRL_1)
 004341       EnvCtrlEnum_NONE : _zz_decode_ENV_CTRL_1_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_decode_ENV_CTRL_1_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_decode_ENV_CTRL_1_string = "ECALL";
%000000       default : _zz_decode_ENV_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_BRANCH_CTRL_1)
 002975       BranchCtrlEnum_INC : _zz_decode_BRANCH_CTRL_1_string = "INC ";
 001207       BranchCtrlEnum_B : _zz_decode_BRANCH_CTRL_1_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_decode_BRANCH_CTRL_1_string = "JAL ";
 000088       BranchCtrlEnum_JALR : _zz_decode_BRANCH_CTRL_1_string = "JALR";
%000000       default : _zz_decode_BRANCH_CTRL_1_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SHIFT_CTRL_1)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_decode_SHIFT_CTRL_1_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_decode_SHIFT_CTRL_1_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_decode_SHIFT_CTRL_1_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_decode_SHIFT_CTRL_1_string = "SRA_1    ";
%000000       default : _zz_decode_SHIFT_CTRL_1_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_BITWISE_CTRL_1)
 001776       AluBitwiseCtrlEnum_XOR_1 : _zz_decode_ALU_BITWISE_CTRL_1_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : _zz_decode_ALU_BITWISE_CTRL_1_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : _zz_decode_ALU_BITWISE_CTRL_1_string = "AND_1";
%000000       default : _zz_decode_ALU_BITWISE_CTRL_1_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC2_CTRL_1)
 001591       Src2CtrlEnum_RS : _zz_decode_SRC2_CTRL_1_string = "RS ";
 001815       Src2CtrlEnum_IMI : _zz_decode_SRC2_CTRL_1_string = "IMI";
 000449       Src2CtrlEnum_IMS : _zz_decode_SRC2_CTRL_1_string = "IMS";
 000487       Src2CtrlEnum_PC : _zz_decode_SRC2_CTRL_1_string = "PC ";
%000000       default : _zz_decode_SRC2_CTRL_1_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_CTRL_1)
 004243       AluCtrlEnum_ADD_SUB : _zz_decode_ALU_CTRL_1_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_decode_ALU_CTRL_1_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_decode_ALU_CTRL_1_string = "BITWISE ";
%000000       default : _zz_decode_ALU_CTRL_1_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC1_CTRL_1)
 003855       Src1CtrlEnum_RS : _zz_decode_SRC1_CTRL_1_string = "RS          ";
 000327       Src1CtrlEnum_IMU : _zz_decode_SRC1_CTRL_1_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : _zz_decode_SRC1_CTRL_1_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_decode_SRC1_CTRL_1_string = "URS1        ";
%000000       default : _zz_decode_SRC1_CTRL_1_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC1_CTRL_2)
 003855       Src1CtrlEnum_RS : _zz_decode_SRC1_CTRL_2_string = "RS          ";
 000327       Src1CtrlEnum_IMU : _zz_decode_SRC1_CTRL_2_string = "IMU         ";
 000160       Src1CtrlEnum_PC_INCREMENT : _zz_decode_SRC1_CTRL_2_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : _zz_decode_SRC1_CTRL_2_string = "URS1        ";
%000000       default : _zz_decode_SRC1_CTRL_2_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_CTRL_2)
 004243       AluCtrlEnum_ADD_SUB : _zz_decode_ALU_CTRL_2_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : _zz_decode_ALU_CTRL_2_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : _zz_decode_ALU_CTRL_2_string = "BITWISE ";
%000000       default : _zz_decode_ALU_CTRL_2_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SRC2_CTRL_2)
 001591       Src2CtrlEnum_RS : _zz_decode_SRC2_CTRL_2_string = "RS ";
 001815       Src2CtrlEnum_IMI : _zz_decode_SRC2_CTRL_2_string = "IMI";
 000449       Src2CtrlEnum_IMS : _zz_decode_SRC2_CTRL_2_string = "IMS";
 000487       Src2CtrlEnum_PC : _zz_decode_SRC2_CTRL_2_string = "PC ";
%000000       default : _zz_decode_SRC2_CTRL_2_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ALU_BITWISE_CTRL_2)
 001776       AluBitwiseCtrlEnum_XOR_1 : _zz_decode_ALU_BITWISE_CTRL_2_string = "XOR_1";
 001104       AluBitwiseCtrlEnum_OR_1 : _zz_decode_ALU_BITWISE_CTRL_2_string = "OR_1 ";
 001462       AluBitwiseCtrlEnum_AND_1 : _zz_decode_ALU_BITWISE_CTRL_2_string = "AND_1";
%000000       default : _zz_decode_ALU_BITWISE_CTRL_2_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_SHIFT_CTRL_2)
 004150       ShiftCtrlEnum_DISABLE_1 : _zz_decode_SHIFT_CTRL_2_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : _zz_decode_SHIFT_CTRL_2_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : _zz_decode_SHIFT_CTRL_2_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : _zz_decode_SHIFT_CTRL_2_string = "SRA_1    ";
%000000       default : _zz_decode_SHIFT_CTRL_2_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_BRANCH_CTRL_2)
 002975       BranchCtrlEnum_INC : _zz_decode_BRANCH_CTRL_2_string = "INC ";
 001207       BranchCtrlEnum_B : _zz_decode_BRANCH_CTRL_2_string = "B   ";
 000072       BranchCtrlEnum_JAL : _zz_decode_BRANCH_CTRL_2_string = "JAL ";
 000088       BranchCtrlEnum_JALR : _zz_decode_BRANCH_CTRL_2_string = "JALR";
%000000       default : _zz_decode_BRANCH_CTRL_2_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(_zz_decode_ENV_CTRL_2)
 004341       EnvCtrlEnum_NONE : _zz_decode_ENV_CTRL_2_string = "NONE ";
 000001       EnvCtrlEnum_XRET : _zz_decode_ENV_CTRL_2_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : _zz_decode_ENV_CTRL_2_string = "ECALL";
%000000       default : _zz_decode_ENV_CTRL_2_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_SRC1_CTRL)
 003858       Src1CtrlEnum_RS : decode_to_execute_SRC1_CTRL_string = "RS          ";
 000325       Src1CtrlEnum_IMU : decode_to_execute_SRC1_CTRL_string = "IMU         ";
 000159       Src1CtrlEnum_PC_INCREMENT : decode_to_execute_SRC1_CTRL_string = "PC_INCREMENT";
%000000       Src1CtrlEnum_URS1 : decode_to_execute_SRC1_CTRL_string = "URS1        ";
%000000       default : decode_to_execute_SRC1_CTRL_string = "????????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_ALU_CTRL)
 004243       AluCtrlEnum_ADD_SUB : decode_to_execute_ALU_CTRL_string = "ADD_SUB ";
 000014       AluCtrlEnum_SLT_SLTU : decode_to_execute_ALU_CTRL_string = "SLT_SLTU";
 000085       AluCtrlEnum_BITWISE : decode_to_execute_ALU_CTRL_string = "BITWISE ";
%000000       default : decode_to_execute_ALU_CTRL_string = "????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_SRC2_CTRL)
 001565       Src2CtrlEnum_RS : decode_to_execute_SRC2_CTRL_string = "RS ";
 001842       Src2CtrlEnum_IMI : decode_to_execute_SRC2_CTRL_string = "IMI";
 000451       Src2CtrlEnum_IMS : decode_to_execute_SRC2_CTRL_string = "IMS";
 000484       Src2CtrlEnum_PC : decode_to_execute_SRC2_CTRL_string = "PC ";
%000000       default : decode_to_execute_SRC2_CTRL_string = "???";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_ALU_BITWISE_CTRL)
 001806       AluBitwiseCtrlEnum_XOR_1 : decode_to_execute_ALU_BITWISE_CTRL_string = "XOR_1";
 001133       AluBitwiseCtrlEnum_OR_1 : decode_to_execute_ALU_BITWISE_CTRL_string = "OR_1 ";
 001403       AluBitwiseCtrlEnum_AND_1 : decode_to_execute_ALU_BITWISE_CTRL_string = "AND_1";
%000000       default : decode_to_execute_ALU_BITWISE_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_SHIFT_CTRL)
 004150       ShiftCtrlEnum_DISABLE_1 : decode_to_execute_SHIFT_CTRL_string = "DISABLE_1";
 000192       ShiftCtrlEnum_SLL_1 : decode_to_execute_SHIFT_CTRL_string = "SLL_1    ";
%000000       ShiftCtrlEnum_SRL_1 : decode_to_execute_SHIFT_CTRL_string = "SRL_1    ";
%000000       ShiftCtrlEnum_SRA_1 : decode_to_execute_SHIFT_CTRL_string = "SRA_1    ";
%000000       default : decode_to_execute_SHIFT_CTRL_string = "?????????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_BRANCH_CTRL)
 003035       BranchCtrlEnum_INC : decode_to_execute_BRANCH_CTRL_string = "INC ";
 001148       BranchCtrlEnum_B : decode_to_execute_BRANCH_CTRL_string = "B   ";
 000072       BranchCtrlEnum_JAL : decode_to_execute_BRANCH_CTRL_string = "JAL ";
 000087       BranchCtrlEnum_JALR : decode_to_execute_BRANCH_CTRL_string = "JALR";
%000000       default : decode_to_execute_BRANCH_CTRL_string = "????";
            endcase
          end
 004342   always @(*) begin
 004342     case(decode_to_execute_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : decode_to_execute_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : decode_to_execute_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : decode_to_execute_ENV_CTRL_string = "ECALL";
%000000       default : decode_to_execute_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(execute_to_memory_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : execute_to_memory_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : execute_to_memory_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : execute_to_memory_ENV_CTRL_string = "ECALL";
%000000       default : execute_to_memory_ENV_CTRL_string = "?????";
            endcase
          end
 004342   always @(*) begin
 004342     case(memory_to_writeBack_ENV_CTRL)
 004341       EnvCtrlEnum_NONE : memory_to_writeBack_ENV_CTRL_string = "NONE ";
 000001       EnvCtrlEnum_XRET : memory_to_writeBack_ENV_CTRL_string = "XRET ";
%000000       EnvCtrlEnum_ECALL : memory_to_writeBack_ENV_CTRL_string = "ECALL";
%000000       default : memory_to_writeBack_ENV_CTRL_string = "?????";
            endcase
          end
          `endif
        
          assign memory_MEMORY_READ_DATA = dBus_rsp_data;
          assign execute_BRANCH_CALC = {execute_BranchPlugin_branchAdder[31 : 1],1'b0};
          assign execute_BRANCH_DO = _zz_execute_BRANCH_DO_1;
          assign writeBack_REGFILE_WRITE_DATA = memory_to_writeBack_REGFILE_WRITE_DATA;
          assign execute_REGFILE_WRITE_DATA = _zz_execute_REGFILE_WRITE_DATA;
          assign memory_MEMORY_ADDRESS_LOW = execute_to_memory_MEMORY_ADDRESS_LOW;
          assign execute_MEMORY_ADDRESS_LOW = dBus_cmd_payload_address[1 : 0];
          assign decode_CSR_READ_OPCODE = (decode_INSTRUCTION[13 : 7] != 7'h20);
          assign decode_CSR_WRITE_OPCODE = (! (((decode_INSTRUCTION[14 : 13] == 2'b01) && (decode_INSTRUCTION[19 : 15] == 5'h00)) || ((decode_INSTRUCTION[14 : 13] == 2'b11) && (decode_INSTRUCTION[19 : 15] == 5'h00))));
          assign decode_SRC2_FORCE_ZERO = (decode_SRC_ADD_ZERO && (! decode_SRC_USE_SUB_LESS));
          assign decode_RS2 = decode_RegFilePlugin_rs2Data;
          assign decode_RS1 = decode_RegFilePlugin_rs1Data;
          assign _zz_memory_to_writeBack_ENV_CTRL = _zz_memory_to_writeBack_ENV_CTRL_1;
          assign _zz_execute_to_memory_ENV_CTRL = _zz_execute_to_memory_ENV_CTRL_1;
          assign decode_ENV_CTRL = _zz_decode_ENV_CTRL;
          assign _zz_decode_to_execute_ENV_CTRL = _zz_decode_to_execute_ENV_CTRL_1;
          assign decode_IS_CSR = _zz_decode_IS_CSR[23];
          assign decode_BRANCH_CTRL = _zz_decode_BRANCH_CTRL;
          assign _zz_decode_to_execute_BRANCH_CTRL = _zz_decode_to_execute_BRANCH_CTRL_1;
          assign decode_SHIFT_CTRL = _zz_decode_SHIFT_CTRL;
          assign _zz_decode_to_execute_SHIFT_CTRL = _zz_decode_to_execute_SHIFT_CTRL_1;
          assign decode_ALU_BITWISE_CTRL = _zz_decode_ALU_BITWISE_CTRL;
          assign _zz_decode_to_execute_ALU_BITWISE_CTRL = _zz_decode_to_execute_ALU_BITWISE_CTRL_1;
          assign decode_SRC_LESS_UNSIGNED = _zz_decode_IS_CSR[15];
          assign decode_MEMORY_STORE = _zz_decode_IS_CSR[12];
          assign execute_BYPASSABLE_MEMORY_STAGE = decode_to_execute_BYPASSABLE_MEMORY_STAGE;
          assign decode_BYPASSABLE_MEMORY_STAGE = _zz_decode_IS_CSR[11];
          assign decode_BYPASSABLE_EXECUTE_STAGE = _zz_decode_IS_CSR[10];
          assign decode_SRC2_CTRL = _zz_decode_SRC2_CTRL;
          assign _zz_decode_to_execute_SRC2_CTRL = _zz_decode_to_execute_SRC2_CTRL_1;
          assign decode_ALU_CTRL = _zz_decode_ALU_CTRL;
          assign _zz_decode_to_execute_ALU_CTRL = _zz_decode_to_execute_ALU_CTRL_1;
          assign decode_MEMORY_ENABLE = _zz_decode_IS_CSR[3];
          assign decode_SRC1_CTRL = _zz_decode_SRC1_CTRL;
          assign _zz_decode_to_execute_SRC1_CTRL = _zz_decode_to_execute_SRC1_CTRL_1;
          assign writeBack_FORMAL_PC_NEXT = memory_to_writeBack_FORMAL_PC_NEXT;
          assign memory_FORMAL_PC_NEXT = execute_to_memory_FORMAL_PC_NEXT;
          assign execute_FORMAL_PC_NEXT = decode_to_execute_FORMAL_PC_NEXT;
          assign decode_FORMAL_PC_NEXT = (decode_PC + 32'h00000004);
          assign memory_PC = execute_to_memory_PC;
          assign execute_CSR_READ_OPCODE = decode_to_execute_CSR_READ_OPCODE;
          assign execute_CSR_WRITE_OPCODE = decode_to_execute_CSR_WRITE_OPCODE;
          assign execute_IS_CSR = decode_to_execute_IS_CSR;
          assign memory_ENV_CTRL = _zz_memory_ENV_CTRL;
          assign execute_ENV_CTRL = _zz_execute_ENV_CTRL;
          assign writeBack_ENV_CTRL = _zz_writeBack_ENV_CTRL;
          assign memory_BRANCH_CALC = execute_to_memory_BRANCH_CALC;
          assign memory_BRANCH_DO = execute_to_memory_BRANCH_DO;
          assign execute_PC = decode_to_execute_PC;
          assign execute_RS1 = decode_to_execute_RS1;
          assign execute_BRANCH_CTRL = _zz_execute_BRANCH_CTRL;
          assign decode_RS2_USE = _zz_decode_IS_CSR[14];
          assign decode_RS1_USE = _zz_decode_IS_CSR[4];
          assign execute_REGFILE_WRITE_VALID = decode_to_execute_REGFILE_WRITE_VALID;
          assign execute_BYPASSABLE_EXECUTE_STAGE = decode_to_execute_BYPASSABLE_EXECUTE_STAGE;
          assign memory_REGFILE_WRITE_VALID = execute_to_memory_REGFILE_WRITE_VALID;
          assign memory_INSTRUCTION = execute_to_memory_INSTRUCTION;
          assign memory_BYPASSABLE_MEMORY_STAGE = execute_to_memory_BYPASSABLE_MEMORY_STAGE;
          assign writeBack_REGFILE_WRITE_VALID = memory_to_writeBack_REGFILE_WRITE_VALID;
 004342   always @(*) begin
 004342     _zz_execute_to_memory_REGFILE_WRITE_DATA = execute_REGFILE_WRITE_DATA;
 004214     if(when_ShiftPlugins_l169) begin
 000128       _zz_execute_to_memory_REGFILE_WRITE_DATA = _zz_execute_to_memory_REGFILE_WRITE_DATA_1;
            end
 004337     if(when_CsrPlugin_l1587) begin
 000005       _zz_execute_to_memory_REGFILE_WRITE_DATA = CsrPlugin_csrMapping_readDataSignal;
            end
          end
        
          assign execute_SHIFT_CTRL = _zz_execute_SHIFT_CTRL;
          assign execute_SRC_LESS_UNSIGNED = decode_to_execute_SRC_LESS_UNSIGNED;
          assign execute_SRC2_FORCE_ZERO = decode_to_execute_SRC2_FORCE_ZERO;
          assign execute_SRC_USE_SUB_LESS = decode_to_execute_SRC_USE_SUB_LESS;
          assign _zz_execute_to_memory_PC = execute_PC;
          assign execute_SRC2_CTRL = _zz_execute_SRC2_CTRL;
          assign execute_SRC1_CTRL = _zz_execute_SRC1_CTRL;
          assign decode_SRC_USE_SUB_LESS = _zz_decode_IS_CSR[2];
          assign decode_SRC_ADD_ZERO = _zz_decode_IS_CSR[18];
          assign execute_SRC_ADD_SUB = execute_SrcPlugin_addSub;
          assign execute_SRC_LESS = execute_SrcPlugin_less;
          assign execute_ALU_CTRL = _zz_execute_ALU_CTRL;
          assign execute_SRC2 = _zz_execute_SRC2_4;
          assign execute_SRC1 = _zz_execute_SRC1;
          assign execute_ALU_BITWISE_CTRL = _zz_execute_ALU_BITWISE_CTRL;
          assign _zz_lastStageRegFileWrite_payload_address = writeBack_INSTRUCTION;
          assign _zz_lastStageRegFileWrite_valid = writeBack_REGFILE_WRITE_VALID;
 013024   always @(*) begin
 013024     _zz_1 = 1'b0;
 011224     if(lastStageRegFileWrite_valid) begin
 001800       _zz_1 = 1'b1;
            end
          end
        
          assign decode_INSTRUCTION_ANTICIPATED = (decode_arbitration_isStuck ? decode_INSTRUCTION : IBusSimplePlugin_iBusRsp_output_payload_rsp_inst);
 004342   always @(*) begin
 004342     decode_REGFILE_WRITE_VALID = _zz_decode_IS_CSR[9];
 003778     if(when_RegFilePlugin_l63) begin
 000564       decode_REGFILE_WRITE_VALID = 1'b0;
            end
          end
        
          assign decode_LEGAL_INSTRUCTION = (|{((decode_INSTRUCTION & 32'h0000005f) == 32'h00000017),{((decode_INSTRUCTION & 32'h0000007f) == 32'h0000006f),{((decode_INSTRUCTION & 32'h0000107f) == 32'h00001073),{((decode_INSTRUCTION & _zz_decode_LEGAL_INSTRUCTION) == 32'h00002073),{(_zz_decode_LEGAL_INSTRUCTION_1 == _zz_decode_LEGAL_INSTRUCTION_2),{_zz_decode_LEGAL_INSTRUCTION_3,{_zz_decode_LEGAL_INSTRUCTION_4,_zz_decode_LEGAL_INSTRUCTION_5}}}}}}});
 004342   always @(*) begin
 004342     _zz_lastStageRegFileWrite_payload_data = writeBack_REGFILE_WRITE_DATA;
 004118     if(when_DBusSimplePlugin_l566) begin
 000224       _zz_lastStageRegFileWrite_payload_data = writeBack_DBusSimplePlugin_rspFormated;
            end
          end
        
          assign writeBack_MEMORY_ENABLE = memory_to_writeBack_MEMORY_ENABLE;
          assign writeBack_MEMORY_ADDRESS_LOW = memory_to_writeBack_MEMORY_ADDRESS_LOW;
          assign writeBack_MEMORY_READ_DATA = memory_to_writeBack_MEMORY_READ_DATA;
          assign memory_ALIGNEMENT_FAULT = execute_to_memory_ALIGNEMENT_FAULT;
          assign memory_REGFILE_WRITE_DATA = execute_to_memory_REGFILE_WRITE_DATA;
          assign memory_MEMORY_STORE = execute_to_memory_MEMORY_STORE;
          assign memory_MEMORY_ENABLE = execute_to_memory_MEMORY_ENABLE;
          assign execute_SRC_ADD = execute_SrcPlugin_addSub;
          assign execute_RS2 = decode_to_execute_RS2;
          assign execute_INSTRUCTION = decode_to_execute_INSTRUCTION;
          assign execute_MEMORY_STORE = decode_to_execute_MEMORY_STORE;
          assign execute_MEMORY_ENABLE = decode_to_execute_MEMORY_ENABLE;
          assign execute_ALIGNEMENT_FAULT = (((dBus_cmd_payload_size == 2'b10) && (dBus_cmd_payload_address[1 : 0] != 2'b00)) || ((dBus_cmd_payload_size == 2'b01) && (dBus_cmd_payload_address[0 : 0] != 1'b0)));
 004342   always @(*) begin
 004342     _zz_memory_to_writeBack_FORMAL_PC_NEXT = memory_FORMAL_PC_NEXT;
 004114     if(BranchPlugin_jumpInterface_valid) begin
 000228       _zz_memory_to_writeBack_FORMAL_PC_NEXT = BranchPlugin_jumpInterface_payload;
            end
          end
        
          assign decode_PC = IBusSimplePlugin_injector_decodeInput_payload_pc;
          assign decode_INSTRUCTION = IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
          assign writeBack_PC = memory_to_writeBack_PC;
          assign writeBack_INSTRUCTION = memory_to_writeBack_INSTRUCTION;
          assign decode_arbitration_haltItself = 1'b0;
 004342   always @(*) begin
 004342     decode_arbitration_haltByOther = 1'b0;
 002946     if(when_HazardSimplePlugin_l113) begin
 001396       decode_arbitration_haltByOther = 1'b1;
            end
 004338     if(CsrPlugin_pipelineLiberator_active) begin
 000004       decode_arbitration_haltByOther = 1'b1;
            end
 004339     if(when_CsrPlugin_l1527) begin
 000003       decode_arbitration_haltByOther = 1'b1;
            end
          end
        
 013024   always @(*) begin
 013024     decode_arbitration_removeIt = 1'b0;
 013021     if(decodeExceptionPort_valid) begin
 000003       decode_arbitration_removeIt = 1'b1;
            end
 012334     if(decode_arbitration_isFlushed) begin
 000690       decode_arbitration_removeIt = 1'b1;
            end
          end
        
          assign decode_arbitration_flushIt = 1'b0;
 004342   always @(*) begin
 004342     decode_arbitration_flushNext = 1'b0;
 004341     if(decodeExceptionPort_valid) begin
 000001       decode_arbitration_flushNext = 1'b1;
            end
          end
        
 004342   always @(*) begin
 004342     execute_arbitration_haltItself = 1'b0;
 004266     if(when_DBusSimplePlugin_l436) begin
 000076       execute_arbitration_haltItself = 1'b1;
            end
 004214     if(when_ShiftPlugins_l169) begin
 000064       if(when_ShiftPlugins_l184) begin
 000064         execute_arbitration_haltItself = 1'b1;
              end
            end
 004337     if(when_CsrPlugin_l1591) begin
~000005       if(execute_CsrPlugin_blockedBySideEffects) begin
%000000         execute_arbitration_haltItself = 1'b1;
              end
            end
          end
        
          assign execute_arbitration_haltByOther = 1'b0;
 013024   always @(*) begin
 013024     execute_arbitration_removeIt = 1'b0;
~013024     if(CsrPlugin_selfException_valid) begin
%000000       execute_arbitration_removeIt = 1'b1;
            end
 012334     if(execute_arbitration_isFlushed) begin
 000690       execute_arbitration_removeIt = 1'b1;
            end
          end
        
          assign execute_arbitration_flushIt = 1'b0;
 004342   always @(*) begin
 004342     execute_arbitration_flushNext = 1'b0;
~004342     if(CsrPlugin_selfException_valid) begin
%000000       execute_arbitration_flushNext = 1'b1;
            end
          end
        
 004342   always @(*) begin
 004342     memory_arbitration_haltItself = 1'b0;
 004240     if(when_DBusSimplePlugin_l490) begin
 000102       memory_arbitration_haltItself = 1'b1;
            end
          end
        
          assign memory_arbitration_haltByOther = 1'b0;
 013024   always @(*) begin
 013024     memory_arbitration_removeIt = 1'b0;
~013024     if(_zz_when) begin
%000000       memory_arbitration_removeIt = 1'b1;
            end
 013018     if(memory_arbitration_isFlushed) begin
 000006       memory_arbitration_removeIt = 1'b1;
            end
          end
        
          assign memory_arbitration_flushIt = 1'b0;
 004342   always @(*) begin
 004342     memory_arbitration_flushNext = 1'b0;
 004114     if(BranchPlugin_jumpInterface_valid) begin
 000228       memory_arbitration_flushNext = 1'b1;
            end
~004342     if(_zz_when) begin
%000000       memory_arbitration_flushNext = 1'b1;
            end
          end
        
          assign writeBack_arbitration_haltItself = 1'b0;
          assign writeBack_arbitration_haltByOther = 1'b0;
 000001   always @(*) begin
 000001     writeBack_arbitration_removeIt = 1'b0;
~000001     if(writeBack_arbitration_isFlushed) begin
%000000       writeBack_arbitration_removeIt = 1'b1;
            end
          end
        
          assign writeBack_arbitration_flushIt = 1'b0;
 013024   always @(*) begin
 013024     writeBack_arbitration_flushNext = 1'b0;
 013021     if(when_CsrPlugin_l1390) begin
 000003       writeBack_arbitration_flushNext = 1'b1;
            end
 013021     if(when_CsrPlugin_l1456) begin
 000003       writeBack_arbitration_flushNext = 1'b1;
            end
          end
        
          assign lastStageInstruction = writeBack_INSTRUCTION;
          assign lastStagePc = writeBack_PC;
          assign lastStageIsValid = writeBack_arbitration_isValid;
          assign lastStageIsFiring = writeBack_arbitration_isFiring;
 013024   always @(*) begin
 013024     IBusSimplePlugin_fetcherHalt = 1'b0;
~013024     if(when_CsrPlugin_l1272) begin
%000000       IBusSimplePlugin_fetcherHalt = 1'b1;
            end
 013021     if(when_CsrPlugin_l1390) begin
 000003       IBusSimplePlugin_fetcherHalt = 1'b1;
            end
 013021     if(when_CsrPlugin_l1456) begin
 000003       IBusSimplePlugin_fetcherHalt = 1'b1;
            end
          end
        
          assign IBusSimplePlugin_forceNoDecodeCond = 1'b0;
 004342   always @(*) begin
 004342     IBusSimplePlugin_incomingInstruction = 1'b0;
 004291     if(IBusSimplePlugin_iBusRsp_stages_1_input_valid) begin
 004291       IBusSimplePlugin_incomingInstruction = 1'b1;
            end
 002777     if(IBusSimplePlugin_injector_decodeInput_valid) begin
 002777       IBusSimplePlugin_incomingInstruction = 1'b1;
            end
          end
        
          assign BranchPlugin_inDebugNoFetchFlag = 1'b0;
 004342   always @(*) begin
 004342     CsrPlugin_csrMapping_allowCsrSignal = 1'b0;
~004342     if(when_CsrPlugin_l1702) begin
%000000       CsrPlugin_csrMapping_allowCsrSignal = 1'b1;
            end
~004342     if(when_CsrPlugin_l1709) begin
%000000       CsrPlugin_csrMapping_allowCsrSignal = 1'b1;
            end
          end
        
          assign CsrPlugin_csrMapping_doForceFailCsr = 1'b0;
          assign CsrPlugin_csrMapping_readDataSignal = CsrPlugin_csrMapping_readDataInit;
          assign CsrPlugin_inWfi = 1'b0;
          assign CsrPlugin_thirdPartyWake = 1'b0;
 013024   always @(*) begin
 013024     CsrPlugin_jumpInterface_valid = 1'b0;
 013021     if(when_CsrPlugin_l1390) begin
 000003       CsrPlugin_jumpInterface_valid = 1'b1;
            end
 013021     if(when_CsrPlugin_l1456) begin
 000003       CsrPlugin_jumpInterface_valid = 1'b1;
            end
          end
        
 013024   always @(*) begin
 013024     CsrPlugin_jumpInterface_payload = 32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
 013021     if(when_CsrPlugin_l1390) begin
 000003       CsrPlugin_jumpInterface_payload = {CsrPlugin_xtvec_base,2'b00};
            end
 013021     if(when_CsrPlugin_l1456) begin
 000003       case(switch_CsrPlugin_l1460)
 000003         2'b11 : begin
 000003           CsrPlugin_jumpInterface_payload = CsrPlugin_mepc;
                end
%000000         default : begin
                end
              endcase
            end
          end
        
          assign CsrPlugin_forceMachineWire = 1'b0;
          assign CsrPlugin_allowInterrupts = 1'b1;
          assign CsrPlugin_allowException = 1'b1;
          assign CsrPlugin_allowEbreakException = 1'b1;
          assign CsrPlugin_xretAwayFromMachine = 1'b0;
          assign IBusSimplePlugin_externalFlush = ({writeBack_arbitration_flushNext,{memory_arbitration_flushNext,{execute_arbitration_flushNext,decode_arbitration_flushNext}}} != 4'b0000);
          assign IBusSimplePlugin_jump_pcLoad_valid = ({CsrPlugin_jumpInterface_valid,BranchPlugin_jumpInterface_valid} != 2'b00);
          assign _zz_IBusSimplePlugin_jump_pcLoad_payload = {BranchPlugin_jumpInterface_valid,CsrPlugin_jumpInterface_valid};
          assign IBusSimplePlugin_jump_pcLoad_payload = (_zz_IBusSimplePlugin_jump_pcLoad_payload_1[0] ? CsrPlugin_jumpInterface_payload : BranchPlugin_jumpInterface_payload);
 013024   always @(*) begin
 013024     IBusSimplePlugin_fetchPc_correction = 1'b0;
 012334     if(IBusSimplePlugin_jump_pcLoad_valid) begin
 000690       IBusSimplePlugin_fetchPc_correction = 1'b1;
            end
          end
        
          assign IBusSimplePlugin_fetchPc_output_fire = (IBusSimplePlugin_fetchPc_output_valid && IBusSimplePlugin_fetchPc_output_ready);
          assign IBusSimplePlugin_fetchPc_corrected = (IBusSimplePlugin_fetchPc_correction || IBusSimplePlugin_fetchPc_correctionReg);
 004342   always @(*) begin
 004342     IBusSimplePlugin_fetchPc_pcRegPropagate = 1'b0;
 002743     if(IBusSimplePlugin_iBusRsp_stages_1_input_ready) begin
 001599       IBusSimplePlugin_fetchPc_pcRegPropagate = 1'b1;
            end
          end
        
          assign when_Fetcher_l133 = (IBusSimplePlugin_fetchPc_correction || IBusSimplePlugin_fetchPc_pcRegPropagate);
          assign when_Fetcher_l133_1 = ((! IBusSimplePlugin_fetchPc_output_valid) && IBusSimplePlugin_fetchPc_output_ready);
 013024   always @(*) begin
 013024     IBusSimplePlugin_fetchPc_pc = (IBusSimplePlugin_fetchPc_pcReg + _zz_IBusSimplePlugin_fetchPc_pc);
 012334     if(IBusSimplePlugin_jump_pcLoad_valid) begin
 000690       IBusSimplePlugin_fetchPc_pc = IBusSimplePlugin_jump_pcLoad_payload;
            end
 013024     IBusSimplePlugin_fetchPc_pc[0] = 1'b0;
 013024     IBusSimplePlugin_fetchPc_pc[1] = 1'b0;
          end
        
 013024   always @(*) begin
 013024     IBusSimplePlugin_fetchPc_flushed = 1'b0;
 012334     if(IBusSimplePlugin_jump_pcLoad_valid) begin
 000690       IBusSimplePlugin_fetchPc_flushed = 1'b1;
            end
          end
        
          assign when_Fetcher_l160 = (IBusSimplePlugin_fetchPc_booted && ((IBusSimplePlugin_fetchPc_output_ready || IBusSimplePlugin_fetchPc_correction) || IBusSimplePlugin_fetchPc_pcRegPropagate));
          assign IBusSimplePlugin_fetchPc_output_valid = ((! IBusSimplePlugin_fetcherHalt) && IBusSimplePlugin_fetchPc_booted);
          assign IBusSimplePlugin_fetchPc_output_payload = IBusSimplePlugin_fetchPc_pc;
          assign IBusSimplePlugin_iBusRsp_redoFetch = 1'b0;
          assign IBusSimplePlugin_iBusRsp_stages_0_input_valid = IBusSimplePlugin_fetchPc_output_valid;
          assign IBusSimplePlugin_fetchPc_output_ready = IBusSimplePlugin_iBusRsp_stages_0_input_ready;
          assign IBusSimplePlugin_iBusRsp_stages_0_input_payload = IBusSimplePlugin_fetchPc_output_payload;
 013024   always @(*) begin
 013024     IBusSimplePlugin_iBusRsp_stages_0_halt = 1'b0;
 008223     if(when_IBusSimplePlugin_l305) begin
 008223       IBusSimplePlugin_iBusRsp_stages_0_halt = 1'b1;
            end
          end
        
          assign _zz_IBusSimplePlugin_iBusRsp_stages_0_input_ready = (! IBusSimplePlugin_iBusRsp_stages_0_halt);
          assign IBusSimplePlugin_iBusRsp_stages_0_input_ready = (IBusSimplePlugin_iBusRsp_stages_0_output_ready && _zz_IBusSimplePlugin_iBusRsp_stages_0_input_ready);
          assign IBusSimplePlugin_iBusRsp_stages_0_output_valid = (IBusSimplePlugin_iBusRsp_stages_0_input_valid && _zz_IBusSimplePlugin_iBusRsp_stages_0_input_ready);
          assign IBusSimplePlugin_iBusRsp_stages_0_output_payload = IBusSimplePlugin_iBusRsp_stages_0_input_payload;
          assign IBusSimplePlugin_iBusRsp_stages_1_halt = 1'b0;
          assign _zz_IBusSimplePlugin_iBusRsp_stages_1_input_ready = (! IBusSimplePlugin_iBusRsp_stages_1_halt);
          assign IBusSimplePlugin_iBusRsp_stages_1_input_ready = (IBusSimplePlugin_iBusRsp_stages_1_output_ready && _zz_IBusSimplePlugin_iBusRsp_stages_1_input_ready);
          assign IBusSimplePlugin_iBusRsp_stages_1_output_valid = (IBusSimplePlugin_iBusRsp_stages_1_input_valid && _zz_IBusSimplePlugin_iBusRsp_stages_1_input_ready);
          assign IBusSimplePlugin_iBusRsp_stages_1_output_payload = IBusSimplePlugin_iBusRsp_stages_1_input_payload;
          assign IBusSimplePlugin_iBusRsp_flush = (IBusSimplePlugin_externalFlush || IBusSimplePlugin_iBusRsp_redoFetch);
          assign IBusSimplePlugin_iBusRsp_stages_0_output_ready = _zz_IBusSimplePlugin_iBusRsp_stages_0_output_ready;
          assign _zz_IBusSimplePlugin_iBusRsp_stages_0_output_ready = ((1'b0 && (! _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid)) || IBusSimplePlugin_iBusRsp_stages_1_input_ready);
          assign _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid = _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid_1;
          assign IBusSimplePlugin_iBusRsp_stages_1_input_valid = _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid;
          assign IBusSimplePlugin_iBusRsp_stages_1_input_payload = IBusSimplePlugin_fetchPc_pcReg;
 004342   always @(*) begin
 004342     IBusSimplePlugin_iBusRsp_readyForError = 1'b1;
 002777     if(IBusSimplePlugin_injector_decodeInput_valid) begin
 002777       IBusSimplePlugin_iBusRsp_readyForError = 1'b0;
            end
 004062     if(when_Fetcher_l322) begin
 000280       IBusSimplePlugin_iBusRsp_readyForError = 1'b0;
            end
          end
        
          assign IBusSimplePlugin_iBusRsp_output_ready = ((1'b0 && (! IBusSimplePlugin_injector_decodeInput_valid)) || IBusSimplePlugin_injector_decodeInput_ready);
          assign IBusSimplePlugin_injector_decodeInput_valid = _zz_IBusSimplePlugin_injector_decodeInput_valid;
          assign IBusSimplePlugin_injector_decodeInput_payload_pc = _zz_IBusSimplePlugin_injector_decodeInput_payload_pc;
          assign IBusSimplePlugin_injector_decodeInput_payload_rsp_error = _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_error;
          assign IBusSimplePlugin_injector_decodeInput_payload_rsp_inst = _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_inst;
          assign IBusSimplePlugin_injector_decodeInput_payload_isRvc = _zz_IBusSimplePlugin_injector_decodeInput_payload_isRvc;
          assign when_Fetcher_l322 = (! IBusSimplePlugin_pcValids_0);
          assign when_Fetcher_l331 = (! (! IBusSimplePlugin_iBusRsp_stages_1_input_ready));
          assign when_Fetcher_l331_1 = (! (! IBusSimplePlugin_injector_decodeInput_ready));
          assign when_Fetcher_l331_2 = (! execute_arbitration_isStuck);
          assign when_Fetcher_l331_3 = (! memory_arbitration_isStuck);
          assign when_Fetcher_l331_4 = (! writeBack_arbitration_isStuck);
          assign IBusSimplePlugin_pcValids_0 = IBusSimplePlugin_injector_nextPcCalc_valids_1;
          assign IBusSimplePlugin_pcValids_1 = IBusSimplePlugin_injector_nextPcCalc_valids_2;
          assign IBusSimplePlugin_pcValids_2 = IBusSimplePlugin_injector_nextPcCalc_valids_3;
          assign IBusSimplePlugin_pcValids_3 = IBusSimplePlugin_injector_nextPcCalc_valids_4;
          assign IBusSimplePlugin_injector_decodeInput_ready = (! decode_arbitration_isStuck);
 000001   always @(*) begin
 000001     decode_arbitration_isValid = IBusSimplePlugin_injector_decodeInput_valid;
~000001     if(IBusSimplePlugin_forceNoDecodeCond) begin
%000000       decode_arbitration_isValid = 1'b0;
            end
          end
        
          assign iBus_cmd_valid = IBusSimplePlugin_cmd_valid;
          assign IBusSimplePlugin_cmd_ready = iBus_cmd_ready;
          assign iBus_cmd_payload_pc = IBusSimplePlugin_cmd_payload_pc;
          assign IBusSimplePlugin_pending_next = (_zz_IBusSimplePlugin_pending_next - _zz_IBusSimplePlugin_pending_next_3);
          assign IBusSimplePlugin_cmdFork_canEmit = (IBusSimplePlugin_iBusRsp_stages_0_output_ready && (IBusSimplePlugin_pending_value != 3'b111));
          assign when_IBusSimplePlugin_l305 = (IBusSimplePlugin_iBusRsp_stages_0_input_valid && ((! IBusSimplePlugin_cmdFork_canEmit) || (! IBusSimplePlugin_cmd_ready)));
          assign IBusSimplePlugin_cmd_valid = (IBusSimplePlugin_iBusRsp_stages_0_input_valid && IBusSimplePlugin_cmdFork_canEmit);
          assign IBusSimplePlugin_cmd_fire = (IBusSimplePlugin_cmd_valid && IBusSimplePlugin_cmd_ready);
          assign IBusSimplePlugin_pending_inc = IBusSimplePlugin_cmd_fire;
          assign IBusSimplePlugin_cmd_payload_pc = {IBusSimplePlugin_iBusRsp_stages_0_input_payload[31 : 2],2'b00};
          assign iBus_rsp_toStream_valid = iBus_rsp_valid;
          assign iBus_rsp_toStream_payload_error = iBus_rsp_payload_error;
          assign iBus_rsp_toStream_payload_inst = iBus_rsp_payload_inst;
          assign iBus_rsp_toStream_ready = IBusSimplePlugin_rspJoin_rspBuffer_c_io_push_ready;
          assign IBusSimplePlugin_rspJoin_rspBuffer_flush = ((IBusSimplePlugin_rspJoin_rspBuffer_discardCounter != 3'b000) || IBusSimplePlugin_iBusRsp_flush);
          assign IBusSimplePlugin_rspJoin_rspBuffer_output_valid = (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_valid && (IBusSimplePlugin_rspJoin_rspBuffer_discardCounter == 3'b000));
          assign IBusSimplePlugin_rspJoin_rspBuffer_output_payload_error = IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_error;
          assign IBusSimplePlugin_rspJoin_rspBuffer_output_payload_inst = IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_payload_inst;
          assign IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_ready = (IBusSimplePlugin_rspJoin_rspBuffer_output_ready || IBusSimplePlugin_rspJoin_rspBuffer_flush);
          assign toplevel_IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_fire = (IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_valid && IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_ready);
          assign IBusSimplePlugin_pending_dec = toplevel_IBusSimplePlugin_rspJoin_rspBuffer_c_io_pop_fire;
          assign IBusSimplePlugin_rspJoin_fetchRsp_pc = IBusSimplePlugin_iBusRsp_stages_1_output_payload;
 004342   always @(*) begin
 004342     IBusSimplePlugin_rspJoin_fetchRsp_rsp_error = IBusSimplePlugin_rspJoin_rspBuffer_output_payload_error;
 002699     if(when_IBusSimplePlugin_l376) begin
 001643       IBusSimplePlugin_rspJoin_fetchRsp_rsp_error = 1'b0;
            end
          end
        
          assign IBusSimplePlugin_rspJoin_fetchRsp_rsp_inst = IBusSimplePlugin_rspJoin_rspBuffer_output_payload_inst;
          assign when_IBusSimplePlugin_l376 = (! IBusSimplePlugin_rspJoin_rspBuffer_output_valid);
          assign IBusSimplePlugin_rspJoin_exceptionDetected = 1'b0;
          assign IBusSimplePlugin_rspJoin_join_valid = (IBusSimplePlugin_iBusRsp_stages_1_output_valid && IBusSimplePlugin_rspJoin_rspBuffer_output_valid);
          assign IBusSimplePlugin_rspJoin_join_payload_pc = IBusSimplePlugin_rspJoin_fetchRsp_pc;
          assign IBusSimplePlugin_rspJoin_join_payload_rsp_error = IBusSimplePlugin_rspJoin_fetchRsp_rsp_error;
          assign IBusSimplePlugin_rspJoin_join_payload_rsp_inst = IBusSimplePlugin_rspJoin_fetchRsp_rsp_inst;
          assign IBusSimplePlugin_rspJoin_join_payload_isRvc = IBusSimplePlugin_rspJoin_fetchRsp_isRvc;
          assign IBusSimplePlugin_rspJoin_join_fire = (IBusSimplePlugin_rspJoin_join_valid && IBusSimplePlugin_rspJoin_join_ready);
          assign IBusSimplePlugin_iBusRsp_stages_1_output_ready = (IBusSimplePlugin_iBusRsp_stages_1_output_valid ? IBusSimplePlugin_rspJoin_join_fire : IBusSimplePlugin_rspJoin_join_ready);
          assign IBusSimplePlugin_rspJoin_rspBuffer_output_ready = IBusSimplePlugin_rspJoin_join_fire;
          assign _zz_IBusSimplePlugin_iBusRsp_output_valid = (! IBusSimplePlugin_rspJoin_exceptionDetected);
          assign IBusSimplePlugin_rspJoin_join_ready = (IBusSimplePlugin_iBusRsp_output_ready && _zz_IBusSimplePlugin_iBusRsp_output_valid);
          assign IBusSimplePlugin_iBusRsp_output_valid = (IBusSimplePlugin_rspJoin_join_valid && _zz_IBusSimplePlugin_iBusRsp_output_valid);
          assign IBusSimplePlugin_iBusRsp_output_payload_pc = IBusSimplePlugin_rspJoin_join_payload_pc;
          assign IBusSimplePlugin_iBusRsp_output_payload_rsp_error = IBusSimplePlugin_rspJoin_join_payload_rsp_error;
          assign IBusSimplePlugin_iBusRsp_output_payload_rsp_inst = IBusSimplePlugin_rspJoin_join_payload_rsp_inst;
          assign IBusSimplePlugin_iBusRsp_output_payload_isRvc = IBusSimplePlugin_rspJoin_join_payload_isRvc;
          assign _zz_dBus_cmd_valid = 1'b0;
 004342   always @(*) begin
 004342     execute_DBusSimplePlugin_skipCmd = 1'b0;
 003472     if(execute_ALIGNEMENT_FAULT) begin
 000870       execute_DBusSimplePlugin_skipCmd = 1'b1;
            end
          end
        
          assign dBus_cmd_valid = (((((execute_arbitration_isValid && execute_MEMORY_ENABLE) && (! execute_arbitration_isStuckByOthers)) && (! execute_arbitration_isFlushed)) && (! execute_DBusSimplePlugin_skipCmd)) && (! _zz_dBus_cmd_valid));
          assign dBus_cmd_payload_wr = execute_MEMORY_STORE;
          assign dBus_cmd_payload_size = execute_INSTRUCTION[13 : 12];
 004342   always @(*) begin
 004342     case(dBus_cmd_payload_size)
 001806       2'b00 : begin
 001806         _zz_dBus_cmd_payload_data = {{{execute_RS2[7 : 0],execute_RS2[7 : 0]},execute_RS2[7 : 0]},execute_RS2[7 : 0]};
              end
 001243       2'b01 : begin
 001243         _zz_dBus_cmd_payload_data = {execute_RS2[15 : 0],execute_RS2[15 : 0]};
              end
 001293       default : begin
 001293         _zz_dBus_cmd_payload_data = execute_RS2[31 : 0];
              end
            endcase
          end
        
          assign dBus_cmd_payload_data = _zz_dBus_cmd_payload_data;
          assign when_DBusSimplePlugin_l436 = ((((execute_arbitration_isValid && execute_MEMORY_ENABLE) && (! dBus_cmd_ready)) && (! execute_DBusSimplePlugin_skipCmd)) && (! _zz_dBus_cmd_valid));
 004342   always @(*) begin
 004342     case(dBus_cmd_payload_size)
 001806       2'b00 : begin
 001806         _zz_execute_DBusSimplePlugin_formalMask = 4'b0001;
              end
 001243       2'b01 : begin
 001243         _zz_execute_DBusSimplePlugin_formalMask = 4'b0011;
              end
 001293       default : begin
 001293         _zz_execute_DBusSimplePlugin_formalMask = 4'b1111;
              end
            endcase
          end
        
          assign execute_DBusSimplePlugin_formalMask = (_zz_execute_DBusSimplePlugin_formalMask <<< dBus_cmd_payload_address[1 : 0]);
          assign dBus_cmd_payload_address = execute_SRC_ADD;
          assign when_DBusSimplePlugin_l490 = (((memory_arbitration_isValid && memory_MEMORY_ENABLE) && (! memory_MEMORY_STORE)) && ((! dBus_rsp_ready) || 1'b0));
 004342   always @(*) begin
 004342     DBusSimplePlugin_memoryExceptionPort_valid = 1'b0;
~004342     if(when_DBusSimplePlugin_l497) begin
%000000       DBusSimplePlugin_memoryExceptionPort_valid = 1'b1;
            end
 003476     if(memory_ALIGNEMENT_FAULT) begin
 000866       DBusSimplePlugin_memoryExceptionPort_valid = 1'b1;
            end
 004016     if(when_DBusSimplePlugin_l523) begin
 004016       DBusSimplePlugin_memoryExceptionPort_valid = 1'b0;
            end
          end
        
 004342   always @(*) begin
 004342     DBusSimplePlugin_memoryExceptionPort_payload_code = 4'bxxxx;
~004342     if(when_DBusSimplePlugin_l497) begin
%000000       DBusSimplePlugin_memoryExceptionPort_payload_code = 4'b0101;
            end
 003476     if(memory_ALIGNEMENT_FAULT) begin
 000866       DBusSimplePlugin_memoryExceptionPort_payload_code = {1'd0, _zz_DBusSimplePlugin_memoryExceptionPort_payload_code};
            end
          end
        
          assign DBusSimplePlugin_memoryExceptionPort_payload_badAddr = memory_REGFILE_WRITE_DATA;
          assign when_DBusSimplePlugin_l497 = ((dBus_rsp_ready && dBus_rsp_error) && (! memory_MEMORY_STORE));
          assign when_DBusSimplePlugin_l523 = (! ((memory_arbitration_isValid && memory_MEMORY_ENABLE) && (1'b1 || (! memory_arbitration_isStuckByOthers))));
 004342   always @(*) begin
 004342     writeBack_DBusSimplePlugin_rspShifted = writeBack_MEMORY_READ_DATA;
 004342     case(writeBack_MEMORY_ADDRESS_LOW)
 000739       2'b01 : begin
 000739         writeBack_DBusSimplePlugin_rspShifted[7 : 0] = writeBack_MEMORY_READ_DATA[15 : 8];
              end
 000507       2'b10 : begin
 000507         writeBack_DBusSimplePlugin_rspShifted[15 : 0] = writeBack_MEMORY_READ_DATA[31 : 16];
              end
 000573       2'b11 : begin
 000573         writeBack_DBusSimplePlugin_rspShifted[7 : 0] = writeBack_MEMORY_READ_DATA[31 : 24];
              end
 002523       default : begin
              end
            endcase
          end
        
          assign switch_Misc_l232 = writeBack_INSTRUCTION[13 : 12];
          assign _zz_writeBack_DBusSimplePlugin_rspFormated = (writeBack_DBusSimplePlugin_rspShifted[7] && (! writeBack_INSTRUCTION[14]));
 000001   always @(*) begin
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[31] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[30] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[29] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[28] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[27] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[26] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[25] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[24] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[23] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[22] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[21] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[20] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[19] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[18] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[17] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[16] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[15] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[14] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[13] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[12] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[11] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[10] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[9] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[8] = _zz_writeBack_DBusSimplePlugin_rspFormated;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_1[7 : 0] = writeBack_DBusSimplePlugin_rspShifted[7 : 0];
          end
        
          assign _zz_writeBack_DBusSimplePlugin_rspFormated_2 = (writeBack_DBusSimplePlugin_rspShifted[15] && (! writeBack_INSTRUCTION[14]));
 000001   always @(*) begin
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[31] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[30] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[29] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[28] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[27] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[26] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[25] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[24] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[23] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[22] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[21] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[20] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[19] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[18] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[17] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[16] = _zz_writeBack_DBusSimplePlugin_rspFormated_2;
 000001     _zz_writeBack_DBusSimplePlugin_rspFormated_3[15 : 0] = writeBack_DBusSimplePlugin_rspShifted[15 : 0];
          end
        
 004342   always @(*) begin
 004342     case(switch_Misc_l232)
 001768       2'b00 : begin
 001768         writeBack_DBusSimplePlugin_rspFormated = _zz_writeBack_DBusSimplePlugin_rspFormated_1;
              end
 001236       2'b01 : begin
 001236         writeBack_DBusSimplePlugin_rspFormated = _zz_writeBack_DBusSimplePlugin_rspFormated_3;
              end
 001338       default : begin
 001338         writeBack_DBusSimplePlugin_rspFormated = writeBack_DBusSimplePlugin_rspShifted;
              end
            endcase
          end
        
          assign when_DBusSimplePlugin_l566 = (writeBack_arbitration_isValid && writeBack_MEMORY_ENABLE);
          assign _zz_decode_IS_CSR_1 = ((decode_INSTRUCTION & 32'h00004050) == 32'h00004050);
          assign _zz_decode_IS_CSR_2 = ((decode_INSTRUCTION & 32'h00000018) == 32'h00000000);
          assign _zz_decode_IS_CSR_3 = ((decode_INSTRUCTION & 32'h00000004) == 32'h00000004);
          assign _zz_decode_IS_CSR_4 = ((decode_INSTRUCTION & 32'h00000050) == 32'h00000010);
          assign _zz_decode_IS_CSR_5 = ((decode_INSTRUCTION & 32'h00000048) == 32'h00000048);
          assign _zz_decode_IS_CSR = {(|((decode_INSTRUCTION & 32'h10003050) == 32'h00000050)),{(|((decode_INSTRUCTION & _zz__zz_decode_IS_CSR) == 32'h10000050)),{(|{_zz__zz_decode_IS_CSR_1,_zz__zz_decode_IS_CSR_2}),{(|{_zz__zz_decode_IS_CSR_3,_zz__zz_decode_IS_CSR_4}),{(|_zz__zz_decode_IS_CSR_6),{_zz__zz_decode_IS_CSR_8,{_zz__zz_decode_IS_CSR_11,_zz__zz_decode_IS_CSR_16}}}}}}};
          assign _zz_decode_SRC1_CTRL_2 = _zz_decode_IS_CSR[1 : 0];
          assign _zz_decode_SRC1_CTRL_1 = _zz_decode_SRC1_CTRL_2;
          assign _zz_decode_ALU_CTRL_2 = _zz_decode_IS_CSR[6 : 5];
          assign _zz_decode_ALU_CTRL_1 = _zz_decode_ALU_CTRL_2;
          assign _zz_decode_SRC2_CTRL_2 = _zz_decode_IS_CSR[8 : 7];
          assign _zz_decode_SRC2_CTRL_1 = _zz_decode_SRC2_CTRL_2;
          assign _zz_decode_ALU_BITWISE_CTRL_2 = _zz_decode_IS_CSR[17 : 16];
          assign _zz_decode_ALU_BITWISE_CTRL_1 = _zz_decode_ALU_BITWISE_CTRL_2;
          assign _zz_decode_SHIFT_CTRL_2 = _zz_decode_IS_CSR[20 : 19];
          assign _zz_decode_SHIFT_CTRL_1 = _zz_decode_SHIFT_CTRL_2;
          assign _zz_decode_BRANCH_CTRL_2 = _zz_decode_IS_CSR[22 : 21];
          assign _zz_decode_BRANCH_CTRL_1 = _zz_decode_BRANCH_CTRL_2;
          assign _zz_decode_ENV_CTRL_2 = _zz_decode_IS_CSR[25 : 24];
          assign _zz_decode_ENV_CTRL_1 = _zz_decode_ENV_CTRL_2;
          assign decodeExceptionPort_valid = (decode_arbitration_isValid && (! decode_LEGAL_INSTRUCTION));
          assign decodeExceptionPort_payload_code = 4'b0010;
          assign decodeExceptionPort_payload_badAddr = decode_INSTRUCTION;
          assign when_RegFilePlugin_l63 = (decode_INSTRUCTION[11 : 7] == 5'h00);
          assign decode_RegFilePlugin_regFileReadAddress1 = decode_INSTRUCTION_ANTICIPATED[19 : 15];
          assign decode_RegFilePlugin_regFileReadAddress2 = decode_INSTRUCTION_ANTICIPATED[24 : 20];
          assign decode_RegFilePlugin_rs1Data = _zz_RegFilePlugin_regFile_port0;
          assign decode_RegFilePlugin_rs2Data = _zz_RegFilePlugin_regFile_port1;
 013024   always @(*) begin
 013024     lastStageRegFileWrite_valid = (_zz_lastStageRegFileWrite_valid && writeBack_arbitration_isFiring);
 013006     if(_zz_5) begin
 000018       lastStageRegFileWrite_valid = 1'b1;
            end
          end
        
 004342   always @(*) begin
 004342     lastStageRegFileWrite_payload_address = _zz_lastStageRegFileWrite_payload_address[11 : 7];
 004336     if(_zz_5) begin
 000006       lastStageRegFileWrite_payload_address = 5'h00;
            end
          end
        
 004342   always @(*) begin
 004342     lastStageRegFileWrite_payload_data = _zz_lastStageRegFileWrite_payload_data;
 004336     if(_zz_5) begin
 000006       lastStageRegFileWrite_payload_data = 32'h00000000;
            end
          end
        
 004342   always @(*) begin
 004342     case(execute_ALU_BITWISE_CTRL)
 001403       AluBitwiseCtrlEnum_AND_1 : begin
 001403         execute_IntAluPlugin_bitwise = (execute_SRC1 & execute_SRC2);
              end
 001133       AluBitwiseCtrlEnum_OR_1 : begin
 001133         execute_IntAluPlugin_bitwise = (execute_SRC1 | execute_SRC2);
              end
 001806       default : begin
 001806         execute_IntAluPlugin_bitwise = (execute_SRC1 ^ execute_SRC2);
              end
            endcase
          end
        
 004342   always @(*) begin
 004342     case(execute_ALU_CTRL)
 000085       AluCtrlEnum_BITWISE : begin
 000085         _zz_execute_REGFILE_WRITE_DATA = execute_IntAluPlugin_bitwise;
              end
 000014       AluCtrlEnum_SLT_SLTU : begin
 000014         _zz_execute_REGFILE_WRITE_DATA = {31'd0, _zz__zz_execute_REGFILE_WRITE_DATA};
              end
 004243       default : begin
 004243         _zz_execute_REGFILE_WRITE_DATA = execute_SRC_ADD_SUB;
              end
            endcase
          end
        
 004342   always @(*) begin
 004342     case(execute_SRC1_CTRL)
 003858       Src1CtrlEnum_RS : begin
 003858         _zz_execute_SRC1 = execute_RS1;
              end
 000159       Src1CtrlEnum_PC_INCREMENT : begin
 000159         _zz_execute_SRC1 = {29'd0, _zz__zz_execute_SRC1};
              end
 000325       Src1CtrlEnum_IMU : begin
 000325         _zz_execute_SRC1 = {execute_INSTRUCTION[31 : 12],12'h000};
              end
%000000       default : begin
%000000         _zz_execute_SRC1 = {27'd0, _zz__zz_execute_SRC1_1};
              end
            endcase
          end
        
          assign _zz_execute_SRC2 = execute_INSTRUCTION[31];
 000001   always @(*) begin
 000001     _zz_execute_SRC2_1[19] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[18] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[17] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[16] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[15] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[14] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[13] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[12] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[11] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[10] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[9] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[8] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[7] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[6] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[5] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[4] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[3] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[2] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[1] = _zz_execute_SRC2;
 000001     _zz_execute_SRC2_1[0] = _zz_execute_SRC2;
          end
        
          assign _zz_execute_SRC2_2 = _zz__zz_execute_SRC2_2[11];
 000001   always @(*) begin
 000001     _zz_execute_SRC2_3[19] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[18] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[17] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[16] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[15] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[14] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[13] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[12] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[11] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[10] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[9] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[8] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[7] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[6] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[5] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[4] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[3] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[2] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[1] = _zz_execute_SRC2_2;
 000001     _zz_execute_SRC2_3[0] = _zz_execute_SRC2_2;
          end
        
 004342   always @(*) begin
 004342     case(execute_SRC2_CTRL)
 001565       Src2CtrlEnum_RS : begin
 001565         _zz_execute_SRC2_4 = execute_RS2;
              end
 001842       Src2CtrlEnum_IMI : begin
 001842         _zz_execute_SRC2_4 = {_zz_execute_SRC2_1,execute_INSTRUCTION[31 : 20]};
              end
 000451       Src2CtrlEnum_IMS : begin
 000451         _zz_execute_SRC2_4 = {_zz_execute_SRC2_3,{execute_INSTRUCTION[31 : 25],execute_INSTRUCTION[11 : 7]}};
              end
 000484       default : begin
 000484         _zz_execute_SRC2_4 = _zz_execute_to_memory_PC;
              end
            endcase
          end
        
 004342   always @(*) begin
 004342     execute_SrcPlugin_addSub = _zz_execute_SrcPlugin_addSub;
 003914     if(execute_SRC2_FORCE_ZERO) begin
 000428       execute_SrcPlugin_addSub = execute_SRC1;
            end
          end
        
          assign execute_SrcPlugin_less = ((execute_SRC1[31] == execute_SRC2[31]) ? execute_SrcPlugin_addSub[31] : (execute_SRC_LESS_UNSIGNED ? execute_SRC2[31] : execute_SRC1[31]));
          assign execute_LightShifterPlugin_isShift = (execute_SHIFT_CTRL != ShiftCtrlEnum_DISABLE_1);
          assign execute_LightShifterPlugin_amplitude = (execute_LightShifterPlugin_isActive ? execute_LightShifterPlugin_amplitudeReg : execute_SRC2[4 : 0]);
          assign execute_LightShifterPlugin_shiftInput = (execute_LightShifterPlugin_isActive ? memory_REGFILE_WRITE_DATA : execute_SRC1);
          assign execute_LightShifterPlugin_done = (execute_LightShifterPlugin_amplitude[4 : 1] == 4'b0000);
          assign when_ShiftPlugins_l169 = ((execute_arbitration_isValid && execute_LightShifterPlugin_isShift) && (execute_SRC2[4 : 0] != 5'h00));
 004342   always @(*) begin
 004342     case(execute_SHIFT_CTRL)
 000192       ShiftCtrlEnum_SLL_1 : begin
 000192         _zz_execute_to_memory_REGFILE_WRITE_DATA_1 = (execute_LightShifterPlugin_shiftInput <<< 1);
              end
 004150       default : begin
 004150         _zz_execute_to_memory_REGFILE_WRITE_DATA_1 = _zz__zz_execute_to_memory_REGFILE_WRITE_DATA_1;
              end
            endcase
          end
        
          assign when_ShiftPlugins_l175 = (! execute_arbitration_isStuckByOthers);
          assign when_ShiftPlugins_l184 = (! execute_LightShifterPlugin_done);
 004342   always @(*) begin
 004342     HazardSimplePlugin_src0Hazard = 1'b0;
 003748     if(HazardSimplePlugin_writeBackBuffer_valid) begin
 000345       if(HazardSimplePlugin_addr0Match) begin
 000345         HazardSimplePlugin_src0Hazard = 1'b1;
              end
            end
 003748     if(when_HazardSimplePlugin_l57) begin
~000594       if(when_HazardSimplePlugin_l58) begin
 000333         if(when_HazardSimplePlugin_l59) begin
 000333           HazardSimplePlugin_src0Hazard = 1'b1;
                end
              end
            end
 003646     if(when_HazardSimplePlugin_l57_1) begin
~000696       if(when_HazardSimplePlugin_l58_1) begin
 000393         if(when_HazardSimplePlugin_l59_1) begin
 000393           HazardSimplePlugin_src0Hazard = 1'b1;
                end
              end
            end
 003422     if(when_HazardSimplePlugin_l57_2) begin
~000920       if(when_HazardSimplePlugin_l58_2) begin
 000470         if(when_HazardSimplePlugin_l59_2) begin
 000450           HazardSimplePlugin_src0Hazard = 1'b1;
                end
              end
            end
 003942     if(when_HazardSimplePlugin_l105) begin
 000400       HazardSimplePlugin_src0Hazard = 1'b0;
            end
          end
        
 004342   always @(*) begin
 004342     HazardSimplePlugin_src1Hazard = 1'b0;
 003748     if(HazardSimplePlugin_writeBackBuffer_valid) begin
 000465       if(HazardSimplePlugin_addr1Match) begin
 000129         HazardSimplePlugin_src1Hazard = 1'b1;
              end
            end
 003748     if(when_HazardSimplePlugin_l57) begin
~000594       if(when_HazardSimplePlugin_l58) begin
 000466         if(when_HazardSimplePlugin_l62) begin
 000128           HazardSimplePlugin_src1Hazard = 1'b1;
                end
              end
            end
 003646     if(when_HazardSimplePlugin_l57_1) begin
~000696       if(when_HazardSimplePlugin_l58_1) begin
 000560         if(when_HazardSimplePlugin_l62_1) begin
 000136           HazardSimplePlugin_src1Hazard = 1'b1;
                end
              end
            end
 003422     if(when_HazardSimplePlugin_l57_2) begin
~000920       if(when_HazardSimplePlugin_l58_2) begin
 000832         if(when_HazardSimplePlugin_l62_2) begin
 000088           HazardSimplePlugin_src1Hazard = 1'b1;
                end
              end
            end
 002327     if(when_HazardSimplePlugin_l108) begin
 002327       HazardSimplePlugin_src1Hazard = 1'b0;
            end
          end
        
          assign HazardSimplePlugin_writeBackWrites_valid = (_zz_lastStageRegFileWrite_valid && writeBack_arbitration_isFiring);
          assign HazardSimplePlugin_writeBackWrites_payload_address = _zz_lastStageRegFileWrite_payload_address[11 : 7];
          assign HazardSimplePlugin_writeBackWrites_payload_data = _zz_lastStageRegFileWrite_payload_data;
          assign HazardSimplePlugin_addr0Match = (HazardSimplePlugin_writeBackBuffer_payload_address == decode_INSTRUCTION[19 : 15]);
          assign HazardSimplePlugin_addr1Match = (HazardSimplePlugin_writeBackBuffer_payload_address == decode_INSTRUCTION[24 : 20]);
          assign when_HazardSimplePlugin_l59 = (writeBack_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]);
          assign when_HazardSimplePlugin_l62 = (writeBack_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]);
          assign when_HazardSimplePlugin_l57 = (writeBack_arbitration_isValid && writeBack_REGFILE_WRITE_VALID);
          assign when_HazardSimplePlugin_l58 = (1'b1 || (! 1'b1));
          assign when_HazardSimplePlugin_l59_1 = (memory_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]);
          assign when_HazardSimplePlugin_l62_1 = (memory_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]);
          assign when_HazardSimplePlugin_l57_1 = (memory_arbitration_isValid && memory_REGFILE_WRITE_VALID);
          assign when_HazardSimplePlugin_l58_1 = (1'b1 || (! memory_BYPASSABLE_MEMORY_STAGE));
          assign when_HazardSimplePlugin_l59_2 = (execute_INSTRUCTION[11 : 7] == decode_INSTRUCTION[19 : 15]);
          assign when_HazardSimplePlugin_l62_2 = (execute_INSTRUCTION[11 : 7] == decode_INSTRUCTION[24 : 20]);
          assign when_HazardSimplePlugin_l57_2 = (execute_arbitration_isValid && execute_REGFILE_WRITE_VALID);
          assign when_HazardSimplePlugin_l58_2 = (1'b1 || (! execute_BYPASSABLE_EXECUTE_STAGE));
          assign when_HazardSimplePlugin_l105 = (! decode_RS1_USE);
          assign when_HazardSimplePlugin_l108 = (! decode_RS2_USE);
          assign when_HazardSimplePlugin_l113 = (decode_arbitration_isValid && (HazardSimplePlugin_src0Hazard || HazardSimplePlugin_src1Hazard));
          assign execute_BranchPlugin_eq = (execute_SRC1 == execute_SRC2);
          assign switch_Misc_l232_1 = execute_INSTRUCTION[14 : 12];
 004342   always @(*) begin
 004342     case(switch_Misc_l232_1)
 001806       3'b000 : begin
 001806         _zz_execute_BRANCH_DO = execute_BranchPlugin_eq;
              end
 001243       3'b001 : begin
 001243         _zz_execute_BRANCH_DO = (! execute_BranchPlugin_eq);
              end
%000000       3'b101 : begin
%000000         _zz_execute_BRANCH_DO = (! execute_SRC_LESS);
              end
 000155       3'b111 : begin
 000155         _zz_execute_BRANCH_DO = (! execute_SRC_LESS);
              end
 001138       default : begin
 001138         _zz_execute_BRANCH_DO = execute_SRC_LESS;
              end
            endcase
          end
        
 004342   always @(*) begin
 004342     case(execute_BRANCH_CTRL)
 003035       BranchCtrlEnum_INC : begin
 003035         _zz_execute_BRANCH_DO_1 = 1'b0;
              end
 000072       BranchCtrlEnum_JAL : begin
 000072         _zz_execute_BRANCH_DO_1 = 1'b1;
              end
 000087       BranchCtrlEnum_JALR : begin
 000087         _zz_execute_BRANCH_DO_1 = 1'b1;
              end
 001148       default : begin
 001148         _zz_execute_BRANCH_DO_1 = _zz_execute_BRANCH_DO;
              end
            endcase
          end
        
          assign execute_BranchPlugin_branch_src1 = ((execute_BRANCH_CTRL == BranchCtrlEnum_JALR) ? execute_RS1 : execute_PC);
          assign _zz_execute_BranchPlugin_branch_src2 = _zz__zz_execute_BranchPlugin_branch_src2[19];
 000001   always @(*) begin
 000001     _zz_execute_BranchPlugin_branch_src2_1[10] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[9] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[8] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[7] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[6] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[5] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[4] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[3] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[2] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[1] = _zz_execute_BranchPlugin_branch_src2;
 000001     _zz_execute_BranchPlugin_branch_src2_1[0] = _zz_execute_BranchPlugin_branch_src2;
          end
        
          assign _zz_execute_BranchPlugin_branch_src2_2 = execute_INSTRUCTION[31];
 000001   always @(*) begin
 000001     _zz_execute_BranchPlugin_branch_src2_3[19] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[18] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[17] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[16] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[15] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[14] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[13] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[12] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[11] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[10] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[9] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[8] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[7] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[6] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[5] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[4] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[3] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[2] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[1] = _zz_execute_BranchPlugin_branch_src2_2;
 000001     _zz_execute_BranchPlugin_branch_src2_3[0] = _zz_execute_BranchPlugin_branch_src2_2;
          end
        
          assign _zz_execute_BranchPlugin_branch_src2_4 = _zz__zz_execute_BranchPlugin_branch_src2_4[11];
 000001   always @(*) begin
 000001     _zz_execute_BranchPlugin_branch_src2_5[18] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[17] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[16] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[15] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[14] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[13] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[12] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[11] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[10] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[9] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[8] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[7] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[6] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[5] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[4] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[3] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[2] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[1] = _zz_execute_BranchPlugin_branch_src2_4;
 000001     _zz_execute_BranchPlugin_branch_src2_5[0] = _zz_execute_BranchPlugin_branch_src2_4;
          end
        
 004342   always @(*) begin
 004342     case(execute_BRANCH_CTRL)
 000072       BranchCtrlEnum_JAL : begin
 000072         _zz_execute_BranchPlugin_branch_src2_6 = {{_zz_execute_BranchPlugin_branch_src2_1,{{{execute_INSTRUCTION[31],execute_INSTRUCTION[19 : 12]},execute_INSTRUCTION[20]},execute_INSTRUCTION[30 : 21]}},1'b0};
              end
 000087       BranchCtrlEnum_JALR : begin
 000087         _zz_execute_BranchPlugin_branch_src2_6 = {_zz_execute_BranchPlugin_branch_src2_3,execute_INSTRUCTION[31 : 20]};
              end
 004183       default : begin
 004183         _zz_execute_BranchPlugin_branch_src2_6 = {{_zz_execute_BranchPlugin_branch_src2_5,{{{execute_INSTRUCTION[31],execute_INSTRUCTION[7]},execute_INSTRUCTION[30 : 25]},execute_INSTRUCTION[11 : 8]}},1'b0};
              end
            endcase
          end
        
          assign execute_BranchPlugin_branch_src2 = _zz_execute_BranchPlugin_branch_src2_6;
          assign execute_BranchPlugin_branchAdder = (execute_BranchPlugin_branch_src1 + execute_BranchPlugin_branch_src2);
          assign BranchPlugin_jumpInterface_valid = ((memory_arbitration_isValid && memory_BRANCH_DO) && (! 1'b0));
          assign BranchPlugin_jumpInterface_payload = memory_BRANCH_CALC;
          assign BranchPlugin_branchExceptionPort_valid = ((memory_arbitration_isValid && memory_BRANCH_DO) && BranchPlugin_jumpInterface_payload[1]);
          assign BranchPlugin_branchExceptionPort_payload_code = 4'b0000;
          assign BranchPlugin_branchExceptionPort_payload_badAddr = BranchPlugin_jumpInterface_payload;
 000001   always @(*) begin
 000001     CsrPlugin_privilege = 2'b11;
~000001     if(CsrPlugin_forceMachineWire) begin
%000000       CsrPlugin_privilege = 2'b11;
            end
          end
        
          assign CsrPlugin_misa_base = 2'b01;
          assign CsrPlugin_misa_extensions = 26'h0000042;
          assign _zz_when_CsrPlugin_l1302 = (CsrPlugin_mip_MTIP && CsrPlugin_mie_MTIE);
          assign _zz_when_CsrPlugin_l1302_1 = (CsrPlugin_mip_MSIP && CsrPlugin_mie_MSIE);
          assign _zz_when_CsrPlugin_l1302_2 = (CsrPlugin_mip_MEIP && CsrPlugin_mie_MEIE);
          assign CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilegeUncapped = 2'b11;
          assign CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilege = ((CsrPlugin_privilege < CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilegeUncapped) ? CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilegeUncapped : CsrPlugin_privilege);
          assign _zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code = {BranchPlugin_branchExceptionPort_valid,DBusSimplePlugin_memoryExceptionPort_valid};
          assign _zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1 = _zz__zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1[0];
 013024   always @(*) begin
 013024     CsrPlugin_exceptionPortCtrl_exceptionValids_decode = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode;
 013021     if(decodeExceptionPort_valid) begin
 000003       CsrPlugin_exceptionPortCtrl_exceptionValids_decode = 1'b1;
            end
 012334     if(decode_arbitration_isFlushed) begin
 000690       CsrPlugin_exceptionPortCtrl_exceptionValids_decode = 1'b0;
            end
          end
        
 013024   always @(*) begin
 013024     CsrPlugin_exceptionPortCtrl_exceptionValids_execute = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute;
~013024     if(CsrPlugin_selfException_valid) begin
%000000       CsrPlugin_exceptionPortCtrl_exceptionValids_execute = 1'b1;
            end
 012334     if(execute_arbitration_isFlushed) begin
 000690       CsrPlugin_exceptionPortCtrl_exceptionValids_execute = 1'b0;
            end
          end
        
 013024   always @(*) begin
 013024     CsrPlugin_exceptionPortCtrl_exceptionValids_memory = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory;
~013024     if(_zz_when) begin
%000000       CsrPlugin_exceptionPortCtrl_exceptionValids_memory = 1'b1;
            end
 013018     if(memory_arbitration_isFlushed) begin
 000006       CsrPlugin_exceptionPortCtrl_exceptionValids_memory = 1'b0;
            end
          end
        
 000001   always @(*) begin
 000001     CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack;
~000001     if(writeBack_arbitration_isFlushed) begin
%000000       CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack = 1'b0;
            end
          end
        
          assign when_CsrPlugin_l1259 = (! decode_arbitration_isStuck);
          assign when_CsrPlugin_l1259_1 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1259_2 = (! memory_arbitration_isStuck);
          assign when_CsrPlugin_l1259_3 = (! writeBack_arbitration_isStuck);
          assign when_CsrPlugin_l1272 = ({CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack,{CsrPlugin_exceptionPortCtrl_exceptionValids_memory,{CsrPlugin_exceptionPortCtrl_exceptionValids_execute,CsrPlugin_exceptionPortCtrl_exceptionValids_decode}}} != 4'b0000);
          assign CsrPlugin_exceptionPendings_0 = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode;
          assign CsrPlugin_exceptionPendings_1 = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute;
          assign CsrPlugin_exceptionPendings_2 = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory;
          assign CsrPlugin_exceptionPendings_3 = CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack;
          assign when_CsrPlugin_l1296 = (CsrPlugin_mstatus_MIE || (CsrPlugin_privilege < 2'b11));
          assign when_CsrPlugin_l1302 = ((_zz_when_CsrPlugin_l1302 && 1'b1) && (! 1'b0));
          assign when_CsrPlugin_l1302_1 = ((_zz_when_CsrPlugin_l1302_1 && 1'b1) && (! 1'b0));
          assign when_CsrPlugin_l1302_2 = ((_zz_when_CsrPlugin_l1302_2 && 1'b1) && (! 1'b0));
          assign CsrPlugin_exception = (CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack && CsrPlugin_allowException);
          assign CsrPlugin_lastStageWasWfi = 1'b0;
          assign CsrPlugin_pipelineLiberator_active = ((CsrPlugin_interrupt_valid && CsrPlugin_allowInterrupts) && decode_arbitration_isValid);
          assign when_CsrPlugin_l1335 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1335_1 = (! memory_arbitration_isStuck);
          assign when_CsrPlugin_l1335_2 = (! writeBack_arbitration_isStuck);
          assign when_CsrPlugin_l1340 = ((! CsrPlugin_pipelineLiberator_active) || decode_arbitration_removeIt);
 013024   always @(*) begin
 013024     CsrPlugin_pipelineLiberator_done = CsrPlugin_pipelineLiberator_pcValids_2;
~013024     if(when_CsrPlugin_l1346) begin
%000000       CsrPlugin_pipelineLiberator_done = 1'b0;
            end
~013024     if(CsrPlugin_hadException) begin
%000000       CsrPlugin_pipelineLiberator_done = 1'b0;
            end
          end
        
          assign when_CsrPlugin_l1346 = ({CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack,{CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory,CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute}} != 3'b000);
          assign CsrPlugin_interruptJump = ((CsrPlugin_interrupt_valid && CsrPlugin_pipelineLiberator_done) && CsrPlugin_allowInterrupts);
 013024   always @(*) begin
 013024     CsrPlugin_targetPrivilege = CsrPlugin_interrupt_targetPrivilege;
~013024     if(CsrPlugin_hadException) begin
%000000       CsrPlugin_targetPrivilege = CsrPlugin_exceptionPortCtrl_exceptionTargetPrivilege;
            end
          end
        
 013024   always @(*) begin
 013024     CsrPlugin_trapCause = CsrPlugin_interrupt_code;
~013024     if(CsrPlugin_hadException) begin
%000000       CsrPlugin_trapCause = CsrPlugin_exceptionPortCtrl_exceptionContext_code;
            end
          end
        
          assign CsrPlugin_trapCauseEbreakDebug = 1'b0;
 013024   always @(*) begin
 013024     CsrPlugin_xtvec_mode = 2'bxx;
 013024     case(CsrPlugin_targetPrivilege)
 004597       2'b11 : begin
 004597         CsrPlugin_xtvec_mode = CsrPlugin_mtvec_mode;
              end
 008427       default : begin
              end
            endcase
          end
        
 013024   always @(*) begin
 013024     CsrPlugin_xtvec_base = 30'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
 013024     case(CsrPlugin_targetPrivilege)
 004597       2'b11 : begin
 004597         CsrPlugin_xtvec_base = CsrPlugin_mtvec_base;
              end
 008427       default : begin
              end
            endcase
          end
        
          assign CsrPlugin_trapEnterDebug = 1'b0;
          assign when_CsrPlugin_l1390 = (CsrPlugin_hadException || CsrPlugin_interruptJump);
          assign when_CsrPlugin_l1398 = (! CsrPlugin_trapEnterDebug);
          assign when_CsrPlugin_l1456 = (writeBack_arbitration_isValid && (writeBack_ENV_CTRL == EnvCtrlEnum_XRET));
          assign switch_CsrPlugin_l1460 = writeBack_INSTRUCTION[29 : 28];
          assign contextSwitching = CsrPlugin_jumpInterface_valid;
          assign when_CsrPlugin_l1527 = (|{(writeBack_arbitration_isValid && (writeBack_ENV_CTRL == EnvCtrlEnum_XRET)),{(memory_arbitration_isValid && (memory_ENV_CTRL == EnvCtrlEnum_XRET)),(execute_arbitration_isValid && (execute_ENV_CTRL == EnvCtrlEnum_XRET))}});
          assign execute_CsrPlugin_blockedBySideEffects = ((|{writeBack_arbitration_isValid,memory_arbitration_isValid}) || 1'b0);
 004342   always @(*) begin
 004342     execute_CsrPlugin_illegalAccess = 1'b1;
 004337     if(execute_CsrPlugin_csr_768) begin
 000005       execute_CsrPlugin_illegalAccess = 1'b0;
            end
 004337     if(execute_CsrPlugin_csr_836) begin
 000005       execute_CsrPlugin_illegalAccess = 1'b0;
            end
 004337     if(execute_CsrPlugin_csr_772) begin
 000005       execute_CsrPlugin_illegalAccess = 1'b0;
            end
 004337     if(execute_CsrPlugin_csr_773) begin
~000005       if(execute_CSR_WRITE_OPCODE) begin
 000005         execute_CsrPlugin_illegalAccess = 1'b0;
              end
            end
~004342     if(execute_CsrPlugin_csr_833) begin
%000000       execute_CsrPlugin_illegalAccess = 1'b0;
            end
 004338     if(execute_CsrPlugin_csr_834) begin
~000004       if(execute_CSR_READ_OPCODE) begin
 000004         execute_CsrPlugin_illegalAccess = 1'b0;
              end
            end
~004342     if(execute_CsrPlugin_csr_835) begin
%000000       if(execute_CSR_READ_OPCODE) begin
%000000         execute_CsrPlugin_illegalAccess = 1'b0;
              end
            end
 004337     if(execute_CsrPlugin_csr_3008) begin
 000005       execute_CsrPlugin_illegalAccess = 1'b0;
            end
~004342     if(execute_CsrPlugin_csr_4032) begin
%000000       if(execute_CSR_READ_OPCODE) begin
%000000         execute_CsrPlugin_illegalAccess = 1'b0;
              end
            end
~004342     if(CsrPlugin_csrMapping_allowCsrSignal) begin
%000000       execute_CsrPlugin_illegalAccess = 1'b0;
            end
~004342     if(when_CsrPlugin_l1719) begin
%000000       execute_CsrPlugin_illegalAccess = 1'b1;
            end
 004337     if(when_CsrPlugin_l1725) begin
 004337       execute_CsrPlugin_illegalAccess = 1'b0;
            end
          end
        
 004342   always @(*) begin
 004342     execute_CsrPlugin_illegalInstruction = 1'b0;
 004341     if(when_CsrPlugin_l1547) begin
~000001       if(when_CsrPlugin_l1548) begin
%000000         execute_CsrPlugin_illegalInstruction = 1'b1;
              end
            end
          end
        
 004342   always @(*) begin
 004342     CsrPlugin_selfException_valid = 1'b0;
~004342     if(when_CsrPlugin_l1555) begin
%000000       CsrPlugin_selfException_valid = 1'b1;
            end
          end
        
 004342   always @(*) begin
 004342     CsrPlugin_selfException_payload_code = 4'bxxxx;
~004342     if(when_CsrPlugin_l1555) begin
%000000       case(CsrPlugin_privilege)
%000000         2'b00 : begin
%000000           CsrPlugin_selfException_payload_code = 4'b1000;
                end
%000000         default : begin
%000000           CsrPlugin_selfException_payload_code = 4'b1011;
                end
              endcase
            end
          end
        
          assign CsrPlugin_selfException_payload_badAddr = execute_INSTRUCTION;
          assign when_CsrPlugin_l1547 = (execute_arbitration_isValid && (execute_ENV_CTRL == EnvCtrlEnum_XRET));
          assign when_CsrPlugin_l1548 = (CsrPlugin_privilege < execute_INSTRUCTION[29 : 28]);
          assign when_CsrPlugin_l1555 = (execute_arbitration_isValid && (execute_ENV_CTRL == EnvCtrlEnum_ECALL));
 004342   always @(*) begin
 004342     execute_CsrPlugin_writeInstruction = ((execute_arbitration_isValid && execute_IS_CSR) && execute_CSR_WRITE_OPCODE);
~004342     if(when_CsrPlugin_l1719) begin
%000000       execute_CsrPlugin_writeInstruction = 1'b0;
            end
          end
        
 000001   always @(*) begin
 000001     execute_CsrPlugin_readInstruction = ((execute_arbitration_isValid && execute_IS_CSR) && execute_CSR_READ_OPCODE);
~000001     if(when_CsrPlugin_l1719) begin
%000000       execute_CsrPlugin_readInstruction = 1'b0;
            end
          end
        
          assign execute_CsrPlugin_writeEnable = (execute_CsrPlugin_writeInstruction && (! execute_arbitration_isStuck));
          assign execute_CsrPlugin_readEnable = (execute_CsrPlugin_readInstruction && (! execute_arbitration_isStuck));
          assign CsrPlugin_csrMapping_hazardFree = (! execute_CsrPlugin_blockedBySideEffects);
          assign execute_CsrPlugin_readToWriteData = CsrPlugin_csrMapping_readDataSignal;
          assign switch_Misc_l232_2 = execute_INSTRUCTION[13];
 004342   always @(*) begin
 004342     case(switch_Misc_l232_2)
 003049       1'b0 : begin
 003049         _zz_CsrPlugin_csrMapping_writeDataSignal = execute_SRC1;
              end
 001293       default : begin
 001293         _zz_CsrPlugin_csrMapping_writeDataSignal = (execute_INSTRUCTION[12] ? (execute_CsrPlugin_readToWriteData & (~ execute_SRC1)) : (execute_CsrPlugin_readToWriteData | execute_SRC1));
              end
            endcase
          end
        
          assign CsrPlugin_csrMapping_writeDataSignal = _zz_CsrPlugin_csrMapping_writeDataSignal;
          assign when_CsrPlugin_l1587 = (execute_arbitration_isValid && execute_IS_CSR);
          assign when_CsrPlugin_l1591 = (execute_arbitration_isValid && (execute_IS_CSR || 1'b0));
          assign execute_CsrPlugin_csrAddress = execute_INSTRUCTION[31 : 20];
          assign _zz_externalInterrupt = (_zz_CsrPlugin_csrMapping_readDataInit & externalInterruptArray_regNext);
          assign externalInterrupt = (|_zz_externalInterrupt);
          assign when_Pipeline_l124 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_1 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_2 = ((! writeBack_arbitration_isStuck) && (! CsrPlugin_exceptionPortCtrl_exceptionValids_writeBack));
          assign when_Pipeline_l124_3 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_4 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_5 = (! writeBack_arbitration_isStuck);
          assign when_Pipeline_l124_6 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_7 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_8 = (! writeBack_arbitration_isStuck);
          assign _zz_decode_to_execute_SRC1_CTRL_1 = decode_SRC1_CTRL;
          assign _zz_decode_SRC1_CTRL = _zz_decode_SRC1_CTRL_1;
          assign when_Pipeline_l124_9 = (! execute_arbitration_isStuck);
          assign _zz_execute_SRC1_CTRL = decode_to_execute_SRC1_CTRL;
          assign when_Pipeline_l124_10 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_11 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_12 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_13 = (! writeBack_arbitration_isStuck);
          assign _zz_decode_to_execute_ALU_CTRL_1 = decode_ALU_CTRL;
          assign _zz_decode_ALU_CTRL = _zz_decode_ALU_CTRL_1;
          assign when_Pipeline_l124_14 = (! execute_arbitration_isStuck);
          assign _zz_execute_ALU_CTRL = decode_to_execute_ALU_CTRL;
          assign _zz_decode_to_execute_SRC2_CTRL_1 = decode_SRC2_CTRL;
          assign _zz_decode_SRC2_CTRL = _zz_decode_SRC2_CTRL_1;
          assign when_Pipeline_l124_15 = (! execute_arbitration_isStuck);
          assign _zz_execute_SRC2_CTRL = decode_to_execute_SRC2_CTRL;
          assign when_Pipeline_l124_16 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_17 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_18 = (! writeBack_arbitration_isStuck);
          assign when_Pipeline_l124_19 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_20 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_21 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_22 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_23 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_24 = (! execute_arbitration_isStuck);
          assign _zz_decode_to_execute_ALU_BITWISE_CTRL_1 = decode_ALU_BITWISE_CTRL;
          assign _zz_decode_ALU_BITWISE_CTRL = _zz_decode_ALU_BITWISE_CTRL_1;
          assign when_Pipeline_l124_25 = (! execute_arbitration_isStuck);
          assign _zz_execute_ALU_BITWISE_CTRL = decode_to_execute_ALU_BITWISE_CTRL;
          assign _zz_decode_to_execute_SHIFT_CTRL_1 = decode_SHIFT_CTRL;
          assign _zz_decode_SHIFT_CTRL = _zz_decode_SHIFT_CTRL_1;
          assign when_Pipeline_l124_26 = (! execute_arbitration_isStuck);
          assign _zz_execute_SHIFT_CTRL = decode_to_execute_SHIFT_CTRL;
          assign _zz_decode_to_execute_BRANCH_CTRL_1 = decode_BRANCH_CTRL;
          assign _zz_decode_BRANCH_CTRL = _zz_decode_BRANCH_CTRL_1;
          assign when_Pipeline_l124_27 = (! execute_arbitration_isStuck);
          assign _zz_execute_BRANCH_CTRL = decode_to_execute_BRANCH_CTRL;
          assign when_Pipeline_l124_28 = (! execute_arbitration_isStuck);
          assign _zz_decode_to_execute_ENV_CTRL_1 = decode_ENV_CTRL;
          assign _zz_execute_to_memory_ENV_CTRL_1 = execute_ENV_CTRL;
          assign _zz_memory_to_writeBack_ENV_CTRL_1 = memory_ENV_CTRL;
          assign _zz_decode_ENV_CTRL = _zz_decode_ENV_CTRL_1;
          assign when_Pipeline_l124_29 = (! execute_arbitration_isStuck);
          assign _zz_execute_ENV_CTRL = decode_to_execute_ENV_CTRL;
          assign when_Pipeline_l124_30 = (! memory_arbitration_isStuck);
          assign _zz_memory_ENV_CTRL = execute_to_memory_ENV_CTRL;
          assign when_Pipeline_l124_31 = (! writeBack_arbitration_isStuck);
          assign _zz_writeBack_ENV_CTRL = memory_to_writeBack_ENV_CTRL;
          assign when_Pipeline_l124_32 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_33 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_34 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_35 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_36 = (! execute_arbitration_isStuck);
          assign when_Pipeline_l124_37 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_38 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_39 = (! writeBack_arbitration_isStuck);
          assign when_Pipeline_l124_40 = ((! memory_arbitration_isStuck) && (! execute_arbitration_isStuckByOthers));
          assign when_Pipeline_l124_41 = (! writeBack_arbitration_isStuck);
          assign when_Pipeline_l124_42 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_43 = (! memory_arbitration_isStuck);
          assign when_Pipeline_l124_44 = (! writeBack_arbitration_isStuck);
          assign decode_arbitration_isFlushed = (({writeBack_arbitration_flushNext,{memory_arbitration_flushNext,execute_arbitration_flushNext}} != 3'b000) || ({writeBack_arbitration_flushIt,{memory_arbitration_flushIt,{execute_arbitration_flushIt,decode_arbitration_flushIt}}} != 4'b0000));
          assign execute_arbitration_isFlushed = (({writeBack_arbitration_flushNext,memory_arbitration_flushNext} != 2'b00) || ({writeBack_arbitration_flushIt,{memory_arbitration_flushIt,execute_arbitration_flushIt}} != 3'b000));
          assign memory_arbitration_isFlushed = ((writeBack_arbitration_flushNext != 1'b0) || ({writeBack_arbitration_flushIt,memory_arbitration_flushIt} != 2'b00));
          assign writeBack_arbitration_isFlushed = (1'b0 || (writeBack_arbitration_flushIt != 1'b0));
          assign decode_arbitration_isStuckByOthers = (decode_arbitration_haltByOther || (((1'b0 || execute_arbitration_isStuck) || memory_arbitration_isStuck) || writeBack_arbitration_isStuck));
          assign decode_arbitration_isStuck = (decode_arbitration_haltItself || decode_arbitration_isStuckByOthers);
          assign decode_arbitration_isMoving = ((! decode_arbitration_isStuck) && (! decode_arbitration_removeIt));
          assign decode_arbitration_isFiring = ((decode_arbitration_isValid && (! decode_arbitration_isStuck)) && (! decode_arbitration_removeIt));
          assign execute_arbitration_isStuckByOthers = (execute_arbitration_haltByOther || ((1'b0 || memory_arbitration_isStuck) || writeBack_arbitration_isStuck));
          assign execute_arbitration_isStuck = (execute_arbitration_haltItself || execute_arbitration_isStuckByOthers);
          assign execute_arbitration_isMoving = ((! execute_arbitration_isStuck) && (! execute_arbitration_removeIt));
          assign execute_arbitration_isFiring = ((execute_arbitration_isValid && (! execute_arbitration_isStuck)) && (! execute_arbitration_removeIt));
          assign memory_arbitration_isStuckByOthers = (memory_arbitration_haltByOther || (1'b0 || writeBack_arbitration_isStuck));
          assign memory_arbitration_isStuck = (memory_arbitration_haltItself || memory_arbitration_isStuckByOthers);
          assign memory_arbitration_isMoving = ((! memory_arbitration_isStuck) && (! memory_arbitration_removeIt));
          assign memory_arbitration_isFiring = ((memory_arbitration_isValid && (! memory_arbitration_isStuck)) && (! memory_arbitration_removeIt));
          assign writeBack_arbitration_isStuckByOthers = (writeBack_arbitration_haltByOther || 1'b0);
          assign writeBack_arbitration_isStuck = (writeBack_arbitration_haltItself || writeBack_arbitration_isStuckByOthers);
          assign writeBack_arbitration_isMoving = ((! writeBack_arbitration_isStuck) && (! writeBack_arbitration_removeIt));
          assign writeBack_arbitration_isFiring = ((writeBack_arbitration_isValid && (! writeBack_arbitration_isStuck)) && (! writeBack_arbitration_removeIt));
          assign when_Pipeline_l151 = ((! execute_arbitration_isStuck) || execute_arbitration_removeIt);
          assign when_Pipeline_l154 = ((! decode_arbitration_isStuck) && (! decode_arbitration_removeIt));
          assign when_Pipeline_l151_1 = ((! memory_arbitration_isStuck) || memory_arbitration_removeIt);
          assign when_Pipeline_l154_1 = ((! execute_arbitration_isStuck) && (! execute_arbitration_removeIt));
          assign when_Pipeline_l151_2 = ((! writeBack_arbitration_isStuck) || writeBack_arbitration_removeIt);
          assign when_Pipeline_l154_2 = ((! memory_arbitration_isStuck) && (! memory_arbitration_removeIt));
          assign when_CsrPlugin_l1669 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_1 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_2 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_3 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_4 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_5 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_6 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_7 = (! execute_arbitration_isStuck);
          assign when_CsrPlugin_l1669_8 = (! execute_arbitration_isStuck);
          assign switch_CsrPlugin_l1031 = CsrPlugin_csrMapping_writeDataSignal[12 : 11];
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_1 = 32'h00000000;
 004337     if(execute_CsrPlugin_csr_768) begin
 000005       _zz_CsrPlugin_csrMapping_readDataInit_1[7 : 7] = CsrPlugin_mstatus_MPIE;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_1[3 : 3] = CsrPlugin_mstatus_MIE;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_1[12 : 11] = CsrPlugin_mstatus_MPP;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_2 = 32'h00000000;
 004337     if(execute_CsrPlugin_csr_836) begin
 000005       _zz_CsrPlugin_csrMapping_readDataInit_2[11 : 11] = CsrPlugin_mip_MEIP;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_2[7 : 7] = CsrPlugin_mip_MTIP;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_2[3 : 3] = CsrPlugin_mip_MSIP;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_3 = 32'h00000000;
 004337     if(execute_CsrPlugin_csr_772) begin
 000005       _zz_CsrPlugin_csrMapping_readDataInit_3[11 : 11] = CsrPlugin_mie_MEIE;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_3[7 : 7] = CsrPlugin_mie_MTIE;
 000005       _zz_CsrPlugin_csrMapping_readDataInit_3[3 : 3] = CsrPlugin_mie_MSIE;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_4 = 32'h00000000;
~004342     if(execute_CsrPlugin_csr_833) begin
%000000       _zz_CsrPlugin_csrMapping_readDataInit_4[31 : 0] = CsrPlugin_mepc;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_5 = 32'h00000000;
 004338     if(execute_CsrPlugin_csr_834) begin
 000004       _zz_CsrPlugin_csrMapping_readDataInit_5[31 : 31] = CsrPlugin_mcause_interrupt;
 000004       _zz_CsrPlugin_csrMapping_readDataInit_5[3 : 0] = CsrPlugin_mcause_exceptionCode;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_6 = 32'h00000000;
~004342     if(execute_CsrPlugin_csr_835) begin
%000000       _zz_CsrPlugin_csrMapping_readDataInit_6[31 : 0] = CsrPlugin_mtval;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_7 = 32'h00000000;
 004337     if(execute_CsrPlugin_csr_3008) begin
 000005       _zz_CsrPlugin_csrMapping_readDataInit_7[31 : 0] = _zz_CsrPlugin_csrMapping_readDataInit;
            end
          end
        
 004342   always @(*) begin
 004342     _zz_CsrPlugin_csrMapping_readDataInit_8 = 32'h00000000;
~004342     if(execute_CsrPlugin_csr_4032) begin
%000000       _zz_CsrPlugin_csrMapping_readDataInit_8[31 : 0] = _zz_externalInterrupt;
            end
          end
        
          assign CsrPlugin_csrMapping_readDataInit = (((_zz_CsrPlugin_csrMapping_readDataInit_1 | _zz_CsrPlugin_csrMapping_readDataInit_2) | (_zz_CsrPlugin_csrMapping_readDataInit_3 | _zz_CsrPlugin_csrMapping_readDataInit_4)) | ((_zz_CsrPlugin_csrMapping_readDataInit_5 | _zz_CsrPlugin_csrMapping_readDataInit_6) | (_zz_CsrPlugin_csrMapping_readDataInit_7 | _zz_CsrPlugin_csrMapping_readDataInit_8)));
          assign when_CsrPlugin_l1702 = ((execute_arbitration_isValid && execute_IS_CSR) && (({execute_CsrPlugin_csrAddress[11 : 2],2'b00} == 12'h3a0) || ({execute_CsrPlugin_csrAddress[11 : 4],4'b0000} == 12'h3b0)));
          assign _zz_when_CsrPlugin_l1709 = (execute_CsrPlugin_csrAddress & 12'hf60);
          assign when_CsrPlugin_l1709 = (((execute_arbitration_isValid && execute_IS_CSR) && (5'h03 <= execute_CsrPlugin_csrAddress[4 : 0])) && (((_zz_when_CsrPlugin_l1709 == 12'hb00) || (((_zz_when_CsrPlugin_l1709 == 12'hc00) && (! execute_CsrPlugin_writeInstruction)) && (CsrPlugin_privilege == 2'b11))) || ((execute_CsrPlugin_csrAddress & 12'hfe0) == 12'h320)));
 000001   always @(*) begin
 000001     when_CsrPlugin_l1719 = CsrPlugin_csrMapping_doForceFailCsr;
~000001     if(when_CsrPlugin_l1717) begin
%000000       when_CsrPlugin_l1719 = 1'b1;
            end
          end
        
          assign when_CsrPlugin_l1717 = (CsrPlugin_privilege < execute_CsrPlugin_csrAddress[9 : 8]);
          assign when_CsrPlugin_l1725 = ((! execute_arbitration_isValid) || (! execute_IS_CSR));
 004342   always @(*) begin
 004342     iBus_cmd_ready = iBus_cmd_m2sPipe_ready;
 003183     if(when_Stream_l369) begin
 001159       iBus_cmd_ready = 1'b1;
            end
          end
        
          assign when_Stream_l369 = (! iBus_cmd_m2sPipe_valid);
          assign iBus_cmd_m2sPipe_valid = iBus_cmd_rValid;
          assign iBus_cmd_m2sPipe_payload_pc = iBus_cmd_rData_pc;
          assign iBusWishbone_ADR = (iBus_cmd_m2sPipe_payload_pc >>> 2'd2);
          assign iBusWishbone_CTI = 3'b000;
          assign iBusWishbone_BTE = 2'b00;
          assign iBusWishbone_SEL = 4'b1111;
          assign iBusWishbone_WE = 1'b0;
          assign iBusWishbone_DAT_MOSI = 32'bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx;
          assign iBusWishbone_CYC = iBus_cmd_m2sPipe_valid;
          assign iBusWishbone_STB = iBus_cmd_m2sPipe_valid;
          assign iBus_cmd_m2sPipe_ready = (iBus_cmd_m2sPipe_valid && iBusWishbone_ACK);
          assign iBus_rsp_valid = (iBusWishbone_CYC && iBusWishbone_ACK);
          assign iBus_rsp_payload_inst = iBusWishbone_DAT_MISO;
          assign iBus_rsp_payload_error = 1'b0;
          assign dBus_cmd_halfPipe_fire = (dBus_cmd_halfPipe_valid && dBus_cmd_halfPipe_ready);
          assign dBus_cmd_ready = (! dBus_cmd_rValid);
          assign dBus_cmd_halfPipe_valid = dBus_cmd_rValid;
          assign dBus_cmd_halfPipe_payload_wr = dBus_cmd_rData_wr;
          assign dBus_cmd_halfPipe_payload_address = dBus_cmd_rData_address;
          assign dBus_cmd_halfPipe_payload_data = dBus_cmd_rData_data;
          assign dBus_cmd_halfPipe_payload_size = dBus_cmd_rData_size;
          assign dBusWishbone_ADR = (dBus_cmd_halfPipe_payload_address >>> 2'd2);
          assign dBusWishbone_CTI = 3'b000;
          assign dBusWishbone_BTE = 2'b00;
 004342   always @(*) begin
 004342     case(dBus_cmd_halfPipe_payload_size)
 001640       2'b00 : begin
 001640         _zz_dBusWishbone_SEL = 4'b0001;
              end
 001195       2'b01 : begin
 001195         _zz_dBusWishbone_SEL = 4'b0011;
              end
 001507       default : begin
 001507         _zz_dBusWishbone_SEL = 4'b1111;
              end
            endcase
          end
        
 004342   always @(*) begin
 004342     dBusWishbone_SEL = (_zz_dBusWishbone_SEL <<< dBus_cmd_halfPipe_payload_address[1 : 0]);
 002419     if(when_DBusSimplePlugin_l196) begin
 001923       dBusWishbone_SEL = 4'b1111;
            end
          end
        
          assign when_DBusSimplePlugin_l196 = (! dBus_cmd_halfPipe_payload_wr);
          assign dBusWishbone_WE = dBus_cmd_halfPipe_payload_wr;
          assign dBusWishbone_DAT_MOSI = dBus_cmd_halfPipe_payload_data;
          assign dBus_cmd_halfPipe_ready = (dBus_cmd_halfPipe_valid && dBusWishbone_ACK);
          assign dBusWishbone_CYC = dBus_cmd_halfPipe_valid;
          assign dBusWishbone_STB = dBus_cmd_halfPipe_valid;
          assign dBus_rsp_ready = ((dBus_cmd_halfPipe_valid && (! dBusWishbone_WE)) && dBusWishbone_ACK);
          assign dBus_rsp_data = dBusWishbone_DAT_MISO;
          assign dBus_rsp_error = 1'b0;
          assign IBusSimplePlugin_rspJoin_rspBuffer_c_io_flush = 1'b0;
 004341   always @(posedge clk) begin
 004335     if(reset) begin
 000006       IBusSimplePlugin_fetchPc_pcReg <= externalResetVector;
 000006       IBusSimplePlugin_fetchPc_correctionReg <= 1'b0;
 000006       IBusSimplePlugin_fetchPc_booted <= 1'b0;
 000006       IBusSimplePlugin_fetchPc_inc <= 1'b0;
 000006       _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid_1 <= 1'b0;
 000006       _zz_IBusSimplePlugin_injector_decodeInput_valid <= 1'b0;
 000006       IBusSimplePlugin_injector_nextPcCalc_valids_0 <= 1'b0;
 000006       IBusSimplePlugin_injector_nextPcCalc_valids_1 <= 1'b0;
 000006       IBusSimplePlugin_injector_nextPcCalc_valids_2 <= 1'b0;
 000006       IBusSimplePlugin_injector_nextPcCalc_valids_3 <= 1'b0;
 000006       IBusSimplePlugin_injector_nextPcCalc_valids_4 <= 1'b0;
 000006       IBusSimplePlugin_pending_value <= 3'b000;
 000006       IBusSimplePlugin_rspJoin_rspBuffer_discardCounter <= 3'b000;
 000006       _zz_5 <= 1'b1;
 000006       execute_LightShifterPlugin_isActive <= 1'b0;
 000006       HazardSimplePlugin_writeBackBuffer_valid <= 1'b0;
 000006       CsrPlugin_mstatus_MIE <= 1'b0;
 000006       CsrPlugin_mstatus_MPIE <= 1'b0;
 000006       CsrPlugin_mstatus_MPP <= 2'b11;
 000006       CsrPlugin_mie_MEIE <= 1'b0;
 000006       CsrPlugin_mie_MTIE <= 1'b0;
 000006       CsrPlugin_mie_MSIE <= 1'b0;
 000006       CsrPlugin_mcycle <= 64'h0000000000000000;
 000006       CsrPlugin_minstret <= 64'h0000000000000000;
 000006       CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode <= 1'b0;
 000006       CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= 1'b0;
 000006       CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= 1'b0;
 000006       CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= 1'b0;
 000006       CsrPlugin_interrupt_valid <= 1'b0;
 000006       CsrPlugin_pipelineLiberator_pcValids_0 <= 1'b0;
 000006       CsrPlugin_pipelineLiberator_pcValids_1 <= 1'b0;
 000006       CsrPlugin_pipelineLiberator_pcValids_2 <= 1'b0;
 000006       CsrPlugin_hadException <= 1'b0;
 000006       execute_CsrPlugin_wfiWake <= 1'b0;
 000006       _zz_CsrPlugin_csrMapping_readDataInit <= 32'h00000000;
 000006       execute_arbitration_isValid <= 1'b0;
 000006       memory_arbitration_isValid <= 1'b0;
 000006       writeBack_arbitration_isValid <= 1'b0;
 000006       iBus_cmd_rValid <= 1'b0;
 000006       dBus_cmd_rValid <= 1'b0;
 004335     end else begin
 004105       if(IBusSimplePlugin_fetchPc_correction) begin
 000230         IBusSimplePlugin_fetchPc_correctionReg <= 1'b1;
              end
 002744       if(IBusSimplePlugin_fetchPc_output_fire) begin
 001591         IBusSimplePlugin_fetchPc_correctionReg <= 1'b0;
              end
 004335       IBusSimplePlugin_fetchPc_booted <= 1'b1;
 002700       if(when_Fetcher_l133) begin
 001635         IBusSimplePlugin_fetchPc_inc <= 1'b0;
              end
 002744       if(IBusSimplePlugin_fetchPc_output_fire) begin
 001591         IBusSimplePlugin_fetchPc_inc <= 1'b1;
              end
 004334       if(when_Fetcher_l133_1) begin
 000001         IBusSimplePlugin_fetchPc_inc <= 1'b0;
              end
 002701       if(when_Fetcher_l160) begin
 001634         IBusSimplePlugin_fetchPc_pcReg <= IBusSimplePlugin_fetchPc_pc;
              end
 004105       if(IBusSimplePlugin_iBusRsp_flush) begin
 000230         _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid_1 <= 1'b0;
              end
 002743       if(_zz_IBusSimplePlugin_iBusRsp_stages_0_output_ready) begin
 001592         _zz_IBusSimplePlugin_iBusRsp_stages_1_input_valid_1 <= (IBusSimplePlugin_iBusRsp_stages_0_output_valid && (! 1'b0));
              end
 004105       if(decode_arbitration_removeIt) begin
 000230         _zz_IBusSimplePlugin_injector_decodeInput_valid <= 1'b0;
              end
 002740       if(IBusSimplePlugin_iBusRsp_output_ready) begin
 002740         _zz_IBusSimplePlugin_injector_decodeInput_valid <= (IBusSimplePlugin_iBusRsp_output_valid && (! IBusSimplePlugin_externalFlush));
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_0 <= 1'b0;
              end
 002743       if(when_Fetcher_l331) begin
 001592         IBusSimplePlugin_injector_nextPcCalc_valids_0 <= 1'b1;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_1 <= 1'b0;
              end
 002740       if(when_Fetcher_l331_1) begin
 002740         IBusSimplePlugin_injector_nextPcCalc_valids_1 <= IBusSimplePlugin_injector_nextPcCalc_valids_0;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_1 <= 1'b0;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_2 <= 1'b0;
              end
 004107       if(when_Fetcher_l331_2) begin
 004107         IBusSimplePlugin_injector_nextPcCalc_valids_2 <= IBusSimplePlugin_injector_nextPcCalc_valids_1;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_2 <= 1'b0;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_3 <= 1'b0;
              end
 004233       if(when_Fetcher_l331_3) begin
 004233         IBusSimplePlugin_injector_nextPcCalc_valids_3 <= IBusSimplePlugin_injector_nextPcCalc_valids_2;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_3 <= 1'b0;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_4 <= 1'b0;
              end
~004335       if(when_Fetcher_l331_4) begin
 004335         IBusSimplePlugin_injector_nextPcCalc_valids_4 <= IBusSimplePlugin_injector_nextPcCalc_valids_3;
              end
 004105       if(IBusSimplePlugin_fetchPc_flushed) begin
 000230         IBusSimplePlugin_injector_nextPcCalc_valids_4 <= 1'b0;
              end
 004335       IBusSimplePlugin_pending_value <= IBusSimplePlugin_pending_next;
 004335       IBusSimplePlugin_rspJoin_rspBuffer_discardCounter <= (IBusSimplePlugin_rspJoin_rspBuffer_discardCounter - _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter);
 004105       if(IBusSimplePlugin_iBusRsp_flush) begin
 000230         IBusSimplePlugin_rspJoin_rspBuffer_discardCounter <= (IBusSimplePlugin_pending_value - _zz_IBusSimplePlugin_rspJoin_rspBuffer_discardCounter_2);
              end
 004335       _zz_5 <= 1'b0;
 004207       if(when_ShiftPlugins_l169) begin
~000128         if(when_ShiftPlugins_l175) begin
 000128           execute_LightShifterPlugin_isActive <= 1'b1;
 000064           if(execute_LightShifterPlugin_done) begin
 000064             execute_LightShifterPlugin_isActive <= 1'b0;
                  end
                end
              end
 004105       if(execute_arbitration_removeIt) begin
 000230         execute_LightShifterPlugin_isActive <= 1'b0;
              end
 004335       HazardSimplePlugin_writeBackBuffer_valid <= HazardSimplePlugin_writeBackWrites_valid;
 004335       CsrPlugin_mcycle <= (CsrPlugin_mcycle + 64'h0000000000000001);
 003204       if(writeBack_arbitration_isFiring) begin
 001131         CsrPlugin_minstret <= (CsrPlugin_minstret + 64'h0000000000000001);
              end
 002740       if(when_CsrPlugin_l1259) begin
 002740         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode <= 1'b0;
 001595       end else begin
 001595         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_decode <= CsrPlugin_exceptionPortCtrl_exceptionValids_decode;
              end
 004107       if(when_CsrPlugin_l1259_1) begin
 004107         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= (CsrPlugin_exceptionPortCtrl_exceptionValids_decode && (! decode_arbitration_isStuck));
 000228       end else begin
 000228         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_execute <= CsrPlugin_exceptionPortCtrl_exceptionValids_execute;
              end
 004233       if(when_CsrPlugin_l1259_2) begin
 004233         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= (CsrPlugin_exceptionPortCtrl_exceptionValids_execute && (! execute_arbitration_isStuck));
 000102       end else begin
 000102         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory <= CsrPlugin_exceptionPortCtrl_exceptionValids_memory;
              end
~004335       if(when_CsrPlugin_l1259_3) begin
 004335         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= (CsrPlugin_exceptionPortCtrl_exceptionValids_memory && (! memory_arbitration_isStuck));
%000000       end else begin
%000000         CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_writeBack <= 1'b0;
              end
 004335       CsrPlugin_interrupt_valid <= 1'b0;
 003022       if(when_CsrPlugin_l1296) begin
~001313         if(when_CsrPlugin_l1302) begin
%000000           CsrPlugin_interrupt_valid <= 1'b1;
                end
~001313         if(when_CsrPlugin_l1302_1) begin
%000000           CsrPlugin_interrupt_valid <= 1'b1;
                end
 001308         if(when_CsrPlugin_l1302_2) begin
 000005           CsrPlugin_interrupt_valid <= 1'b1;
                end
              end
 004331       if(CsrPlugin_pipelineLiberator_active) begin
~000004         if(when_CsrPlugin_l1335) begin
 000004           CsrPlugin_pipelineLiberator_pcValids_0 <= 1'b1;
                end
~000004         if(when_CsrPlugin_l1335_1) begin
 000004           CsrPlugin_pipelineLiberator_pcValids_1 <= CsrPlugin_pipelineLiberator_pcValids_0;
                end
~000004         if(when_CsrPlugin_l1335_2) begin
 000004           CsrPlugin_pipelineLiberator_pcValids_2 <= CsrPlugin_pipelineLiberator_pcValids_1;
                end
              end
 004332       if(when_CsrPlugin_l1340) begin
 004332         CsrPlugin_pipelineLiberator_pcValids_0 <= 1'b0;
 004332         CsrPlugin_pipelineLiberator_pcValids_1 <= 1'b0;
 004332         CsrPlugin_pipelineLiberator_pcValids_2 <= 1'b0;
              end
 004334       if(CsrPlugin_interruptJump) begin
 000001         CsrPlugin_interrupt_valid <= 1'b0;
              end
 004335       CsrPlugin_hadException <= CsrPlugin_exception;
 004334       if(when_CsrPlugin_l1390) begin
~000001         if(when_CsrPlugin_l1398) begin
 000001           case(CsrPlugin_targetPrivilege)
 000001             2'b11 : begin
 000001               CsrPlugin_mstatus_MIE <= 1'b0;
 000001               CsrPlugin_mstatus_MPIE <= CsrPlugin_mstatus_MIE;
 000001               CsrPlugin_mstatus_MPP <= CsrPlugin_privilege;
                    end
%000000             default : begin
                    end
                  endcase
                end
              end
 004334       if(when_CsrPlugin_l1456) begin
 000001         case(switch_CsrPlugin_l1460)
 000001           2'b11 : begin
 000001             CsrPlugin_mstatus_MPP <= 2'b00;
 000001             CsrPlugin_mstatus_MIE <= CsrPlugin_mstatus_MPIE;
 000001             CsrPlugin_mstatus_MPIE <= 1'b1;
                  end
%000000           default : begin
                  end
                endcase
              end
 004335       execute_CsrPlugin_wfiWake <= (({_zz_when_CsrPlugin_l1302_2,{_zz_when_CsrPlugin_l1302_1,_zz_when_CsrPlugin_l1302}} != 3'b000) || CsrPlugin_thirdPartyWake);
 004107       if(when_Pipeline_l151) begin
 004107         execute_arbitration_isValid <= 1'b0;
              end
 002512       if(when_Pipeline_l154) begin
 002512         execute_arbitration_isValid <= decode_arbitration_isValid;
              end
 004233       if(when_Pipeline_l151_1) begin
 004233         memory_arbitration_isValid <= 1'b0;
              end
 003877       if(when_Pipeline_l154_1) begin
 003877         memory_arbitration_isValid <= execute_arbitration_isValid;
              end
~004335       if(when_Pipeline_l151_2) begin
 004335         writeBack_arbitration_isValid <= 1'b0;
              end
 004231       if(when_Pipeline_l154_2) begin
 004231         writeBack_arbitration_isValid <= memory_arbitration_isValid;
              end
 004330       if(execute_CsrPlugin_csr_768) begin
 000004         if(execute_CsrPlugin_writeEnable) begin
 000001           CsrPlugin_mstatus_MPIE <= CsrPlugin_csrMapping_writeDataSignal[7];
 000001           CsrPlugin_mstatus_MIE <= CsrPlugin_csrMapping_writeDataSignal[3];
 000001           case(switch_CsrPlugin_l1031)
 000001             2'b11 : begin
 000001               CsrPlugin_mstatus_MPP <= 2'b11;
                    end
%000000             default : begin
                    end
                  endcase
                end
              end
 004330       if(execute_CsrPlugin_csr_772) begin
 000004         if(execute_CsrPlugin_writeEnable) begin
 000001           CsrPlugin_mie_MEIE <= CsrPlugin_csrMapping_writeDataSignal[11];
 000001           CsrPlugin_mie_MTIE <= CsrPlugin_csrMapping_writeDataSignal[7];
 000001           CsrPlugin_mie_MSIE <= CsrPlugin_csrMapping_writeDataSignal[3];
                end
              end
 004330       if(execute_CsrPlugin_csr_3008) begin
 000004         if(execute_CsrPlugin_writeEnable) begin
 000001           _zz_CsrPlugin_csrMapping_readDataInit <= CsrPlugin_csrMapping_writeDataSignal[31 : 0];
                end
              end
 002743       if(iBus_cmd_ready) begin
 002743         iBus_cmd_rValid <= iBus_cmd_valid;
              end
 004049       if(dBus_cmd_valid) begin
 000286         dBus_cmd_rValid <= 1'b1;
              end
 004111       if(dBus_cmd_halfPipe_fire) begin
 000224         dBus_cmd_rValid <= 1'b0;
              end
            end
          end
        
 004341   always @(posedge clk) begin
 002746     if(IBusSimplePlugin_iBusRsp_output_ready) begin
 002746       _zz_IBusSimplePlugin_injector_decodeInput_payload_pc <= IBusSimplePlugin_iBusRsp_output_payload_pc;
 002746       _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_error <= IBusSimplePlugin_iBusRsp_output_payload_rsp_error;
 002746       _zz_IBusSimplePlugin_injector_decodeInput_payload_rsp_inst <= IBusSimplePlugin_iBusRsp_output_payload_rsp_inst;
 002746       _zz_IBusSimplePlugin_injector_decodeInput_payload_isRvc <= IBusSimplePlugin_iBusRsp_output_payload_isRvc;
            end
 002746     if(IBusSimplePlugin_injector_decodeInput_ready) begin
 002746       IBusSimplePlugin_injector_formal_rawInDecode <= IBusSimplePlugin_iBusRsp_output_payload_rsp_inst;
            end
 004213     if(when_ShiftPlugins_l169) begin
~000128       if(when_ShiftPlugins_l175) begin
 000128         execute_LightShifterPlugin_amplitudeReg <= (execute_LightShifterPlugin_amplitude - 5'h01);
              end
            end
 004341     HazardSimplePlugin_writeBackBuffer_payload_address <= HazardSimplePlugin_writeBackWrites_payload_address;
 004341     HazardSimplePlugin_writeBackBuffer_payload_data <= HazardSimplePlugin_writeBackWrites_payload_data;
 004341     CsrPlugin_mip_MEIP <= externalInterrupt;
 004341     CsrPlugin_mip_MTIP <= timerInterrupt;
 004341     CsrPlugin_mip_MSIP <= softwareInterrupt;
 004340     if(decodeExceptionPort_valid) begin
 000001       CsrPlugin_exceptionPortCtrl_exceptionContext_code <= decodeExceptionPort_payload_code;
 000001       CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr <= decodeExceptionPort_payload_badAddr;
            end
~004341     if(CsrPlugin_selfException_valid) begin
%000000       CsrPlugin_exceptionPortCtrl_exceptionContext_code <= CsrPlugin_selfException_payload_code;
%000000       CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr <= CsrPlugin_selfException_payload_badAddr;
            end
~004341     if(_zz_when) begin
%000000       CsrPlugin_exceptionPortCtrl_exceptionContext_code <= (_zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1 ? DBusSimplePlugin_memoryExceptionPort_payload_code : BranchPlugin_branchExceptionPort_payload_code);
%000000       CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr <= (_zz_CsrPlugin_exceptionPortCtrl_exceptionContext_code_1 ? DBusSimplePlugin_memoryExceptionPort_payload_badAddr : BranchPlugin_branchExceptionPort_payload_badAddr);
            end
 003028     if(when_CsrPlugin_l1296) begin
~001313       if(when_CsrPlugin_l1302) begin
%000000         CsrPlugin_interrupt_code <= 4'b0111;
%000000         CsrPlugin_interrupt_targetPrivilege <= 2'b11;
              end
~001313       if(when_CsrPlugin_l1302_1) begin
%000000         CsrPlugin_interrupt_code <= 4'b0011;
%000000         CsrPlugin_interrupt_targetPrivilege <= 2'b11;
              end
 001308       if(when_CsrPlugin_l1302_2) begin
 000005         CsrPlugin_interrupt_code <= 4'b1011;
 000005         CsrPlugin_interrupt_targetPrivilege <= 2'b11;
              end
            end
 004340     if(when_CsrPlugin_l1390) begin
~000001       if(when_CsrPlugin_l1398) begin
 000001         case(CsrPlugin_targetPrivilege)
 000001           2'b11 : begin
 000001             CsrPlugin_mcause_interrupt <= (! CsrPlugin_hadException);
 000001             CsrPlugin_mcause_exceptionCode <= CsrPlugin_trapCause;
 000001             CsrPlugin_mepc <= writeBack_PC;
~000001             if(CsrPlugin_hadException) begin
%000000               CsrPlugin_mtval <= CsrPlugin_exceptionPortCtrl_exceptionContext_badAddr;
                    end
                  end
%000000           default : begin
                  end
                endcase
              end
            end
 004341     externalInterruptArray_regNext <= externalInterruptArray;
 004113     if(when_Pipeline_l124) begin
 004113       decode_to_execute_PC <= decode_PC;
            end
 004239     if(when_Pipeline_l124_1) begin
 004239       execute_to_memory_PC <= _zz_execute_to_memory_PC;
            end
~004341     if(when_Pipeline_l124_2) begin
 004341       memory_to_writeBack_PC <= memory_PC;
            end
 004113     if(when_Pipeline_l124_3) begin
 004113       decode_to_execute_INSTRUCTION <= decode_INSTRUCTION;
            end
 004239     if(when_Pipeline_l124_4) begin
 004239       execute_to_memory_INSTRUCTION <= execute_INSTRUCTION;
            end
~004341     if(when_Pipeline_l124_5) begin
 004341       memory_to_writeBack_INSTRUCTION <= memory_INSTRUCTION;
            end
 004113     if(when_Pipeline_l124_6) begin
 004113       decode_to_execute_FORMAL_PC_NEXT <= decode_FORMAL_PC_NEXT;
            end
 004239     if(when_Pipeline_l124_7) begin
 004239       execute_to_memory_FORMAL_PC_NEXT <= execute_FORMAL_PC_NEXT;
            end
~004341     if(when_Pipeline_l124_8) begin
 004341       memory_to_writeBack_FORMAL_PC_NEXT <= _zz_memory_to_writeBack_FORMAL_PC_NEXT;
            end
 004113     if(when_Pipeline_l124_9) begin
 004113       decode_to_execute_SRC1_CTRL <= _zz_decode_to_execute_SRC1_CTRL;
            end
 004113     if(when_Pipeline_l124_10) begin
 004113       decode_to_execute_SRC_USE_SUB_LESS <= decode_SRC_USE_SUB_LESS;
            end
 004113     if(when_Pipeline_l124_11) begin
 004113       decode_to_execute_MEMORY_ENABLE <= decode_MEMORY_ENABLE;
            end
 004239     if(when_Pipeline_l124_12) begin
 004239       execute_to_memory_MEMORY_ENABLE <= execute_MEMORY_ENABLE;
            end
~004341     if(when_Pipeline_l124_13) begin
 004341       memory_to_writeBack_MEMORY_ENABLE <= memory_MEMORY_ENABLE;
            end
 004113     if(when_Pipeline_l124_14) begin
 004113       decode_to_execute_ALU_CTRL <= _zz_decode_to_execute_ALU_CTRL;
            end
 004113     if(when_Pipeline_l124_15) begin
 004113       decode_to_execute_SRC2_CTRL <= _zz_decode_to_execute_SRC2_CTRL;
            end
 004113     if(when_Pipeline_l124_16) begin
 004113       decode_to_execute_REGFILE_WRITE_VALID <= decode_REGFILE_WRITE_VALID;
            end
 004239     if(when_Pipeline_l124_17) begin
 004239       execute_to_memory_REGFILE_WRITE_VALID <= execute_REGFILE_WRITE_VALID;
            end
~004341     if(when_Pipeline_l124_18) begin
 004341       memory_to_writeBack_REGFILE_WRITE_VALID <= memory_REGFILE_WRITE_VALID;
            end
 004113     if(when_Pipeline_l124_19) begin
 004113       decode_to_execute_BYPASSABLE_EXECUTE_STAGE <= decode_BYPASSABLE_EXECUTE_STAGE;
            end
 004113     if(when_Pipeline_l124_20) begin
 004113       decode_to_execute_BYPASSABLE_MEMORY_STAGE <= decode_BYPASSABLE_MEMORY_STAGE;
            end
 004239     if(when_Pipeline_l124_21) begin
 004239       execute_to_memory_BYPASSABLE_MEMORY_STAGE <= execute_BYPASSABLE_MEMORY_STAGE;
            end
 004113     if(when_Pipeline_l124_22) begin
 004113       decode_to_execute_MEMORY_STORE <= decode_MEMORY_STORE;
            end
 004239     if(when_Pipeline_l124_23) begin
 004239       execute_to_memory_MEMORY_STORE <= execute_MEMORY_STORE;
            end
 004113     if(when_Pipeline_l124_24) begin
 004113       decode_to_execute_SRC_LESS_UNSIGNED <= decode_SRC_LESS_UNSIGNED;
            end
 004113     if(when_Pipeline_l124_25) begin
 004113       decode_to_execute_ALU_BITWISE_CTRL <= _zz_decode_to_execute_ALU_BITWISE_CTRL;
            end
 004113     if(when_Pipeline_l124_26) begin
 004113       decode_to_execute_SHIFT_CTRL <= _zz_decode_to_execute_SHIFT_CTRL;
            end
 004113     if(when_Pipeline_l124_27) begin
 004113       decode_to_execute_BRANCH_CTRL <= _zz_decode_to_execute_BRANCH_CTRL;
            end
 004113     if(when_Pipeline_l124_28) begin
 004113       decode_to_execute_IS_CSR <= decode_IS_CSR;
            end
 004113     if(when_Pipeline_l124_29) begin
 004113       decode_to_execute_ENV_CTRL <= _zz_decode_to_execute_ENV_CTRL;
            end
 004239     if(when_Pipeline_l124_30) begin
 004239       execute_to_memory_ENV_CTRL <= _zz_execute_to_memory_ENV_CTRL;
            end
~004341     if(when_Pipeline_l124_31) begin
 004341       memory_to_writeBack_ENV_CTRL <= _zz_memory_to_writeBack_ENV_CTRL;
            end
 004113     if(when_Pipeline_l124_32) begin
 004113       decode_to_execute_RS1 <= decode_RS1;
            end
 004113     if(when_Pipeline_l124_33) begin
 004113       decode_to_execute_RS2 <= decode_RS2;
            end
 004113     if(when_Pipeline_l124_34) begin
 004113       decode_to_execute_SRC2_FORCE_ZERO <= decode_SRC2_FORCE_ZERO;
            end
 004113     if(when_Pipeline_l124_35) begin
 004113       decode_to_execute_CSR_WRITE_OPCODE <= decode_CSR_WRITE_OPCODE;
            end
 004113     if(when_Pipeline_l124_36) begin
 004113       decode_to_execute_CSR_READ_OPCODE <= decode_CSR_READ_OPCODE;
            end
 004239     if(when_Pipeline_l124_37) begin
 004239       execute_to_memory_ALIGNEMENT_FAULT <= execute_ALIGNEMENT_FAULT;
            end
 004239     if(when_Pipeline_l124_38) begin
 004239       execute_to_memory_MEMORY_ADDRESS_LOW <= execute_MEMORY_ADDRESS_LOW;
            end
~004341     if(when_Pipeline_l124_39) begin
 004341       memory_to_writeBack_MEMORY_ADDRESS_LOW <= memory_MEMORY_ADDRESS_LOW;
            end
 004239     if(when_Pipeline_l124_40) begin
 004239       execute_to_memory_REGFILE_WRITE_DATA <= _zz_execute_to_memory_REGFILE_WRITE_DATA;
            end
~004341     if(when_Pipeline_l124_41) begin
 004341       memory_to_writeBack_REGFILE_WRITE_DATA <= memory_REGFILE_WRITE_DATA;
            end
 004239     if(when_Pipeline_l124_42) begin
 004239       execute_to_memory_BRANCH_DO <= execute_BRANCH_DO;
            end
 004239     if(when_Pipeline_l124_43) begin
 004239       execute_to_memory_BRANCH_CALC <= execute_BRANCH_CALC;
            end
~004341     if(when_Pipeline_l124_44) begin
 004341       memory_to_writeBack_MEMORY_READ_DATA <= memory_MEMORY_READ_DATA;
            end
 004113     if(when_CsrPlugin_l1669) begin
 004113       execute_CsrPlugin_csr_768 <= (decode_INSTRUCTION[31 : 20] == 12'h300);
            end
 004113     if(when_CsrPlugin_l1669_1) begin
 004113       execute_CsrPlugin_csr_836 <= (decode_INSTRUCTION[31 : 20] == 12'h344);
            end
 004113     if(when_CsrPlugin_l1669_2) begin
 004113       execute_CsrPlugin_csr_772 <= (decode_INSTRUCTION[31 : 20] == 12'h304);
            end
 004113     if(when_CsrPlugin_l1669_3) begin
 004113       execute_CsrPlugin_csr_773 <= (decode_INSTRUCTION[31 : 20] == 12'h305);
            end
 004113     if(when_CsrPlugin_l1669_4) begin
 004113       execute_CsrPlugin_csr_833 <= (decode_INSTRUCTION[31 : 20] == 12'h341);
            end
 004113     if(when_CsrPlugin_l1669_5) begin
 004113       execute_CsrPlugin_csr_834 <= (decode_INSTRUCTION[31 : 20] == 12'h342);
            end
 004113     if(when_CsrPlugin_l1669_6) begin
 004113       execute_CsrPlugin_csr_835 <= (decode_INSTRUCTION[31 : 20] == 12'h343);
            end
 004113     if(when_CsrPlugin_l1669_7) begin
 004113       execute_CsrPlugin_csr_3008 <= (decode_INSTRUCTION[31 : 20] == 12'hbc0);
            end
 004113     if(when_CsrPlugin_l1669_8) begin
 004113       execute_CsrPlugin_csr_4032 <= (decode_INSTRUCTION[31 : 20] == 12'hfc0);
            end
 004336     if(execute_CsrPlugin_csr_836) begin
~000005       if(execute_CsrPlugin_writeEnable) begin
%000000         CsrPlugin_mip_MSIP <= CsrPlugin_csrMapping_writeDataSignal[3];
              end
            end
 004336     if(execute_CsrPlugin_csr_773) begin
 000004       if(execute_CsrPlugin_writeEnable) begin
 000001         CsrPlugin_mtvec_base <= CsrPlugin_csrMapping_writeDataSignal[31 : 2];
              end
            end
~004341     if(execute_CsrPlugin_csr_833) begin
%000000       if(execute_CsrPlugin_writeEnable) begin
%000000         CsrPlugin_mepc <= CsrPlugin_csrMapping_writeDataSignal[31 : 0];
              end
            end
 002749     if(iBus_cmd_ready) begin
 002749       iBus_cmd_rData_pc <= iBus_cmd_payload_pc;
            end
 003887     if(dBus_cmd_ready) begin
 003887       dBus_cmd_rData_wr <= dBus_cmd_payload_wr;
 003887       dBus_cmd_rData_address <= dBus_cmd_payload_address;
 003887       dBus_cmd_rData_data <= dBus_cmd_payload_data;
 003887       dBus_cmd_rData_size <= dBus_cmd_payload_size;
            end
          end
        
        
        endmodule
        
        module StreamFifoLowLatency (
          input  wire          io_push_valid,
          output wire          io_push_ready,
          input  wire          io_push_payload_error,
          input  wire [31:0]   io_push_payload_inst,
          output wire          io_pop_valid,
          input  wire          io_pop_ready,
          output wire          io_pop_payload_error,
          output wire [31:0]   io_pop_payload_inst,
          input  wire          io_flush,
          output wire [0:0]    io_occupancy,
          output wire [0:0]    io_availability,
          input  wire          clk,
          input  wire          reset
        );
        
          wire                fifo_io_push_ready;
          wire                fifo_io_pop_valid;
          wire                fifo_io_pop_payload_error;
          wire       [31:0]   fifo_io_pop_payload_inst;
          wire       [0:0]    fifo_io_occupancy;
          wire       [0:0]    fifo_io_availability;
        
          StreamFifo fifo (
            .io_push_valid         (io_push_valid                 ), //i
            .io_push_ready         (fifo_io_push_ready            ), //o
            .io_push_payload_error (io_push_payload_error         ), //i
            .io_push_payload_inst  (io_push_payload_inst[31:0]    ), //i
            .io_pop_valid          (fifo_io_pop_valid             ), //o
            .io_pop_ready          (io_pop_ready                  ), //i
            .io_pop_payload_error  (fifo_io_pop_payload_error     ), //o
            .io_pop_payload_inst   (fifo_io_pop_payload_inst[31:0]), //o
            .io_flush              (io_flush                      ), //i
            .io_occupancy          (fifo_io_occupancy             ), //o
            .io_availability       (fifo_io_availability          ), //o
            .clk                   (clk                           ), //i
            .reset                 (reset                         )  //i
          );
          assign io_push_ready = fifo_io_push_ready;
          assign io_pop_valid = fifo_io_pop_valid;
          assign io_pop_payload_error = fifo_io_pop_payload_error;
          assign io_pop_payload_inst = fifo_io_pop_payload_inst;
          assign io_occupancy = fifo_io_occupancy;
          assign io_availability = fifo_io_availability;
        
        endmodule
        
        module StreamFifo (
          input  wire          io_push_valid,
          output reg           io_push_ready,
          input  wire          io_push_payload_error,
          input  wire [31:0]   io_push_payload_inst,
          output reg           io_pop_valid,
          input  wire          io_pop_ready,
          output reg           io_pop_payload_error,
          output reg  [31:0]   io_pop_payload_inst,
          input  wire          io_flush,
          output wire [0:0]    io_occupancy,
          output wire [0:0]    io_availability,
          input  wire          clk,
          input  wire          reset
        );
        
          reg                 oneStage_doFlush;
          wire                oneStage_buffer_valid;
          wire                oneStage_buffer_ready;
          wire                oneStage_buffer_payload_error;
          wire       [31:0]   oneStage_buffer_payload_inst;
          reg                 io_push_rValid;
          reg                 io_push_rData_error;
          reg        [31:0]   io_push_rData_inst;
          wire                when_Stream_l369;
          wire                when_Stream_l1187;
        
 013024   always @(*) begin
 013024     oneStage_doFlush = io_flush;
 009577     if(when_Stream_l1187) begin
 006420       if(io_pop_ready) begin
 003157         oneStage_doFlush = 1'b1;
              end
            end
          end
        
 013024   always @(*) begin
 013024     io_push_ready = oneStage_buffer_ready;
 009577     if(when_Stream_l369) begin
 009577       io_push_ready = 1'b1;
            end
          end
        
          assign when_Stream_l369 = (! oneStage_buffer_valid);
          assign oneStage_buffer_valid = io_push_rValid;
          assign oneStage_buffer_payload_error = io_push_rData_error;
          assign oneStage_buffer_payload_inst = io_push_rData_inst;
 004342   always @(*) begin
 004342     io_pop_valid = oneStage_buffer_valid;
 003193     if(when_Stream_l1187) begin
 003193       io_pop_valid = io_push_valid;
            end
          end
        
          assign oneStage_buffer_ready = io_pop_ready;
 004342   always @(*) begin
 004342     io_pop_payload_error = oneStage_buffer_payload_error;
 003193     if(when_Stream_l1187) begin
 003193       io_pop_payload_error = io_push_payload_error;
            end
          end
        
 004342   always @(*) begin
 004342     io_pop_payload_inst = oneStage_buffer_payload_inst;
 003193     if(when_Stream_l1187) begin
 003193       io_pop_payload_inst = io_push_payload_inst;
            end
          end
        
          assign io_occupancy = oneStage_buffer_valid;
          assign io_availability = (! oneStage_buffer_valid);
          assign when_Stream_l1187 = (! oneStage_buffer_valid);
 004341   always @(posedge clk) begin
 004335     if(reset) begin
 000006       io_push_rValid <= 1'b0;
 004335     end else begin
 003765       if(io_push_ready) begin
 003765         io_push_rValid <= io_push_valid;
              end
 003283       if(oneStage_doFlush) begin
 001052         io_push_rValid <= 1'b0;
              end
            end
          end
        
 004341   always @(posedge clk) begin
 003771     if(io_push_ready) begin
 003771       io_push_rData_error <= io_push_payload_error;
 003771       io_push_rData_inst <= io_push_payload_inst;
            end
          end
        
        
        endmodule
        
