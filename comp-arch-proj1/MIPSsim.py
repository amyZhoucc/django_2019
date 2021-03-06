# -*- coding: utf-8 -*-
# @Time    : 2019/10/27 21:38
# @Author  : Zcc
# @File    : MIPSsim.py
# @note    :On my honor, I have neither given nor received unauthorized aid on this assignment.

import sys
#基准地址
BEGIN_ADDR = 256
#指令长度
INSTRUCTION_LEN = 4
#数据长度
DATA_LEN = 4
#数据字长
BIN_DATA_LEN = 32

#存放寄存器当前的值
registers = [
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]
#以字典形式，存放汇编指令，格式是 指令地址: 指令 eg：256: 'ADD R1, R0, R0'
instruction = {}
#以字典形式，存放数据，格式是 数据地址：数据 eg：348: -3
data = {}

#category-1指令转换
#'xxxx'匹配，则进入到对应的函数中，将机器码对应的翻译出汇编指令，返回一个字符串，注意机器码翻译出来的寄存器的顺序有些不同
#J,BEQ,BLTZ,BGTZ的立即数要经过处理才能用
category_1 = {
    '0000': lambda bin_instr: 'J #%d' %(int(bin_instr[6:32]+'00', 2)),      #imm 意义为无条件跳转到指定pc地址（pc地址无负号，所以是无符号数）
    '0001': lambda bin_instr: 'JR R%d' %(int(bin_instr[6:11], 2)),          #rs  意义为无条件跳转到指定pc地址，地址存放在寄存器中
    '0010': lambda bin_instr: 'BEQ R%d, R%d, #%d' %(int(bin_instr[6:11], 2), int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32]+'00')),   #rs rt off -> rs rt off 意义为若rs = rt 就基于此跳转off量(off是signed)
    '0011': lambda bin_instr: 'BLTZ R%d, #%d' %(int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32]+'00')),                                 #rs off -> rs off 意义为若rs < 0，就基于此跳转off量（off是signed）
    '0100': lambda bin_instr: 'BGTZ R%d, #%d' %(int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32]+'00')),                                 #rs off -> rs off 意义为若rs > 0，就基于此跳转off量（off是signed）
    '0101': lambda bin_instr: 'BREAK',
    '0110': lambda bin_instr: 'SW R%d, %d(R%d)' %(int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32]), int(bin_instr[6:11],2)),          #base rt off -> rt off(base) base is a register 意义为将寄存器的值存放在内存中（off是signed）
    '0111': lambda bin_instr: 'LW R%d, %d(R%d)' %(int(bin_instr[11:16], 2), bin2dec(bin_instr[16:32]), int(bin_instr[6:11],2)),          #base rt off -> rt off(base) base is a register 意义为将内存中的值存放在寄存器（off是signed）
    '1000': lambda bin_instr: 'SLL R%d, R%d, #%d' %(int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),      #rt rd sa -> rd rt sa sa是无符号数   rt向左逻辑移位sa位（空出来的位，补0）
    '1001': lambda bin_instr: 'SRL R%d, R%d, #%d' %(int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),      #rt rd sa -> rd rt sa sa是无符号数   rt向右逻辑移位sa位（空出来的位，补0）
    '1010': lambda bin_instr: 'SRA R%d, R%d, #%d' %(int(bin_instr[16:21], 2), int(bin_instr[11:16], 2), int(bin_instr[21:26], 2)),      #rt rd sa -> rd rt sa sa是无符号数   rt向右算术移位sa位（空出来的位，补符号数）
    '1011': lambda bin_instr: 'NOP'
}
#category-2指令转换
#'xxxx'匹配，则进入到对应的函数中，将机器码对应的翻译出汇编指令，返回一个字符串，注意机器码翻译出来的操作对象的顺序有些不同
#逻辑运算指令，注意翻译出来的寄存器编号的顺序
category_2 = {
    '0000': lambda bin_instr: 'ADD R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs + rt
    '0001': lambda bin_instr: 'SUB R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs - rt
    '0010': lambda bin_instr: 'MUL R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs * rt
    '0011': lambda bin_instr: 'AND R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs and rt
    '0100': lambda bin_instr: 'OR R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),        #rs rt rd -> rd rs rt  意义为 rd <- rs or rt
    '0101': lambda bin_instr: 'XOR R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs xor rt
    '0110': lambda bin_instr: 'NOR R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为 rd <- rs nor rt
    '0111': lambda bin_instr: 'SLT R%d, R%d, R%d' %(int(bin_instr[16:21], 2), int(bin_instr[6:11], 2), int(bin_instr[11:16], 2)),       #rs rt rd -> rd rs rt  意义为若 rs < rt 返回1->rd 否则返回0->rd
    '1000': lambda bin_instr: 'ADDI R%d, R%d, #%d' %(int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), bin2dec(bin_instr[16:32])),  #rs rt imm ->rt rs imm 意义为 rt <- rs + imm(signed)
    '1001': lambda bin_instr: 'ANDI R%d, R%d, #%d' %(int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),  #rs rt imm ->rt rs imm 意义为 rt <- rs and imm(是16位，左边扩展16位，以对齐，本质上是无符号数，但是翻译还是当成符号数翻译)
    '1010': lambda bin_instr: 'ORI R%d, R%d, #%d' %(int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),   #rs rt imm ->rt rs imm 意义为 rt <- rs or imm(是16位，左边扩展16位，以对齐，本质上是无符号数)
    '1011': lambda bin_instr: 'XORI R%d, R%d, #%d' %(int(bin_instr[11:16], 2), int(bin_instr[6:11], 2), int(bin_instr[16:32], 2)),  #rs rt imm ->rt rs imm 意义为 rt <- rs xor imm(是16位，左边扩展16位，以对齐，本质上是无符号数)
}
#区分category-1和category-2，根据指令最前面2位，分别进入到不同的函数中
instruction = {
    '01': lambda bin_instr: category_1[bin_instr[2:6]](bin_instr),      #category-1根据指令的2-5位（共4位），判断具体是哪个指令
    '11': lambda bin_instr: category_2[bin_instr[2:6]](bin_instr),      #category-2
}

