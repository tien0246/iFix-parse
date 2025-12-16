import struct
import io
import os
import argparse
import math
from typing import List, Dict, Any, Tuple, Optional, Callable
from enum import Enum, auto

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def colorize(text: str, color: str, use_color: bool = True) -> str:
        if not use_color:
            return text
        return f"{color}{text}{Colors.ENDC}"


class OperandType(Enum):
    InlineNone = auto()
    InlineInt = auto()
    InlineString = auto()
    InlineType = auto()
    InlineField = auto()
    InlineMethod = auto()
    InlineBrTarget = auto()
    InlineTok = auto()
    InlineVar = auto()
    InlineStackSpace = auto()
    InlineSwitch = auto()
    Inline8Byte = auto()


class FlowControl(Enum):
    Next = auto()
    Branch = auto()
    CondBranch = auto()
    Return = auto()
    Call = auto()
    Throw = auto()
    Meta = auto()

class OpCode:
    def __init__(self, code: int, name: str, operand_type: OperandType, flow: FlowControl = FlowControl.Next):
        self.code = code
        self.name = name
        self.operand_type = operand_type
        self.flow = flow

    @property
    def mnemonic(self) -> str:
        return self.name.lower().replace('_', '.')

OPCODES: Dict[int, OpCode] = {}

def register_op(code: int, name: str, operand_type: OperandType, flow: FlowControl = FlowControl.Next):
    OPCODES[code] = OpCode(code, name, operand_type, flow)

OPCODE_MAP_UNITY = {
    0: 'Conv_I1',
    1: 'Ldelem_I',
    2: 'Cgt',
    3: 'Mul',
    5: 'Stobj',
    6: 'Ldftn',
    7: 'Conv_I8',
    8: 'Ldloca',
    9: 'Shr',
    11: 'Bgt',
    12: 'Callvirtvirt',
    13: 'Ldarga',
    15: 'Ldobj',
    16: 'Ldobj',
    17: 'Bgt_Un',
    19: 'Conv_Ovf_I4',
    20: 'Shl',
    21: 'Neg',
    22: 'Box',
    23: 'Stelem_Ref',
    24: 'Isinst',
    25: 'Newarr_Prim',
    27: 'Ldelem_I1',
    28: 'Ldc_I8',
    29: 'Conv_U4',
    30: 'Bge_Un',
    33: 'Ble_Un',
    34: 'Ldflda',
    35: 'Conv_U2',
    36: 'Stloc',
    37: 'Conv_I8',
    39: 'Ldstr',
    40: 'Cgt_Un',
    41: 'Stind_I4',
    42: 'Conv_I2',
    43: 'Beq',
    44: 'Stind_R8',
    45: 'Call',
    46: 'Conv_I1',
    47: 'Blt_Un',
    48: 'Stelem_I8',
    49: 'Conv_Ovf_I4_Un',
    51: 'Stind_I1',
    52: 'Ldelem_R4',
    53: 'Unbox',
    55: 'Conv_Ovf_U8',
    56: 'Ldobj',
    57: 'Conv_R4',
    58: 'Conv_R4',
    59: 'Conv_Ovf_U2',
    60: 'Ldsfld',
    61: 'Conv_U1',
    62: 'Starg',
    63: 'Conv_I2',
    64: 'Conv_Ovf_I4',
    65: 'Rethrow',
    66: 'Stelem_I4',
    67: 'Newanon',
    68: 'Conv_R8',
    69: 'Conv_Ovf_I1',
    71: 'Add_Ovf_Un',
    72: 'Ldloc',
    73: 'Calli',
    74: 'Ldelem_I2',
    75: 'Stfld',
    76: 'Not',
    77: 'Ldobj',
    78: 'Conv_U1',
    79: 'Or',
    80: 'Add',
    81: 'Ldobj',
    82: 'Ldelem_Ref',
    83: 'Ldobj',
    84: 'Div',
    85: 'Stsfld',
    86: 'Ldobj',
    87: 'Throw',
    88: 'Castclass',
    89: 'Newarr',
    90: 'Xor',
    91: 'Mul_Ovf_Un',
    93: 'Br',
    94: 'Ldtoken',
    95: 'Ldtype',
    96: 'Stobj',
    97: 'Call',
    98: 'Ldelem_U2',
    99: 'Stind_Ref',
    100: 'Ldc_R8',
    101: 'Conv_Ovf_I2',
    103: 'Ret',
    105: 'Ret',
    108: 'Conv_Ovf_U2',
    109: 'Blt',
    110: 'Bne_Un',
    111: 'Blt_Un',
    112: 'Conv_U4',
    113: 'Stelem_I1',
    115: 'Stind_I2',
    116: 'Blt',
    117: 'Initobj',
    119: 'Stind_R4',
    120: 'Conv_U8',
    121: 'Stelem_R8',
    122: 'Callvirt',
    123: 'Ldelem_I1',
    124: 'Stelem_R4',
    125: 'Bge',
    126: 'Sub',
    127: 'Brtrue',
    128: 'Pop',
    129: 'Stelem_Ref',
    130: 'Div_Un',
    131: 'Conv_U1',
    132: 'Stelem_I8',
    133: 'Unbox_Any',
    134: 'Brfalse',
    135: 'Unbox_Any',
    136: 'Add_Ovf',
    137: 'Ldobj',
    138: 'Calli',
    139: 'Ldlen',
    140: 'Conv_U4',
    141: 'Ldc_I4',
    143: 'Ldc_I4',
    144: 'Dup',
    145: 'Conv_Ovf_U8',
    147: 'Stelem_I',
    148: 'And',
    149: 'Switch',
    150: 'Conv_U4',
    151: 'Newobj',
    153: 'Leave',
    155: 'Ldobj',
    156: 'Ldelem_U4',
    158: 'Stind_Ref',
    159: 'Ldelem_R8',
    160: 'Rem',
    161: 'Box',
    162: 'Ldvirtftn',
    163: 'Conv_Ovf_I1',
    164: 'Ldarg',
    165: 'Stind',
    166: 'Ceq',
    167: 'Ldfld',
    168: 'Ldobj',
    169: 'Shr_Un',
    170: 'Ldelem_I4',
    171: 'Rem_Un',
    172: 'Ldobj',
    173: 'Ret',
    174: 'Conv_R8',
    175: 'Stelem_Ref',
    176: 'Ble',
    177: 'Rethrow',
    178: 'Conv_U8',
    179: 'Mul',
}

