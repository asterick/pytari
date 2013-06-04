#
#   6507 CPU core, interpretive opcode set
#   
#   Requirements:
#       Register Set: { S, A, X, Y, P, PC, PRE }
#       Bus Driver:
#           Push()      Pushes a value to the stack
#           Pull()      Pulls a value from the stack
#           Fetch()     Grabs a value off the bus
#           Throw()     Writes a value to the bus
#   
#   Pulls and pushes both preform their becrementation
#   post read / write, to conform to the perceived
#   method laid out by the cyclic timing chart
#

#
#   The flag getters and setters, this is purely for readability
#   of code, these will most likely be depreciated eventually, and
#   simply inlined.
#

def flag_carry( status ):
    return status & 0x01

def flag_zero( status ):
    return status & 0x02

def flag_interrupt( status ):
    return status & 0x04
    
def flag_decimal( status ):
    return status & 0x08

def flag_break( status ):
    return status & 0x10

def flag_overflow( status ):
    return status & 0x40

def flag_negitive( status ):
    return status & 0x80

def set_carry( registers, condition ):
    if condition:
        registers.P |= 0x01
    else:
        registers.P &= 0xFE

def set_zero( registers, value ):
    if not value:
        registers.P |= 0x02
    else:
        registers.P &= 0xFD

def set_interrupt( registers, condition ):
    if condition:
        registers.P |= 0x04
    else:
        registers.P &= 0xFB
    
def set_decimal( registers, condition ):
    if condition:
        registers.P |= 0x08
    else:
        registers.P &= 0xF7

def set_break( registers, condition ):
    if condition:
        registers.P |= 0x10
    else:
        registers.P &= 0xEF

def set_overflow( registers, condition ):
    if condition:
        registers.P |= 0x40
    else:
        registers.P &= 0xBF

def set_negitive( registers, value ):
    if value & 0x80:
        registers.P |= 0x80
    else:
        registers.P &= 0x7F

#
#  This is the actual code for instructions, only the stack
#  and jump instructions are hardcoded.  The templates are used
#  to reduce my risk of getting carpal tunnel syndrome.  Its a
#  robot designed to produce several functions based off the
#  addressing mode cycle charts found freely on the internet.
#
#  The calculation matrix is simply inserted into the functions,
#  I could have in theory broken it down into two diffrent
#  functions, but the usefulness of that is minimal, and this
#  will actually be faster.  
#
#  Commentary is very minimal for now, I will go back later
#  and insert information where I deem nessessary, most is
#  self explanitory.
#

UNDEFINED_OPCODE = "UndefinedOpcode"
BREAKPOINT = "BreakPointEncountered"

def inst_Undefined( registers, bus ):
    raise UNDEFINED_OPCODE, "Attempted to execute undefined opcode"

# 
#   Stack and Jump instructions
#

def inst_BRK_IMP( registers, bus ):
    bus.push( registers.PC >> 8 )
    bus.push( registers.PC & 0xFF )
    set_break( registers, 1 )
    bus.push( registers.P | 0x10 )
    set_interrupt( registers, 1 )
    registers.PC = bus.fetch( 0xFFFE )
    registers.PC |= bus.fetch( 0xFFFF ) << 8

def inst_RTI_IMP( registers, bus ):    
    bus.pull()
    registers.P = bus.pull() | 0x10
    registers.PC = bus.pull()
    registers.PC |= bus.fetch( registers.S | 0x100 ) << 8

def inst_RTS_IMP( registers, bus ):
    bus.pull()
    registers.PC = bus.pull()
    registers.PC |= bus.fetch( registers.S | 0x100 ) << 8
    bus.fetch( registers.PC )
    registers.PC += 1

def inst_PHA_IMP( registers, bus ):
    bus.push( registers.A )

def inst_PHP_IMP( registers, bus ):
    bus.push( registers.P | 0x10 )

def inst_PLA_IMP( registers, bus ):
    bus.pull()
    registers.A = bus.fetch( registers.S | 0x100 )
    set_zero( registers, registers.A )
    set_negitive( registers, registers.A )