#模拟计算机对category-2中的 算术逻辑指令 进行具体操作
simluation_cate_2 = {
    "ADD": lambda rs,rt: rs + rt,               #寄存器加操作 rs + rt -> rd
    "SUB": lambda rs,rt: rs - rt,               #寄存器减操作 rs - rt -> rd
    "MUL": lambda rs, rt: rs * rt,              #寄存器乘操作 rs * rt -> rd
    "AND": lambda rs, rt: rs & rt,              #寄存器与操作 rs & rt -> rd
    "OR": lambda rs, rt: rs | rt,               #寄存器或操作
    "XOR": lambda rs, rt: rs ^ rt,              #寄存器异或操作
    "NOR": lambda rs, rt: ~(rs | rt),           #寄存器或非操作
    "SLT": lambda rs, rt: 1 if rs < rt else 0,  #寄存器值比较操作 如果rs < rt，返回1；反之，返回0
    "ADDI": lambda rs, imm: rs + imm,           #寄存器+立即数操作
    "ANDI": lambda rs, imm: rs & imm,           #寄存器-立即数操作
    "ORI": lambda rs, imm: rs | imm,            #寄存器或立即数操作
    "XORI": lambda rs, imm: rs ^ imm            #寄存器异或立即数操作
}

#参数：二进制数字
#将补码的二进制数字转换成十进制数
def bin2dec(bin_num):
    if bin_num[0] == '0':               #如果首位为0，为非负数
        dec_num = int(bin_num[1:],2)    #直接调用函数
    else:                               #如果首位为1，则为负数，先取反，再+1，获得负数的原码，然后再翻译，注意前面有个负号
        revers_num = ''
        for num in bin_num[1:]:
            if num == "0":
                revers_num += "1"
            else:
                revers_num += "0"
        dec_num = -(int(revers_num,2) + 1)
    return dec_num