for c, n in OPCODE_MAP_UNITY.items():
    ot = OperandType.InlineNone
    flow = FlowControl.Next

    if n in ['Ldc_I4', 'Ldc_R4', 'Ldc_I4_S']:
        ot = OperandType.InlineInt
    elif n == 'Ldstr':
        ot = OperandType.InlineString
    elif n in ['Ldc_I8', 'Ldc_R8']:
        ot = OperandType.Inline8Byte
    elif n in ['Ldarg', 'Ldarga', 'Ldloc', 'Ldloca', 'Stloc', 'Starg']:
        ot = OperandType.InlineVar
    elif n in ['Br', 'Brtrue', 'Brfalse', 'Beq', 'Bne_Un', 'Bge', 'Bgt', 'Ble', 'Blt', 'Bge_Un', 'Bgt_Un', 'Ble_Un', 'Blt_Un', 'Leave']:
        ot = OperandType.InlineBrTarget
        if n in ['Br', 'Leave']:
            flow = FlowControl.Branch
        else:
            flow = FlowControl.CondBranch
    elif n == 'Switch':
        ot = OperandType.InlineSwitch
        flow = FlowControl.CondBranch
    elif n in ['Call', 'Callvirt', 'Newobj', 'Ldftn', 'Ldvirtftn', 'Callvirtvirt', 'Calli']:
        if n == 'Newobj':
            ot = OperandType.InlineType
        else:
            ot = OperandType.InlineMethod
        flow = FlowControl.Call
    elif n in ['Ldfld', 'Ldflda', 'Stfld', 'Ldsfld', 'Stsfld']:
        ot = OperandType.InlineField
    elif n in ['Box', 'Unbox', 'Isinst', 'Castclass', 'Newarr', 'Ldobj', 'Stobj', 'Initobj', 'Newanon', 'Ldtype', 'Unbox_Any']:
        ot = OperandType.InlineType
    elif n == 'Ldtoken':
        ot = OperandType.InlineTok
    elif n in ['Ret', 'Throw', 'Rethrow']:
        if n == 'Ret':
            flow = FlowControl.Return
        else:
            flow = FlowControl.Throw

    register_op(c, n, ot, flow)