def inst_PLP_IMP( registers, bus ):
    bus.pull()
    registers.P = bus.fetch( registers.S | 0x100 ) | 0x10

# Jump instructions (Special case)

def inst_JSR_ABS( registers, bus ):
    registers.PC = registers.PC + 1 & 0xFFFF
    bus.fetch( registers.S | 0x100 )
    bus.push( registers.PC >> 8 )
    bus.push( registers.PC & 0xFF )
    registers.PC = ( bus.fetch( registers.PC ) << 8 ) | registers.PRE

def inst_JMP_ABS( registers, bus ):
    registers.PC = registers.PC + 1 & 0xFFFF
    registers.PC = bus.fetch( registers.PC ) << 8 | registers.PRE

def inst_JMP_IND( registers, bus ):
    registers.PC = registers.PC + 1 & 0xFFFF
    src = bus.fetch( registers.PC ) << 8 | registers.PRE
    registers.PC = bus.fetch( src )
    src = (src + 1) & 0xFF | (src & 0xFF00)
    registers.PC |= bus.fetch( src ) << 8

#
#   Templating Matricies, used for the automated opcode generator 
#   to build opcode prototypes, these are to be destroied once the
#   generator has passed, INIT TIME only.
#
#   Accumulator functions will not be templated, as
#   they only have one addressing mode, and do not perform bus ops
#
#   Relative and Implied is templated simply to save me time
#

Accumulator = 'ACC'
Implied = 'IMP'
Relative = 'REL'
Immediate = 'IMM'
Absolute = 'ABS'
ZeroPage = 'ZZZ'
IndexedX = 'INX'
IndexedY = 'INY'
ZeroPageIndexedX = 'ZIX'
ZeroPageIndexedY = 'ZIY'
Indirect = 'IND'
PreIndexedX = 'PRE'
PostIndexedY = 'PST'

__OP_TEMPLATE = {
    'CLC':('R',['IMP']),
    'CLD':('R',['IMP']),
    'CLI':('R',['IMP']),
    'CLV':('R',['IMP']),
    'DEX':('R',['IMP']),
    'DEY':('R',['IMP']),
    'INX':('R',['IMP']),
    'INY':('R',['IMP']),
    'NOP':('R',['IMP']),
    'SEC':('R',['IMP']),
    'SED':('R',['IMP']),
    'SEI':('R',['IMP']),
    'TAX':('R',['IMP']),
    'TAY':('R',['IMP']),
    'TSX':('R',['IMP']),
    'TXA':('R',['IMP']),
    'TXS':('R',['IMP']),
    'TYA':('R',['IMP']),

    'ADC':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'AND':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'CMP':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'EOR':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'LDA':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'ORA':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),    
    'SBC':('R',['IMM','ZZZ','ZIX','ABS','INX','INY','PRE','PST']),    
    'STA':('W',['ZZZ','ZIX','ABS','INX','INY','PRE','PST']),
    'LDX':('R',['IMM','ZZZ','ZIY','ABS','INY']),
    'LDY':('R',['IMM','ZZZ','ZIX','ABS','INX']),
    'DEC':('RW',['ZZZ','ZIX','ABS','INX']),
    'INC':('RW',['ZZZ','ZIX','ABS','INX']),

    'ASL':('RW',['ACC','ZZZ','ZIX','ABS','INX']),
    'LSR':('RW',['ACC','ZZZ','ZIX','ABS','INX']),
    'ROL':('RW',['ACC','ZZZ','ZIX','ABS','INX']),
    'ROR':('RW',['ACC','ZZZ','ZIX','ABS','INX']),

    'CPX':('R',['IMM','ZZZ','ABS']),
    'CPY':('R',['IMM','ZZZ','ABS']),
    'STX':('W',['ZZZ','ZIY','ABS']),
    'STY':('W',['ZZZ','ZIX','ABS']),
    'BIT':('R',['ZZZ','ABS']),
    'BCC':('R',['REL']),
    'BCS':('R',['REL']),
    'BEQ':('R',['REL']),
    'BMI':('R',['REL']),
    'BNE':('R',['REL']),
    'BPL':('R',['REL']),
    'BVC':('R',['REL']),
    'BVS':('R',['REL']) 
    }