#参数:十进制数字，移动方向，移动位数
#将寄存器中的十进制数字转换位补码的二进制数，再进行逻辑移位操作，再将其变成十进制数字返回
#返回：移位好的十进制数字
def move_logic(dec_num, move_direct, move_num):
    move_bin = ""
    if dec_num < 0:                                             #先判断十进制数是正数or负数
        dec_num += 1
        bin_dec = bin(dec_num)                                  #先将其转换为二进制 -0bxxxxx
        bin_dec = bin_dec.replace("-0b", "")                    #将前缀去掉
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):
            rev_bin += "1"                                      #将前面不足的位数，用符号位（1）补足
        for num in bin_dec:                                     #变成补码形式
            if num == '1':
                rev_bin += '0'
            else:
                rev_bin += '1'
    else:
        bin_dec = bin(dec_num)
        bin_dec = bin_dec.replace("0b", "")
        rev_bin = ""
        for i in range(0, BIN_DATA_LEN - len(bin_dec)):         #将前面补足的位数，用符号位（0）补足
            rev_bin += "0"
        rev_bin += bin_dec

    if move_direct == "left":                                   #判断移位方向
        move_bin += rev_bin[move_num:]                          #根据移动位数，取后面的32-num位，前面的num放弃
        for i in range(0, move_num):                            #用0补足后面的num位数
            move_bin += '0'
    if move_direct == "right":
        for i in range(0, move_num):                            #用0补足前面的num位
            move_bin += '0'
        for i in range(0, BIN_DATA_LEN - move_num):             #取前面的32-num位，后面的num位放弃
            move_bin += rev_bin[i]
    return bin2dec(move_bin)
#翻译机器指令变成汇编语句的函数
#参数：全部的机器码
#返回值：机器指令+指令地址+翻译出来的汇编 按照指定的格式输出
def handle_code(binary_code):
    current_loc = BEGIN_ADDR                                                        #current_loc保存当前指令存放的地址，第一个地址就是题目指定的初始地址
    flag_code = True                                                                #判断当前译码的是指令还是数据
    assembly_code = ''                                                              #存放完成译码的指令或是数据
    for bin_instr in binary_code.split('\n'):                                       #将指令一条一条的读取，以\n作为指令之间的分界
        #print(bin_instr)
        if bin_instr == '':                                                         #最后一行是空格，如果继续处理会报错，所以将之排除
            continue
        if flag_code:                                                               #当在处理指令时
            tran_ass = instruction[bin_instr[0:2]](bin_instr)                       #翻译指令：先根据机器码的前2位，判断是 算术逻辑指令or 非算术逻辑指令 -> 进入到不同的指令处理区
            assembly_code += "%s\t%d\t%s\n" %(bin_instr, current_loc, tran_ass)     #按照指定格式存放，每一行三列：原机器码\t指令存放的位置\t汇编指令
            instruction[current_loc] = tran_ass                                     #将翻译好的汇编指令存放在字典中，方便后面仿真的时候调用 指令地址: 指令名
            if tran_ass == "BREAK":                                                 #如果当前读取的是BREAK指令，意味着后面就是数据区了
                flag_code = False
                data_loc = current_loc + INSTRUCTION_LEN                            #数据指示地址，在处理数据时需要用到
                global  data_addr
                data_addr = data_loc                                                #获得数据基地址，为一个全局变量，以方便其他函数调用
            current_loc += INSTRUCTION_LEN                                          #更新当前指令地址
            #print(tran_ass)
        else:
            dec_num = bin2dec(bin_instr)                                            #将二进制的补码翻译成十进制数字
            assembly_code += "%s\t%d\t%s\n" % (bin_instr, current_loc, dec_num)     #按照指定格式存放，每一行三列：原机器码\t指令存放的位置\t汇编指令
            data[data_loc] = dec_num                                                #将翻译好的数据存放在字典中，方便后面仿真的时候调用 数据地址：数据
            data_loc += DATA_LEN
            current_loc += DATA_LEN                                              #更新当前指令存放
    return assembly_code