register_op(146, 'StackSpace', OperandType.InlineStackSpace, FlowControl.Meta)


class PatchFile:
    def __init__(self):
        self.magic = 0
        self.bridge_name = ""
        self.wrappers_manager_name = ""
        self.assembly_string = ""
        self.extern_types: List[str] = []
        self.extern_methods: List[Dict] = []
        self.intern_strings: List[str] = []
        self.fields: List[Dict] = []
        self.static_fields: List[Tuple[int, int]] = []
        self.anon_storeys: List[Dict] = []
        self.fix_infos: List[Dict] = []
        self.new_classes: List[str] = []
        self.methods: List[Dict] = []


class BinaryReader:
    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)
        self.length = len(data)

    def read_byte(self) -> int:
        b = self.stream.read(1)
        if not b:
            raise EOFError()
        return ord(b)

    def read_bool(self) -> bool:
        return self.read_byte() != 0

    def read_int(self) -> int:
        return struct.unpack('<i', self.stream.read(4))[0]

    def read_ulong(self) -> int:
        return struct.unpack('<Q', self.stream.read(8))[0]
        
    def read_instructions(self, count) -> List[Tuple[int, int]]:
        raw = self.stream.read(8 * count)
        if len(raw) < 8 * count:
            raise EOFError("Incomplete instructions")
        return list(struct.iter_unpack('<ii', raw))

    def read_string(self) -> str:
        length = 0
        shift = 0
        while True:
            byte = self.read_byte()
            length |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
        if length == 0:
            return ""
        return self.stream.read(length).decode('utf-8', errors='replace')


class PatchParser:
    def __init__(self, filepath: str):
        with open(filepath, 'rb') as f:
            self.reader = BinaryReader(f.read())
        self.patch = PatchFile()

    def parse(self) -> PatchFile:
        r = self.reader
        p = self.patch

        p.magic = r.read_ulong()
        p.bridge_name = r.read_string()

        p.extern_types = []
        for _ in range(r.read_int()):
            p.extern_types.append(r.read_string())

        for _ in range(r.read_int()):
            code_len = r.read_int()
            insts = r.read_instructions(code_len)

            eh_count = r.read_int()
            ehs = []
            for _ in range(eh_count):
                ehs.append(struct.unpack('<iiiiii', r.stream.read(24)))

            p.methods.append({'instructions': insts, 'exceptions': ehs})

        for _ in range(r.read_int()):
            is_generic = r.read_bool()
            decl_type = r.read_int()
            name = r.read_string()

            gen_args, params = [], []
            if is_generic:
                gen_args = [r.read_int() for _ in range(r.read_int())]
                for _ in range(r.read_int()):
                    if r.read_bool():
                        r.read_string()
                    else:
                        params.append(r.read_int())
            else:
                params = []
                for _ in range(r.read_int()):
                    params.append(r.read_int())

            p.extern_methods.append({
                'name': name, 'type_id': decl_type, 'params': params,
                'generic_args': gen_args, 'is_generic': is_generic
            })

        p.intern_strings = []
        for _ in range(r.read_int()):
            p.intern_strings.append(r.read_string())

        for _ in range(r.read_int()):
            is_new = r.read_bool()
            decl = r.read_int()
            name = r.read_string()
            p.fields.append({'name': name, 'type_id': decl, 'is_new': is_new})
            if is_new:
                r.stream.read(8)

        for _ in range(r.read_int()):
            p.static_fields.append(struct.unpack('<ii', r.stream.read(8)))

        for _ in range(r.read_int()):
            f_types = []
            for _ in range(r.read_int()):
                f_types.append(r.read_int())
            ctor = r.read_int()
            ctor_p = r.read_int()
            itfs = []
            for _ in range(r.read_int()):
                itfs.append(r.read_int())
            vtable = []
            for _ in range(r.read_int()):
                vtable.append(r.read_int())
            p.anon_storeys.append({'fields': f_types, 'ctor': ctor, 'vtable': vtable})

        p.wrappers_manager_name = r.read_string()
        p.assembly_string = r.read_string()

        for _ in range(r.read_int()):
            is_gen = r.read_bool()
            decl = r.read_int()
            name = r.read_string()
            gen_args, params = [], []

            if is_gen:
                gen_args = []
                for _ in range(r.read_int()):
                    gen_args.append(r.read_int())
                for _ in range(r.read_int()):
                    if r.read_bool():
                        r.read_string()
                    else:
                        params.append(r.read_int())
            else:
                params = []
                for _ in range(r.read_int()):
                    params.append(r.read_int())

            patch_id = r.read_int()
            p.fix_infos.append({
                'name': name, 'type_id': decl, 'params': params,
                'generic_args': gen_args, 'patch_id': patch_id, 'is_generic': is_gen
            })

        p.new_classes = []
        for _ in range(r.read_int()):
            p.new_classes.append(r.read_string())

        return p