__CALC_TEMPLATE = {
    'ADC':"""temp = registers.A + fetch + flag_carry( registers.P )
    set_zero( registers, temp & 0xFF )
    if flag_decimal( registers.P ):
        if (registers.A & 0xF) + (fetch & 0xF) + flag_carry(registers.P) > 9:
            temp += 0x06
        set_negitive( registers, temp )
        set_overflow( registers, (not ( (registers.A ^ fetch) & 0x80 )) and ( (registers.A ^ temp) & 0x80 ) )
        if temp > 0x99:
            temp += 0x60
    else:
        set_negitive( registers, temp )
        set_overflow( registers, (not ( (registers.A ^ fetch) & 0x80 )) and ( (registers.A ^ temp) & 0x80 ) )
    set_carry( registers, temp > 0xFF )
    registers.A = 0xFF & temp""",
    'SBC':"""temp = registers.A - fetch - (not flag_carry( registers.P ))
    set_negitive( registers, temp )
    set_zero( registers, temp & 0xFF )
    set_overflow( registers, ( (registers.A ^ fetch) & 0x80 ) and ( (registers.A ^ temp) & 0x80 ) ) 
    if flag_decimal( registers.P ):
        if (( registers.A & 0xF ) - (not flag_carry(registers.P)) ) < ( fetch & 0xF ):
            temp -= 0x06
        if temp < 0x100:            # I KNOW THIS ISN'T RIGHT!!!
            temp -= 0x60
    set_carry( registers, temp >= 0 )
    registers.A = temp & 0xFF""",
    'ROL':"""temp = fetch
    fetch = ( fetch << 1 ) | ( flag_carry(registers.P) ) & 0xFF
    set_carry( registers, temp & 0x80 )
    set_zero( registers, fetch )
    set_negitive( registers, fetch )""",
    'ROR':"""temp = fetch
    fetch = ( fetch >> 1 ) | ( flag_carry(registers.P) << 7 )
    set_carry( registers, temp & 0x01 )
    set_zero( registers, fetch )
    set_negitive( registers, fetch )""",
    'ASL':"""set_carry( registers, fetch & 0x80 )
    fetch = (fetch << 1) & 0xFF
    set_zero( registers, fetch )
    set_negitive( registers, fetch )""",
    'LSR':"""set_carry( registers, fetch & 0x01 )
    fetch >>= 1
    set_zero( registers, fetch )
    set_negitive( registers, fetch )""",
    'CMP':"""fetch = (registers.A - fetch) & 0xFFFF
    set_carry( registers, fetch < 0x100 )
    set_zero( registers, fetch & 0xFF)
    set_negitive( registers, fetch )""",
    'CPX':"""fetch = (registers.X - fetch) & 0xFFFF
    set_carry( registers, fetch < 0x100 )
    set_zero( registers, fetch & 0xFF)
    set_negitive( registers, fetch )""",
    'CPY':"""fetch = (registers.Y - fetch) & 0xFFFF
    set_carry( registers, fetch < 0x100 )
    set_zero( registers, fetch & 0xFF)
    set_negitive( registers, fetch )""",    
    'DEC':"""fetch = fetch - 1 & 0xFF
    set_zero(registers, fetch)
    set_negitive(registers, fetch)""",
    'INC':"""fetch = fetch + 1 & 0xFF
    set_zero(registers,fetch)
    set_negitive(registers,fetch)""",
    'AND':"""registers.A &= fetch
    set_zero(registers,registers.A)
    set_negitive(registers,registers.A)""",
    'ORA':"""registers.A |= fetch
    set_zero(registers,registers.A)
    set_negitive(registers,registers.A)""",
    'EOR':"""registers.A ^= fetch
    set_zero(registers,registers.A)
    set_negitive(registers,registers.A)""",
    'BIT':"""registers.P = (fetch & 0xC0) | (registers.P & 0x3F)
    set_zero(registers, fetch & registers.A)""",
    'LDA':"""
    registers.A = fetch
    set_zero(registers,fetch)
    set_negitive(registers,fetch)""",
    'LDX':"""registers.X = fetch
    set_zero(registers,fetch)
    set_negitive(registers,fetch)""",
    'LDY':"""registers.Y = fetch
    set_zero(registers,fetch)
    set_negitive(registers,fetch)""",
    'CLC':"set_carry(registers,0)",
    'CLD':"set_decimal(registers,0)",
    'CLI':"set_interrupt(registers,0)",
    'CLV':"set_overflow(registers,0)",
    'SEC':"set_carry(registers,1)",
    'SED':"set_decimal(registers,1)",
    'SEI':"set_interrupt(registers,1)",
    'DEX':"""registers.X = registers.X - 1 & 0xFF
    set_zero(registers,registers.X)
    set_negitive(registers,registers.X)""",
    'DEY':"""registers.Y = registers.Y - 1 & 0xFF
    set_zero(registers,registers.Y)
    set_negitive(registers,registers.Y)""",
    'INX':"""registers.X = registers.X + 1 & 0xFF
    set_zero(registers,registers.X)
    set_negitive(registers,registers.X)""",
    'INY':"""registers.Y = registers.Y + 1 & 0xFF
    set_zero(registers,registers.Y)
    set_negitive(registers,registers.Y)""",
    'NOP':"pass",
    'TAX':"""registers.X = registers.A
    set_zero(registers,registers.X)
    set_negitive(registers,registers.X)""",
    'TAY':"""registers.Y = registers.A
    set_zero(registers,registers.Y)
    set_negitive(registers,registers.Y)""",
    'TSX':"""registers.X = registers.S
    set_zero(registers,registers.X)
    set_negitive(registers,registers.X)""",
    'TXA':"""registers.A = registers.X
    set_zero(registers,registers.X)
    set_negitive(registers,registers.X)""",
    'TXS':"registers.S = registers.X",
    'TYA':"""registers.A = registers.Y
    set_zero(registers,registers.A)
    set_negitive(registers,registers.A)""",    
    'STA':"fetch = registers.A",
    'STX':"fetch = registers.X",
    'STY':"fetch = registers.Y",
    'BCC':"not flag_carry(registers.P)",
    'BNE':"not flag_zero(registers.P)",
    'BVC':"not flag_overflow(registers.P)",
    'BPL':"not flag_negitive(registers.P)",
    'BCS':"flag_carry(registers.P)",
    'BEQ':"flag_zero(registers.P)",
    'BVS':"flag_overflow(registers.P)",
    'BMI':"flag_negitive(registers.P)",
    }