#参数：每一条指令，当前的PC值
#计算机模拟每一条不同的指令的执行过程
#返回执行该指令后pc的值和break标志
def execute_instr(instr, pc):
    flag_break = False                                                                  #判断程序是否终止的标志，是出现BREAK，就意味着程序终止了; True：程序终止；False:程序未终止
    instr_part = instr.replace(', ', ' ').split(' ')                                    #将指令进行切割，执行数之间是通过“，”相隔，而执行数和操作数之间是通过空格，所以统一换成空格，再进行切割
    if instr_part[0] in ("ADD", "SUB", "MUL", "AND", "OR", "XOR", "NOR", "SLT"):        #若操作指令是 寄存器算术逻辑指令 的一个   格式统一为 operand rd,rs,rt （ADD R2,R1,R5）
        rs_data = registers[int(instr_part[2].replace("R",""))]                         #获取当前rs寄存器中的值，eg："R6" -> "6" -> 6 -> register[6]
        rt_data = registers[int(instr_part[3].replace("R",""))]                         #获取当前rt寄存器中的值，"R4"
        rd_data = simluation_cate_2[instr_part[0]](rs_data, rt_data)                    #得到rs、rt操作后的值，存放在rd_data中
        registers[int(instr_part[1].replace("R",""))] = rd_data                         #将rd_data的值传入register[rd]中
        pc += INSTRUCTION_LEN                                                           #pc向下移位

    elif instr_part[0] in ("ADDI", "ANDI", "ORI", "XORI"):                              #若操作指令是 寄存器-立即数算术逻辑指令 的一个 格式统一为 operand rd rs imm （ADDI R2,R4,#34）
        rs_data = registers[int(instr_part[2].replace("R",""))]                         #获取register[rs]
        imm_data = int(instr_part[3].replace("#", ""))                                  #获取立即数的值
        rd_data = simluation_cate_2[instr_part[0]](rs_data, imm_data)                   #将rs、imm操作后的值，存放在rd_data中
        registers[int(instr_part[1].replace("R",""))] = rd_data                         #将rd_data的值传入register[rd]中
        pc += INSTRUCTION_LEN                                                           #pc向下移动

    elif instr_part[0] == 'J':                                                          #无条件转移，立即数为操作数 operand imm -> J #340
        pc = int(instr_part[1].replace("#",""))
    elif instr_part[0] == 'JR':                                                         #无条件转移，寄存器值为操作数 operand imm -> JR R3
        pc = registers[int(instr_part[1].replace("R",""))]
    elif instr_part[0] == 'BEQ':                                                        #相等即跳转，否则不跳转；先执行后跳转，且跳转在pc的基础上进行的。pc+4是一定会执行的 operand rs rt off -> BEQ R3,R5,#23
        rs_data = registers[int(instr_part[1].replace("R",""))]                         #获取register[rs]
        rt_data = registers[int(instr_part[2].replace("R",""))]                         #获取register[rt]
        offset = int(instr_part[3].replace("#",""))                                     #获取偏移量
        pc += INSTRUCTION_LEN                                                           #pc向下移动
        if rs_data == rt_data:                                                          #若register[rs]、register[rt]相等，就跳转
            pc += offset
    elif instr_part[0] in ('BLTZ','BGTZ'):                                              #register[rs]<0/register[rs]>0 即跳转，否则不跳转； operand rs off -> BLTZ R4,#23/BGTZ R4,#23
        rs_data = registers[int(instr_part[1].replace("R",""))]                         #获取register[rs]
        offset = int(instr_part[2].replace("#",""))                                     #获取偏移量
        pc += INSTRUCTION_LEN                                                           #pc向下移动
        if instr_part[0] == 'BLTZ':                                                     #若为BLTZ，即小于0就跳转
            if rs_data < 0:
                pc += offset
        else:                                                                           #若为BGTZ，即大于0就跳转
            if rs_data > 0:
                pc += offset
    elif instr_part[0] == 'BREAK':                                                      #出现BREAK，就将标志致为True
        flag_break = True
    elif instr_part[0] in ('SW','LW'):                                                  #寄存器的值存放到memory中/将memory的值存放在寄存器中  operand rt off(base) -> SW R3,#356(R4)/LW R5,#380(R4)   ->memory[356+R4] = R3/ R5 = memory[380+R4]
        rt = int(instr_part[1].replace("R",""))                                         #获取rt
        mix = instr_part[2].split('(')                                                  # 形如 #380(R5) 进行切割 mix=["#380", "R5)"]
        offset = int(mix[0].replace("#",""))                                            #获得偏移量
        base_data = registers[int(mix[1].replace("R","").replace(")",""))]              #将"R5)" -> "5)" ->"5" ->5 -> register[5]
        if instr_part[0] == "SW":                                                       #如果为SW,store
            data[offset + base_data] = registers[rt]                                    #寄存器的值存放在data对应的位置
        else:                                                                           #如果为LW，load
            registers[rt] =  data[offset + base_data]                                   #data对应位置的值存放在寄存器中
        pc += INSTRUCTION_LEN
    elif instr_part[0] in ('SLL', 'SRL', 'SRA'):                                        #移位操作 SLL/SRL/SRA 逻辑左移/逻辑右移/算术右移(先逻辑右移，再把最高为复制)   operand rd rt sa -> SLL R3,R4,#2/SRL R5,R6,#3/SRA R1,R16,#2
        rt = int(instr_part[2].replace("R",""))                                         #获取rt
        rd = int(instr_part[1].replace("R",""))                                         #获取rd
        sa = int(instr_part[3].replace("#",""))                                         #获取sa
        if instr_part[0] == 'SLL':
            registers[rd] = move_logic(registers[rt], "left", sa)                       #逻辑左移，并赋值
        elif instr_part[0] == 'SRL':
            registers[rd] = move_logic(registers[rt], "right", sa)                      #逻辑右移并赋值
        else:
            registers[rd] = registers[rt] >> sa                                         #算术右移
        pc += INSTRUCTION_LEN
    elif instr_part[0] == 'NOP':                                                        #不进行任何操作
        pc += INSTRUCTION_LEN
    return pc, flag_break