class TablePrinter:
    def __init__(self, headers: List[str]):
        self.headers = headers
        self.rows: List[List[str]] = []
        self.col_widths = [len(h) for h in headers]

    def add_row(self, row: List[Any]):
        s_row = [str(x) for x in row]
        self.rows.append(s_row)
        for i, val in enumerate(s_row):
            if i < len(self.col_widths):
                self.col_widths[i] = max(self.col_widths[i], len(val))

    def print(self, indent: str = ""):
        header_str = "  ".join([h.ljust(w) for h, w in zip(self.headers, self.col_widths)])
        print(f"{indent}{Colors.BOLD}{header_str}{Colors.ENDC}")
        print(f"{indent}" + "-" * (sum(self.col_widths) + 2 * (len(self.headers) - 1)))

        for row in self.rows:
            row_str = "  ".join([c.ljust(w) for c, w in zip(row, self.col_widths)])
            print(f"{indent}{row_str}")
        print("")


class Disassembler:
    def __init__(self, patch: PatchFile, use_color: bool = True, debug: bool = False):
        self.p = patch
        self.use_color = use_color
        self.debug = debug

    def _type_name(self, idx: int) -> str:
        if 0 <= idx < len(self.p.extern_types):
            full_name = self.p.extern_types[idx]
            if not self.debug:
                import re
                full_name = re.sub(r', Version=[\d\.]+', '', full_name)
                full_name = re.sub(r', Culture=[\w-]+', '', full_name)
                full_name = re.sub(r', PublicKeyToken=\w+', '', full_name)

                if '[' not in full_name:
                    full_name = full_name.split(',')[0].strip()
                else:
                    last_bracket = full_name.rfind(']')
                    if last_bracket != -1:
                        suffix = full_name[last_bracket+1:]
                        if ',' in suffix:
                            full_name = full_name[:last_bracket+1]

            return Colors.colorize(full_name, Colors.CYAN, self.use_color)
        return f"UnknownType({idx})"

    def format_val(self, op_info: OpCode, operand: int, idx: int, insts: List[Tuple[int, int]]) -> Tuple[str, int]:
        val_str = ""
        consumed = 0
        ot = op_info.operand_type

        if ot == OperandType.InlineNone:
            val_str = ""
        elif ot == OperandType.InlineInt:
            val_str = str(operand)
            if op_info.name.startswith('Ldc_I4') and abs(operand) > 1000:
                try:
                    raw = struct.pack('<i', operand)
                    f_val = struct.unpack('<f', raw)[0]
                    if 0.0001 < abs(f_val) < 1000000 or f_val == 0.0:
                        val_str = f"{f_val} ({operand})"
                except:
                    pass
        elif ot == OperandType.InlineString:
            if 0 <= operand < len(self.p.intern_strings):
                s = self.p.intern_strings[operand]
            else:
                s = f"str_{operand}"
            val_str = f'"{Colors.colorize(s, Colors.GREEN, self.use_color)}"'
        elif ot == OperandType.InlineType:
            val_str = self._type_name(operand)
        elif ot == OperandType.InlineMethod:
            mid = operand & 0xFFFF
            narg = operand >> 16
            if mid < len(self.p.extern_methods):
                m = self.p.extern_methods[mid]
                t = self._type_name(m['type_id'])
                if m['generic_args']:
                    args = f"<{','.join(self._type_name(x) for x in m['generic_args']) }>"
                else:
                    args = ""
                val_str = f"{t}::{Colors.colorize(m['name'], Colors.WARNING, self.use_color)}{args}"
            else:
                val_str = f"method_{mid} (args={narg})"
        elif ot == OperandType.InlineField:
            if 0 <= operand < len(self.p.fields):
                f = self.p.fields[operand]
                val_str = f"{self._type_name(f['type_id'])}::{f['name']}"
            else:
                val_str = f"field_{operand}"
        elif ot == OperandType.InlineBrTarget:
            target = idx + operand
            val_str = f"IL_{target:04X}"
        elif ot == OperandType.InlineVar:
            val_str = f"V_{operand}"
        elif ot == OperandType.InlineStackSpace:
            max_stack = operand & 0xFFFF
            locals_cnt = operand >> 16
            val_str = f"MaxStack: {max_stack}, Locals: {locals_cnt}"

        elif ot == OperandType.Inline8Byte:
            if idx + 1 < len(insts):
                next_code, next_op = insts[idx + 1]
                raw_bytes = struct.pack('<ii', next_code, next_op)
                if op_info.name == 'Ldc_R8':
                    val = struct.unpack('<d', raw_bytes)[0]
                    val_str = f"{val} (0x{struct.unpack('<Q', raw_bytes)[0]:X})"
                else:
                    val = struct.unpack('<q', raw_bytes)[0]
                    val_str = f"{val}"
                consumed = 1
            else:
                val_str = "<EOF>"

        elif ot == OperandType.InlineSwitch:
            count = operand
            slots_needed = (count + 1) // 2

            targets = []
            current_slot = 0
            while current_slot < slots_needed:
                if idx + 1 + current_slot >= len(insts):
                    break
                c, o = insts[idx + 1 + current_slot]

                targets.append(c)
                if len(targets) < count:
                    targets.append(o)

                current_slot += 1

            consumed = slots_needed
            val_str = f"({', '.join(f'IL_{idx + t:04X}' for t in targets) })"

        return val_str, consumed

    def print_summary(self):
        print(f"{Colors.HEADER} IFix Patch Summary {Colors.ENDC}")
        print(f"Magic:      0x{self.p.magic:X}")
        print(f"Bridge:     {self.p.bridge_name}")
        print(f"Wrappers:   {self.p.wrappers_manager_name}")
        print(f"Counts:     {len(self.p.extern_types)} Types, {len(self.p.extern_methods)} Methods, {len(self.p.fix_infos)} Fixes")
        print("")

    def print_tables(self):
        print(f"{Colors.HEADER} [1] Header Info {Colors.ENDC}")
        print(f"Magic:      0x{self.p.magic:X}")
        print(f"Bridge:     {self.p.bridge_name}")
        print(f"Wrappers:   {self.p.wrappers_manager_name}")
        print(f"Assembly:   {self.p.assembly_string}")
        print("")

        print(f"{Colors.HEADER} [2] Extern Types ({len(self.p.extern_types)}) {Colors.ENDC}")
        for i, t in enumerate(self.p.extern_types):
            print(f"  {i}: {self._type_name(i)}")
        print("")

        print(f"{Colors.HEADER} [3] Extern Methods ({len(self.p.extern_methods)}) {Colors.ENDC}")
        tbl = TablePrinter(["ID", "Type", "Method", "Params", "Generic"])
        for i, m in enumerate(self.p.extern_types):
            pass
        for i, m in enumerate(self.p.extern_methods):
            t_name = self._type_name(m['type_id'])
            p_str = ", ".join([self._type_name(x) for x in m['params']])
            if m['generic_args']:
                g_str = str(m['generic_args'])
            else:
                g_str = ""
            tbl.add_row([i, t_name, m['name'], p_str, g_str])
        tbl.print("  ")
        print("")

        print(f"{Colors.HEADER} [4] Intern Strings ({len(self.p.intern_strings)}) {Colors.ENDC}")
        for i, s in enumerate(self.p.intern_strings):
            print(f"  {i}: \"{Colors.colorize(s, Colors.GREEN, self.use_color)}\"")
        print("")

        print(f"{Colors.HEADER} [5] Fields ({len(self.p.fields)}) {Colors.ENDC}")
        tbl = TablePrinter(["ID", "Type", "Name", "New?"])
        for i, f in enumerate(self.p.fields):
            t_name = self._type_name(f['type_id'])
            tbl.add_row([i, t_name, f['name'], f['is_new']])
        tbl.print("  ")
        print("")

        print(f"{Colors.HEADER} [6] Static Fields ({len(self.p.static_fields)}) {Colors.ENDC}")
        for i, sf in enumerate(self.p.static_fields):
            print(f"  {i}: TypeID={sf[0]} ({self._type_name(sf[0])}), CctorID={sf[1]}")
        print("")

        print(f"{Colors.HEADER} [7] Anonymous Storeys ({len(self.p.anon_storeys)}) {Colors.ENDC}")
        for i, s in enumerate(self.p.anon_storeys):
            print(f"  {i}: Fields={len(s['fields'])}, Ctor={s['ctor']}, VTableSize={len(s['vtable'])}")
        print("")

        print(f"{Colors.HEADER} [8] Fix Table ({len(self.p.fix_infos)}) {Colors.ENDC}")
        tbl = TablePrinter(["PatchID", "Class", "Method", "Params"])
        for fix in self.p.fix_infos:
            t_name = self._type_name(fix['type_id'])
            param_type_names = []
            for pid in fix['params']:
                param_type_names.append(self._type_name(pid))
            p_str = ", ".join(param_type_names)
            tbl.add_row([fix['patch_id'], t_name, fix['name'], p_str])
        tbl.print("  ")
        print("")

        print(f"{Colors.HEADER} [9] New Classes ({len(self.p.new_classes)}) {Colors.ENDC}")
        for i, c in enumerate(self.p.new_classes):
            print(f"  {i}: {c}")
        print("")

    def print_code(self, method_id: Optional[int] = None):
        print(f"{Colors.HEADER} Disassembly {Colors.ENDC}")

        if method_id is not None:
            targets = [method_id]
        else:
            targets = range(len(self.p.methods))

        for mid in targets:
            if mid >= len(self.p.methods):
                continue

            patches = []
            for f in self.p.fix_infos:
                if f['patch_id'] == mid:
                    patches.append(f)

            header_note = ""
            if patches:
                p = patches[0]
                t_name = self._type_name(p['type_id'])
                header_note = f" (Patches {t_name}::{p['name']})"

            print(f"{Colors.BOLD}.method {mid:02d}{header_note}{Colors.ENDC}")
            print("{")

            method = self.p.methods[mid]
            insts = method['instructions']

            idx = 0
            while idx < len(insts):
                code, op = insts[idx]
                op_info = OPCODES.get(code)

                debug_prefix = ""
                if self.debug:
                    debug_prefix = f"[{code:02X} {op:08X}] "

                if op_info:
                    mnemonic = Colors.colorize(op_info.mnemonic.ljust(12), Colors.BLUE, self.use_color)
                    val_str, consumed = self.format_val(op_info, op, idx, insts)

                    if code == 146:
                        print(f"  // {mnemonic} {val_str}")
                    else:
                        print(f"  IL_{idx:04X}: {debug_prefix}{mnemonic} {val_str}")

                    for k in range(consumed):
                        pass

                    idx += 1 + consumed
                else:
                    print(f"  IL_{idx:04X}: {debug_prefix}unknown_0x{code:X} {op}")
                    idx += 1

            if method['exceptions']:
                print("\n  // Exception Handlers")
                for eh in method['exceptions']:
                    c_type = self._type_name(eh[1])
                    print(f"  .try IL_{eh[2]:04X} to IL_{eh[3]:04X} catch {c_type} handler IL_{eh[4]:04X} to IL_{eh[5]:04X}")

            print("}\n")


def main():
    parser = argparse.ArgumentParser(description='Advanced IFix Disassembler')
    parser.add_argument('file', help='Input .dec file')
    parser.add_argument('--summary', action='store_true', help='Show file summary')
    parser.add_argument('--tables', action='store_true', help='Show metadata tables')
    parser.add_argument('--disasm', action='store_true', help='Show disassembly')
    parser.add_argument('--method', type=int, help='Disassemble specific method ID')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    parser.add_argument('--debug', action='store_true', help='Show raw hex values')

    args = parser.parse_args()

    if not (args.summary or args.tables or args.disasm or args.method is not None):
        args.summary = True
        args.tables = True
        args.disasm = True

    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found.")
        return

    try:
        p = PatchParser(args.file).parse()
        d = Disassembler(p, not args.no_color, args.debug)

        if args.summary:
            d.print_summary()
        if args.tables:
            d.print_tables()
        if args.disasm or args.method is not None:
            d.print_code(args.method)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()