# WARNING!  Page bound is not enforced when loading the high byte of the effective
# address I do not know if this is suppose to be done or not. this is effective on
# pre and post indexed indirect

__MODE_TEMPLATE = {
    'R':{       # Read only instructions
        'IMP':"""
def inst_%s_IMP( registers, bus ):
    %s
""",
        'IMM':"""
def inst_%s_IMM( registers, bus ):
    registers.PC += 1
    fetch = registers.PRE
    %s
""",

        'ABS':"""
def inst_%s_ABS( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8 | registers.PRE
    registers.PC += 1
    fetch = bus.fetch( src )
    %s
""",

        'ZZZ':"""
def inst_%s_ZZZ( registers, bus ):
    registers.PC += 1
    fetch = bus.fetch( registers.PRE )
    %s
""",

        'ZIX':"""
def inst_%s_ZIX( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    fetch = bus.fetch( src )
    %s
""",

        'ZIY':"""
def inst_%s_ZIY( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.Y & 0xFF
    fetch = bus.fetch( src )
    %s
""",

        'INX':"""
def inst_%s_INX( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.X
    fetch = bus.fetch( offset & 0xFF | src )
    if (offset & 0x100):
        fetch = bus.fetch( offset + src & 0xFFFF )
    %s
""",

        'INY':"""
def inst_%s_INY( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.Y
    fetch = bus.fetch( offset & 0xFF | src )
    if (offset & 0x100):
        fetch = bus.fetch( offset + src & 0xFFFF )
    %s
""",

        'REL':"""
def inst_%s_REL( registers, bus ):
    registers.PC += 1
    if (%s):
        bus.fetch( registers.PC )
        if registers.PRE & 0x80:
            offset = -(registers.PRE & 0x7F ^ 0x7F) - 1
        else:
            offset = registers.PRE
        src = (registers.PC & 0xFF) + offset
        if ( src > 0xFF or src < 0 ):
            bus.fetch( (registers.PC & 0xFF00) | (src & 0xFF) )
        registers.PC = (registers.PC + offset) & 0xFFFF
""",

        'PRE':"""
def inst_%s_PRE( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    addr = bus.fetch( src )
    addr |= bus.fetch( src + 1 & 0xFF ) << 8
    fetch = bus.fetch( addr )
    %s
""",

        'PST':"""
def inst_%s_PST( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PRE )
    src |= bus.fetch( registers.PRE + 1 & 0xFF ) << 8
    offset = (src & 0xFF) + registers.Y
    if offset > 0xFF:
        bus.fetch( (offset & 0xFF) | (src & 0xFF00) )
    fetch = bus.fetch( src + registers.Y & 0xFFFF )
    %s
"""
        },
    'RW':{      # Read / Write instructions

        'ACC':"""
def inst_%s_ACC( registers, bus ):
    fetch = registers.A
    %s
    registers.A = fetch
""",

        'ABS':"""
def inst_%s_ABS( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8 | registers.PRE
    registers.PC += 1
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
""",

        'ZZZ':"""
def inst_%s_ZZZ( registers, bus ):
    registers.PC += 1
    fetch = bus.fetch( registers.PRE )
    bus.throw( registers.PRE, fetch )
    %s
    bus.throw( registers.PRE, fetch )
""",

        'ZIX':"""
def inst_%s_ZIX( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
""",

        'ZIY':"""
def inst_%s_ZIY( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.Y & 0xFF
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
""",

        'INX':"""
def inst_%s_INX( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.X
    fetch = bus.fetch( offset & 0xFF | src )
    src = offset + src & 0xFFFF
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
""",

        'INY':"""
def inst_%s_INY( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.Y
    fetch = bus.fetch( offset & 0xFF | src )
    src = offset + src & 0xFFFF
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
""",

        'PRE':"""
def inst_%s_PRE( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    addr = bus.fetch( src )
    addr |= bus.fetch( src + 1 & 0xFF ) << 8
    fetch = bus.fetch( addr )
    bus.throw( addr, fetch )
    %s
    bus.throw( addr, fetch )
""",

        'PST':"""
def inst_%s_PST( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PRE )
    src |= bus.fetch( registers.PRE + 1 & 0xFF ) << 8
    bus.fetch( (src + registers.Y & 0xFF) | (src & 0xFF00) )
    src = src + registers.Y & 0xFFFF
    fetch = bus.fetch( src )
    bus.throw( src, fetch )
    %s
    bus.throw( src, fetch )
"""
        },
    'W':{       # Write only instructions

        'ABS':"""
def inst_%s_ABS( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8 | registers.PRE
    registers.PC += 1
    fetch = bus.fetch( src )
    %s
    bus.throw( src, fetch )
""",

        'ZZZ':"""
def inst_%s_ZZZ( registers, bus ):
    registers.PC += 1
    %s
    bus.throw( registers.PRE, fetch )
""",

        'ZIX':"""
def inst_%s_ZIX( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    %s
    bus.throw( src, fetch )
""",

        'ZIY':"""
def inst_%s_ZIY( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.Y & 0xFF
    %s
    bus.throw( src, fetch )
""",
        
        'INX':"""
def inst_%s_INX( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.X
    bus.fetch( offset & 0xFF | src )
    src = offset + src & 0xFFFF
    %s
    bus.throw( src, fetch )
""",
        
        'INY':"""
def inst_%s_INY( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PC ) << 8
    bus.fetch( registers.PRE | src )
    registers.PC += 1
    offset = registers.PRE + registers.Y
    bus.fetch( offset & 0xFF | src )
    src = offset + src & 0xFFFF
    %s
    bus.throw( src, fetch )
""",
        
        'PRE':"""
def inst_%s_PRE( registers, bus ):
    registers.PC += 1
    bus.fetch( registers.PRE )
    src = registers.PRE + registers.X & 0xFF
    addr = bus.fetch( src )
    addr |= bus.fetch( src + 1 & 0xFF ) << 8
    fetch = bus.fetch( addr )
    %s
    bus.throw( addr, fetch )
""",

        'PST':"""
def inst_%s_PST( registers, bus ):
    registers.PC += 1
    src = bus.fetch( registers.PRE )
    src |= bus.fetch( registers.PRE + 1 & 0xFF ) << 8
    bus.fetch( (src + registers.Y & 0xFF) | (src & 0xFF00) )
    src = src + registers.Y & 0xFFFF
    %s
    bus.throw( src, fetch )
"""
        }
    }