#将执行过程按照指定要求输出
#参数：当前执行步数，当前pc值
#返回：str格式的输出formated_output
def format_output(cycle, pc):
    output = ""
    output += "--------------------\nCycle:%d\t%d\t%s\n\nRegisters\n" %(cycle, pc, instruction[pc])
    output+= "R00:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
             "R08:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
             "R16:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" \
             "R24:\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n\nData\n" %(tuple(registers))
    data_output = ""
    i = 0
    data_loc = data_addr
    for data_v in data.values():
        if i == 0 or i % 8 == 0:
            data_output += str(data_loc)+':\t%d\t' %(data_v)
        elif i % 8 == 7 and i != 0:
            data_output +='%d\n' %(data_v)
        else:
            data_output += '%d\t' %(data_v)
        data_loc += DATA_LEN
        i += 1
    if i % 8 != 0:
        output += data_output + '\n' + '\n'
    else:
        output += data_output+'\n'
    return output

#模拟计算机执行汇编指令
#参数：无
#返回：str格式输出的，按照格式要求的所有执行结果的format_simu_output
def simulate_instruction():
    cycle = 1                                                                       #记录执行的步数
    pc = BEGIN_ADDR                                                                 #pc存放的是指令位置
    format_simu_output = ""
    while True:
        format_simu_output += format_output(cycle, pc)
        pc, break_flag = execute_instr(instruction[pc], pc)                         #执行pc指向的指令，返回pc的位置和break标志
        if break_flag:                                                              #如果break_flag = True，就跳出循环
            #print("in")
            break
        cycle += 1

    return format_simu_output

#参数：输出的内容，文件路径
#将输出的内容，写入文件
def write_file(output, file_path):
    try:
        out_file = open(file_path,"w")  #可写形式，打开文件
    except:
        print("can't open the file!")   #打不开抛出异常，程序结束
        sys.exit(1)
    try:
        out_file.write(output)          #写入内容
    except:
        print("can't write to the file!")   #写不了抛出异常，程序结束
        sys.exit(1)
    finally:
        out_file.close()                #关闭文件

#参数：文件路径;
#返回：文件内容，str格式
#打开文件
def read_File(file_path):
    try:
        binary_file = open(file_path, "r")  #只读形式，打开文件
    except:
        print("can't open the file!")       #打不开则抛出异常，程序结束
        sys.exit(1)
    try:
        binary_code = binary_file.read()    #读取文件内容，存放在binary_code中
    except:
        print("can't read the file!")       #读不了则抛出异常，程序结束
        sys.exit(1)
    finally:
        binary_file.close()                 #将文件关闭
    #print(binary_code)
    return  binary_code

if __name__ == '__main__':
    filename = sys.argv;     #用户自行输入需要译码的文件名字
    binary_code = read_File(filename[1])                   #读取存放机器指令的文件
    assemble_code = handle_code(binary_code)            #处理读取出来的机器指令进行反汇编
    write_file(assemble_code,'./disassembly.txt')       #将翻译好的汇编指令写入指定文件
    simulation_output = simulate_instruction()
    write_file(simulation_output,'./simulation.txt')