for inst in __OP_TEMPLATE:
    access = __OP_TEMPLATE[inst][0]
    for addr in __OP_TEMPLATE[inst][1]:
        exec __MODE_TEMPLATE[access][addr] % (inst,__CALC_TEMPLATE[inst])

del __OP_TEMPLATE
del __MODE_TEMPLATE
del __CALC_TEMPLATE

#
#   This is the opcode execution matrix, it converts the definition
#   dictionary to a 256 index function array.  This is used for
#   fast execution of code.
#
#   Format:  {'Instruction':{'Addressing mode':OpCode, 'Addr':Op, etc},
#             'Instruction':... }
#
#   Conversion should be relatively simple, and provides easy debugging   
#   and some what readable tables.  Inlining this would be senseless.
#
#   This may be packed into the templating robot at a later time.
#

__OP_TABLE_SET = {
        'ADC':{'IMM':0x69, 'ZZZ':0x65, 'ZIX':0x75, 'ABS':0x6d, 'INX':0x7d, 'INY':0x79, 'PRE':0x61, 'PST':0x71},
        'AND':{'IMM':0x29, 'ZZZ':0x25, 'ZIX':0x35, 'ABS':0x2D, 'INX':0x3D, 'INY':0x39, 'PRE':0x21, 'PST':0x31},
        'ASL':{'ACC':0x0A, 'ZZZ':0x06, 'ZIX':0x16, 'ABS':0x0E, 'INX':0x1E},
        'BCC':{'REL':0x90},
        'BCS':{'REL':0xB0},
        'BEQ':{'REL':0xF0},
        'BIT':{'ZZZ':0x24, 'ABS':0x2C},
        'BMI':{'REL':0x30},        
        'BNE':{'REL':0xD0},
        'BPL':{'REL':0x10},
        'BRK':{'IMP':0x00},
        'BVC':{'REL':0x50},
        'BVS':{'REL':0x70},
        'CLC':{'IMP':0x18},
        'CLD':{'IMP':0xD8},
        'CLI':{'IMP':0x58},
        'CLV':{'IMP':0xB8},
        'CMP':{'IMM':0xC9, 'ZZZ':0xC5, 'ZIX':0xD5, 'ABS':0xCD, 'INX':0xDD, 'INY':0xD9, 'PRE':0xC1, 'PST':0xD1},
        'CPX':{'IMM':0xE0, 'ZZZ':0xE4, 'ABS':0xEC},
        'CPY':{'IMM':0xC0, 'ZZZ':0xC4, 'ABS':0xCC},
        'DEC':{'ZZZ':0xC6, 'ZIX':0xD6, 'ABS':0xCE, 'INX': 0xDE},
        'DEX':{'IMP':0xCA},
        'DEY':{'IMP':0x88},
        'EOR':{'IMM':0x49, 'ZZZ':0x45, 'ZIX':0x55, 'ABS':0x4d, 'INX':0x5d, 'INY':0x59, 'PRE':0x41, 'PST':0x51},
        'INC':{'ZZZ':0xE6, 'ZIX':0xF6, 'ABS':0xEE, 'INX': 0xFE},
        'INX':{'IMP':0xE8},
        'INY':{'IMP':0xC8},
        'JMP':{'ABS':0x4C,'IND':0x6C},
        'JSR':{'ABS':0x20},
        'LDA':{'IMM':0xA9, 'ZZZ':0xA5, 'ZIX':0xB5, 'ABS':0xAD, 'INX':0xBD, 'INY':0xB9, 'PRE':0xA1, 'PST':0xB1},
        'LDX':{'IMM':0xA2, 'ZZZ':0xA6, 'ZIY':0xB6, 'ABS':0xAE, 'INY':0xBE},
        'LDY':{'IMM':0xA0, 'ZZZ':0xA4, 'ZIX':0xB4, 'ABS':0xAC, 'INX':0xBC},
        'LSR':{'ACC':0x4A, 'ZZZ':0x46, 'ZIX':0x56, 'ABS':0x4E, 'INX':0x5E},
        'NOP':{'IMP':0xEA},
        'ORA':{'IMM':0x09, 'ZZZ':0x05, 'ZIX':0x15, 'ABS':0x0D, 'INX':0x1d, 'INY':0x19, 'PRE':0x01, 'PST':0x11},
        'PHA':{'IMP':0x48},
        'PHP':{'IMP':0x08},
        'PLA':{'IMP':0x68},
        'PLP':{'IMP':0x28},
        'ROL':{'ACC':0x2A, 'ZZZ':0x26, 'ZIX':0x36, 'ABS':0x2E, 'INX':0x3E},
        'ROR':{'ACC':0x6A, 'ZZZ':0x66, 'ZIX':0x76, 'ABS':0x6E, 'INX':0x7E},
        'RTI':{'IMP':0x40},
        'RTS':{'IMP':0x60},
        'SBC':{'IMM':0xE9, 'ZZZ':0xE5, 'ZIX':0xF5, 'ABS':0xED, 'INX':0xFD, 'INY':0xF9, 'PRE':0xE1, 'PST':0xF1},
        'SEC':{'IMP':0x38},
        'SED':{'IMP':0xF8},
        'SEI':{'IMP':0x78},
        'STA':{'ZZZ':0x85, 'ZIX':0x95, 'ABS':0x8d, 'INX':0x9d, 'INY':0x99, 'PRE':0x81, 'PST':0x91},
        'STX':{'ZZZ':0x86, 'ZIY':0x96, 'ABS':0x8E},
        'STY':{'ZZZ':0x84, 'ZIX':0x94, 'ABS':0x8C},
        'TAX':{'IMP':0xAA},
        'TAY':{'IMP':0xA8},
        'TSX':{'IMP':0xBA},
        'TXA':{'IMP':0x8A},
        'TXS':{'IMP':0x9A},
        'TYA':{'IMP':0x98}
    }

instTable = []
instDefs = []

while len(instTable) < 256:
    instTable.append(inst_Undefined)
    instDefs.append(('---','IMP'))

for inst in __OP_TABLE_SET:
    for mode in __OP_TABLE_SET[inst]:
        exec "instTable[" + hex(__OP_TABLE_SET[inst][mode]) + "] =inst_" + inst + "_" + mode
        exec "instDefs[" + hex(__OP_TABLE_SET[inst][mode]) + "] = ('" + inst + "','" + mode +"')"

del __OP_TABLE_SET
print "MESSAGE\tCPU Opcodes templated"
