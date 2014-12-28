from __future__ import print_function
import xml.etree.ElementTree as ET
import os


class Instruction:
    """Instruction is defines by its mnemonic name (in Intel-style assembly).

    An instruction may have multiple forms, that mainly differ by operand types.

    :ivar name: instruction name in Intel-style assembly (Peach-Py, NASM and YASM assemblers).
    :ivar summary: a summary description of the instruction name.
    :ivar forms: a list of :class:`InstructionForm` objects representing the instruction forms.
    """
    def __init__(self, name):
        self.name = name
        self.summary = None
        self.forms = []

    def __str__(self):
        """Returns string representation of the instruction and the number of instruction forms"""
        return "%s (%d forms)" % (self.name, len(self.forms))

    def __repr__(self):
        return str(self)


class InstructionForm:
    """Instruction form is a combination of mnemonic name and operand types.

    An instruction form may have multiple possible encodings.

    :ivar name: instruction name in Peach-Py, NASM and YASM assemblers.
    :ivar gas_name: instruction form name in GNU assembler (gas).
    :ivar go_name: instruction form name in Go/Plan 9 assembler (8a).

        None means instruction is not supported in Go/Plan 9 assembler.

    :ivar mmx_mode: MMX technology state required or forced by this instruction. Possible values are:

        "FPU"
            Instruction requires the MMX technology state to be clear.

        "MMX"
            Instruction causes transition to MMX technology state.

        None
            Instruction neither affects nor cares about the MMX technology state.

    :ivar xmm_mode: XMM registers state accessed by this instruction. Possible values are:

        "SSE"
            Instruction accesses XMM registers in legacy SSE mode.

        "AVX"
            Instruction accesses XMM registers in AVX mode.

        None
            Instruction does not affect XMM registers and does not change XMM registers access mode.

    :ivar operands: a list of :class:`Operand` objects representing the instruction operands.
    :ivar implicit_inputs: a set of register names that are implicitly read by this instruction.
    :ivar implicit_outputs: a set of register names that are implicitly written by this instruction.
    :ivar isa_extensions: a list of :class:`ISAExtension` objects that represent the ISA extensions required to execute
        the instruction.
    :ivar encodings: a list of :class:`Encoding` objects representing the possible encodings for this instruction.
    """

    def __init__(self, name):
        self.name = name
        self.gas_name = None
        self.go_name = None
        self.mmx_mode = None
        self.xmm_mode = None
        self.operands = []
        self.implicit_inputs = set()
        self.implicit_outputs = set()
        self.isa_extensions = []
        self.encodings = []

    def __str__(self):
        """Returns string representation of the instruction form and its operands in Intel-style assembly"""
        if self.operands:
            return self.name + " " + ", ".join([operand.type for operand in self.operands])
        else:
            return self.name

    def __repr__(self):
        return str(self)


class Operand:
    """An explicit instruction operand.

    :ivar type: the type of the instruction operand. Possible values are:

        "1"
            The constant value `1`.

        "3"
            The constant value `3`.

        "al"
            The al register.

        "ax"
            The ax register.

        "eax"
            The eax register.

        "rax"
            The rax register.

        "cl"
            The cl register.

        "xmm0"
            The xmm0 register.

        "rel8"
            An 8-bit signed offset relative to the address of instruction end.

        "rel32"
            A 32-bit signed offset relative to the address of instruction end.

        "imm8"
            An 8-bit immediate value.

        "imm16"
            A 16-bit immediate value.

        "imm32"
            A 32-bit immediate value.

        "imm64"
            A 64-bit immediate value.

        "r8"
            An 8-bit general-purpose register (al, bl, cl, dl, sil, dil, bpl, spl, r8b-r15b).

        "r8l"
            A legacy 8-bit general-purpose register (al, ah, bl, bh, cl, ch, dl, dh).

        "r16"
            A 16-bit general-purpose register (ax, bx, cx, dx, si, di, bp, sp, r8w-r15w).

        "r16l"
            A legacy 16-bit general-purpose register (ax, bx, cx, dx, si, di, bp, sp).

        "r32"
            A 32-bit general-purpose register (eax, ebx, ecx, edx, esi, edi, ebp, esp, r8d-r15d).

        "r32l"
            A legacy 32-bit general-purpose register (eax, ebx, ecx, edx, esi, edi, ebx, esp).

        "r64"
            A 64-bit general-purpose register (rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp, r8-r15).

        "mm"
            A 64-bit MMX SIMD register (mm0-mm7).

        "xmm"
            A 128-bit XMM SIMD register (xmm0-xmm31).

        "ymm"
            A 256-bit YMM SIMD register (ymm0-ymm31).

        "zmm"
            A 512-bit ZMM SIMD register (zmm0-zmm31).

        "m"
            A memory operand of any size.

        "m8"
            An 8-bit memory operand.

        "m16"
            A 16-bit memory operand.

        "m32"
            A 32-bit memory operand.

        "m64"
            A 64-bit memory operand.

        "m80"
            An 80-bit memory operand.

        "m128"
            A 128-bit memory operand.

        "m256"
            A 256-bit memory operand.

        "m512"
            A 512-bit memory operand.

    :ivar is_input: indicates if the instruction reads the variable specified by this operand.
    :ivar is_output: indicates if the instruction writes the variable specified by this operand.
    """
    def __init__(self, type):
        self.type = type
        self.is_input = False
        self.is_output = False

    def __str__(self):
        """Return string representation of the operand type and its read/write attributes"""
        return {
            (False, False): self.type,
            (True, False): "[in] " + self.type,
            (False, True): "[out] " + self.type,
            (True, True): "[in/out] " + self.type
        }[(self.is_input, self.is_output)]

    def __repr__(self):
        return str(self)

    @property
    def is_variable(self):
        """Indicates whether this operand refers to a variable (i.e. specifies either a register or a memory location)"""
        return self.is_input or self.is_output

    @property
    def is_register(self):
        """Indicates whether this operand specifies a register"""
        return self.type in {"al", "cl", "ax", "eax", "rax", "xmm0", "r8", "r16", "r32", "r64", "r8l", "r16l", "r32l", "mm", "xmm", "ymm"}

    @property
    def is_memory(self):
        """Indicates whether this operand specifies a memory location"""
        return self.type in {"m", "m8", "m16", "m32", "m64", "m80", "m128", "m256", "m512"}


class ISAExtension:
    """An extension to x86-64 instruction set.

    :ivar name: name of the ISA extension. Possible values are:

        - "RDTSC"     := The `RDTSC` instruction.
        - "RDTSCP"    := The `RDTSCP` instruction.
        - "CPUID"     := The `CPUID` instruction.
        - "POPCNT"    := The `POPCNT` instruction.
        - "LZCNT"     := The `LZCNT` instruction.
        - "PCLMULQDQ" := The `PCLMULQDQ` instruction.
        - "RDRAND"    := The `RDRAND` instruction.
        - "RDSEED"    := The `RDSEED` instruction.
        - "CMOV"      := Conditional MOVe instructions.
        - "MMX"       := MultiMedia eXtension.
        - "SSE"       := Streaming SIMD Extension.
        - "SSE2"      := Streaming SIMD Extension 2.
        - "SSE3"      := Streaming SIMD Extension 3.
        - "SSSE3"     := Supplemental Streaming SIMD Extension 3.
        - "SSE4.1"    := Streaming SIMD Extension 4.1.
        - "SSE4.2"    := Streaming SIMD Extension 4.2.
        - "AVX"       := Advanced Vector eXtension.
        - "AVX2"      := Advanced Vector eXtension 2.
        - "F16C"      := Half-Precision (F16) Conversion instructions.
        - "FMA3"      := Fused Multiply-Add instructions (3-operand).
        - "BMI"       := Bit Manipulation Instructions.
        - "BMI2"      := Bit Manipulation Instructions 2.
        - "ADX"       := The `ADCX` and `ADOX` instructions.
        - "AES"       := `AES` instruction set.
        - "SHA"       := `SHA` instruction set.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        """Returns the name of the ISA extension"""
        return self.name


class Encoding:
    """Instruction encoding

    :ivar components: a list of :class:`Prefix`, :class:`REX`, :class:`VEX`, :class:`Opcode`, :class:`ModRM`, \
        :class:`ImmediateByte`, :class:`ImmediateWord`, :class:`ImmediateDWord`, :class:`ImmediateQWord`, \
        :class:`DataOffset32`, :class:`DataOffset64`, :class:`CodeOffset8`, or :class:`CodeOffset32` objects that \
        specify the components of encoded instruction
    """

    def __init__(self):
        self.components = []


class Prefix:
    """0x66/0xF2/0xF3 prefix

    :ivar is_mandatory: indicates that the prefix is used not for its primary purpose, but for extending instruction \
        opcode. Mandatory prefixes are common in SSE instructions. Non-mandatory prefix is usually 0x66 that modifies \
        the instruction to operate on 16-bit operands.
    :ivar byte: numerical representation of the prefix byte.
    """

    def __init__(self, byte, is_mandatory):
        self.byte = byte
        self.is_mandatory = is_mandatory


class REX:
    """REX prefix.

    Encoding may have only one REX prefix and if present, it immediately precedes the opcode.

    :ivar is_mandatory: indicates whether the REX prefix must be encoded even if no extended registers are used.

        REX is mandatory for most 64-bit instructions (encoded with REX.W = 1) and instructions that operate on the \
        extended set of 8-bit registers (to indicate access to dil/sil/bpl/spl as opposed to ah/bh/ch/dh which use the \
        same ModR/M).

    :ivar W: the REX.W bit. Possible values are 0, 1, and None.

        None indicates that the bit is ignored.

    :ivar R: the REX.R bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If R is a reference to an instruction operand, the operand is of register type and REX.R bit specifies the \
        high bit (bit 3) of the register number.

    :ivar B: the REX.B bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If R is a reference to an instruction operand, the operand can be of register or memory type. If the operand \
        is of register type, the REX.R bit specifies the high bit (bit 3) of the register number, and the REX.X bit is \
        ignored. If the operand is of memory type, the REX.R bit specifies the high bit (bit 3) of the base register \
        number, and the X instance variable refers to the same operand.

    :ivar X: the REX.X bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If X is a reference to an instruction operand, the operand is of memory type and the REX.X bit specifies the \
        high bit (bit 3) of the index register number, and the B instance variable refers to the same operand.
    """

    def __init__(self, is_mandatory):
        self.is_mandatory = is_mandatory
        self.W = None
        self.R = None
        self.X = None
        self.B = None

    def set_ignored(self, w=0, r=0, x=0, b=0):
        """Sets values for ignored bits

        :param int w: the value (0 or 1) to be assigned to REX.W bit if it is ignored.
        :param int r: the value (0 or 1) to be assigned to REX.R bit if it is ignored.
        :param int x: the value (0 or 1) to be assigned to REX.X bit if it is ignored.
        :param int b: the value (0 or 1) to be assigned to REX.B bit if it is ignored.
        """
        assert w in {0, 1}, "REX.W can be only 0 or 1"
        assert r in {0, 1}, "REX.R can be only 0 or 1"
        assert x in {0, 1}, "REX.X can be only 0 or 1"
        assert b in {0, 1}, "REX.B can be only 0 or 1"
        if self.W is None:
            self.W = w
        if self.R is None:
            self.R = r
        if self.X is None:
            self.X = x
        if self.B is None:
            self.B = b


class VEX:
    """VEX prefix.

    Encoding may have only one VEX prefix and if present, it immediately precedes the opcode, and no other prefix is \
    allowed.

    :ivar mmmmm: the VEX m-mmmm (implied leading opcode bytes) field. Possible values are:

        0b00001
            Implies 0x0F leading opcode byte.

        0b00010
            Implies 0x0F 0x38 leading opcode bytes.

        0b00011
            Implies 0x0F 0x3A leading opcode bytes.

        Only VEX prefix with m-mmmm equal to 0b00001 could be encoded in two bytes.

    :ivar pp: the VEX pp (implied legacy prefix) field. Possible values are:

        0b00
            No implied prefix.

        0b01
            Implied 0x66 prefix.

        0b10
            Implied 0xF3 prefix.

        0b11
            Implied 0xF2 prefix.

    :ivar W: the VEX.W bit. Possible values are 0, 1, and None.

        None indicates that the bit is ignored.

    :ivar L: the VEX.L bit. Possible values are 0, 1, and None.

        None indicates that the bit is ignored.

    :ivar R: the VEX.R bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If R is a reference to an instruction operand, the operand is of register type and VEX.R bit specifies the \
        high bit (bit 3) of the register number.

    :ivar B: the VEX.B bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If R is a reference to an instruction operand, the operand can be of register or memory type. If the operand is \
        of register type, the VEX.R bit specifies the high bit (bit 3) of the register number, and the VEX.X bit is \
        ignored. If the operand is of memory type, the VEX.R bit specifies the high bit (bit 3) of the base register \
        number, and the X instance variable refers to the same operand.

    :ivar X: the VEX.X bit. Possible values are 0, 1, None, or a reference to one of the instruction operands.

        The value None indicates that this bit is ignored. \
        If X is a reference to an instruction operand, the operand is of memory type and the VEX.X bit specifies the \
        high bit (bit 3) of the index register number, and the B instance variable refers to the same operand.

    :ivar vvvv: the VEX vvvv field. Possible values are 0b1111 or a reference to one of the instruction operands.

        The value 0b1111 indicates that this field is not used.
        If vvvv is a reference to an instruction operand, the operand is of register type and VEX.vvvv field specifies \
        its number.
    """

    def __init__(self):
        self.mmmmm = None
        self.pp = None
        self.W = None
        self.L = None
        self.R = None
        self.X = None
        self.B = None
        self.vvvv = None

    def set_ignored(self, w=0, l=0, r=0, x=0, b=0):
        """Sets values for ignored bits

        :param int w: the value (0 or 1) to be assigned to VEX.W bit if it is ignored.
        :param int l: the value (0 or 1) to be assigned to VEX.L bit if it is ignored.
        :param int r: the value (0 or 1) to be assigned to VEX.R bit if it is ignored.
        :param int x: the value (0 or 1) to be assigned to VEX.X bit if it is ignored.
        :param int b: the value (0 or 1) to be assigned to VEX.B bit if it is ignored.
        """
        assert w in {0, 1}, "VEX.W can be only 0 or 1"
        assert l in {0, 1}, "VEX.L can be only 0 or 1"
        assert r in {0, 1}, "VEX.R can be only 0 or 1"
        assert x in {0, 1}, "VEX.X can be only 0 or 1"
        assert b in {0, 1}, "VEX.B can be only 0 or 1"
        if self.W is None:
            self.W = w
        if self.L is None:
            self.L = l
        if self.R is None:
            self.R = r
        if self.X is None:
            self.X = x
        if self.B is None:
            self.B = b


class Opcode:
    """Operation code

    Encoding may include more than one opcode. Opcodes do not necessarily go in sequence.

    :ivar byte: operation code as a byte integer (0 <= `byte` <= 255)
    :ivar addend: None or a reference to an instruction operand.

        If addend is a reference to an instruction operand, the operand is of register type and the three lowest bits
        of its number must be ORed with `byte` to produce the final opcode value.
    """
    def __init__(self, byte):
        self.byte = byte
        self.addend = None

    def __str__(self):
        return "0x%02X".format(self.byte)

    def __repr__(self):
        return str(self)


class ModRM:
    def __init__(self):
        self.mode = None
        self.rm = None
        self.reg = None


class ImmediateByte:
    def __init__(self):
        self.byte = None


class ImmediateWord:
    def __init__(self):
        self.word = None


class ImmediateDWord:
    def __init__(self):
        self.dword = None


class ImmediateQWord:
    def __init__(self):
        self.qword = None


class CodeOffset32:
    def __init__(self):
        self.offset = None


class CodeOffset8:
    def __init__(self):
        self.offset = None


class DataOffset32:
    def __init__(self):
        self.offset = None


class DataOffset64:
    def __init__(self):
        self.offset = None


def read_instruction_set(filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), "x86_64.xml")):
    xml_tree = ET.parse(filename)
    xml_instruction_set = xml_tree.getroot()
    assert xml_instruction_set.tag == "InstructionSet"
    assert xml_instruction_set.attrib["name"] == "x86-64"

    instruction_set = []
    for xml_instruction in xml_instruction_set:
        assert xml_instruction.tag == "Instruction"
        instruction = Instruction(xml_instruction.attrib["name"])
        instruction.summary = xml_instruction.attrib["summary"]
        for xml_instruction_form in xml_instruction:
            instruction_form = InstructionForm(instruction.name)
            instruction_form.gas_name = xml_instruction_form.attrib["gas-name"]
            instruction_form.go_name = xml_instruction_form.attrib.get("go-name")
            instruction_form.mmx_mode = xml_instruction_form.attrib.get("mmx-mode")
            instruction_form.xmm_mode = xml_instruction_form.attrib.get("xmm-mode")
            for xml_operand in xml_instruction_form.findall("Operands/Operand"):
                operand = Operand(xml_operand.attrib["type"])
                operand.is_input = {"true": True, "false": False}[xml_operand.attrib.get("input", "false")]
                operand.is_output = {"true": True, "false": False}[xml_operand.attrib.get("output", "false")]
                instruction_form.operands.append(operand)
            for xml_implicit_operand in xml_instruction_form.findall("Operands/ImplicitOperands"):
                if xml_implicit_operand.attrib["input"] == "true":
                    instruction_form.implicit_inputs.add(xml_implicit_operand.attrib["id"])
                if xml_implicit_operand.attrib["output"] == "true":
                    instruction_form.implicit_outputs.add(xml_implicit_operand.attrib["id"])
            for xml_isa_extension in xml_instruction_form.findall("ISA/Extension"):
                assert "id" in xml_isa_extension.attrib
                isa_extension = ISAExtension(xml_isa_extension.attrib["id"])
                instruction_form.isa_extensions.append(isa_extension)
            for xml_encoding in xml_instruction_form.findall("Encodings/Encoding"):
                encoding = Encoding()
                for xml_component in xml_encoding:
                    if xml_component.tag == "Prefix":
                        is_mandatory = {"true": True, "false": False}[xml_component.attrib["mandatory"]]
                        byte = int(xml_component.attrib["byte"], 16)
                        assert byte in {0x66, 0xF2, 0xF3}
                        prefix = Prefix(byte, is_mandatory)
                        encoding.components.append(prefix)
                    elif xml_component.tag == "REX":
                        assert "mandatory" in xml_component.attrib
                        is_mandatory = {"true": True, "false": False}[xml_component.attrib["mandatory"]]

                        rex = REX(is_mandatory)

                        assert "W" in xml_component.attrib
                        rex.W = xml_component.attrib["W"]
                        if rex.W == "ignored":
                            rex.W = None
                        else:
                            rex.W = int(rex.W)

                        if "R" in xml_component.attrib:
                            assert "R-operand-number" not in xml_component.attrib
                            rex.R = xml_component.attrib["R"]
                            if rex.R == "ignored":
                                rex.R = None
                            else:
                                rex.R = int(rex.R)
                        else:
                            assert "R-operand-number" in xml_component.attrib
                            rex.R = instruction_form.operands[int(xml_component.attrib["R-operand-number"])]

                        if "B" in xml_component.attrib:
                            assert "B-operand-number" not in xml_component.attrib
                            assert "BX-operand-number" not in xml_component.attrib
                            rex.B = xml_component.attrib["B"]
                            if rex.B == "ignored":
                                rex.B = None
                            else:
                                rex.B = int(rex.B)
                        elif "B-operand-number" in xml_component.attrib:
                            assert "B" not in xml_component.attrib
                            assert "BX-operand-number" not in xml_component.attrib
                            rex.B = instruction_form.operands[int(xml_component.attrib["B-operand-number"])]
                        else:
                            assert "BX-operand-number" in xml_component.attrib
                            assert "B-operand-number" not in xml_component.attrib
                            assert "B" not in xml_component.attrib
                            assert "X" not in xml_component.attrib
                            rex.B = instruction_form.operands[int(xml_component.attrib["BX-operand-number"])]

                        if "X" in xml_component.attrib:
                            assert "BX-operand-number" not in xml_component.attrib
                            rex.X = xml_component.attrib["X"]
                            if rex.X == "ignored":
                                rex.X = None
                            else:
                                rex.X = int(rex.X)
                        else:
                            assert "BX-operand-number" in xml_component.attrib
                            rex.X = instruction_form.operands[int(xml_component.attrib["BX-operand-number"])]
                        encoding.components.append(rex)
                    elif xml_component.tag == "VEX":
                        vex = VEX()

                        assert "W" in xml_component.attrib
                        vex.W = xml_component.attrib["W"]
                        if vex.W == "ignored":
                            vex.W = None
                        else:
                            vex.W = int(vex.W)

                        assert "L" in xml_component.attrib
                        vex.L = xml_component.attrib["L"]
                        if vex.L == "ignored":
                            vex.L = None
                        else:
                            vex.L = int(vex.L)

                        vex.mmmmm = int(xml_component.attrib["m-mmmm"], 2)
                        vex.pp = int(xml_component.attrib["pp"], 2)

                        if "R" in xml_component.attrib:
                            assert "R-operand-number" not in xml_component.attrib
                            vex.R = xml_component.attrib["R"]
                            if vex.R == "ignored":
                                vex.R = None
                            else:
                                vex.R = int(rex.R)
                        else:
                            assert "R-operand-number" in xml_component.attrib
                            vex.R = instruction_form.operands[int(xml_component.attrib["R-operand-number"])]

                        if "B" in xml_component.attrib:
                            assert "B-operand-number" not in xml_component.attrib
                            assert "BX-operand-number" not in xml_component.attrib
                            vex.B = xml_component.attrib["B"]
                            if vex.B == "ignored":
                                vex.B = None
                            else:
                                vex.B = int(rex.B)
                        elif "B-operand-number" in xml_component.attrib:
                            assert "B" not in xml_component.attrib
                            assert "BX-operand-number" not in xml_component.attrib
                            vex.B = instruction_form.operands[int(xml_component.attrib["B-operand-number"])]
                        else:
                            assert "BX-operand-number" in xml_component.attrib
                            assert "B-operand-number" not in xml_component.attrib
                            assert "B" not in xml_component.attrib
                            assert "X" not in xml_component.attrib
                            vex.B = instruction_form.operands[int(xml_component.attrib["BX-operand-number"])]

                        if "X" in xml_component.attrib:
                            assert "BX-operand-number" not in xml_component.attrib
                            vex.X = xml_component.attrib["X"]
                            if vex.X == "ignored":
                                vex.X = None
                            else:
                                vex.X = int(vex.X)
                        else:
                            assert "BX-operand-number" in xml_component.attrib
                            vex.X = instruction_form.operands[int(xml_component.attrib["BX-operand-number"])]

                        vex.vvvv = None
                        if "vvvv" in xml_component.attrib:
                            assert "vvvv-operand-number" not in xml_component.attrib
                            assert xml_component.attrib["vvvv"] == "1111"
                            vex.vvvv = int(xml_component.attrib["vvvv"], 2)
                        else:
                            assert "vvvv-operand-number" in xml_component.attrib
                            vex.vvvv = instruction_form.operands[int(xml_component.attrib["vvvv-operand-number"])]

                        encoding.components.append(vex)
                    elif xml_component.tag == "Opcode":
                        opcode = Opcode(int(xml_component.attrib["byte"], 16))
                        if "addend-operand-number" in xml_component.attrib:
                            opcode.addend = instruction_form.operands[int(xml_component.attrib["addend-operand-number"])]
                        encoding.components.append(opcode)
                    elif xml_component.tag == "ModRM":
                        modrm = ModRM()
                        if "mode" in xml_component.attrib:
                            modrm.mode = int(xml_component.attrib["mode"], 2)
                            assert modrm.mode == 0b11
                        else:
                            assert "mode-operand-number" in xml_component.attrib
                            assert xml_component.attrib["mode-operand-number"] == xml_component.attrib["rm-operand-number"]
                            modrm.mode = instruction_form.operands[int(xml_component.attrib["mode-operand-number"])]
                        if "reg" in xml_component.attrib:
                            modrm.reg = int(xml_component.attrib["reg"])
                            assert 0 <= modrm.reg <= 7
                        else:
                            assert "reg-operand-number" in xml_component.attrib
                            modrm.reg = instruction_form.operands[int(xml_component.attrib["reg-operand-number"])]
                        assert "rm-operand-number" in xml_component.attrib
                        modrm.rm = instruction_form.operands[int(xml_component.attrib["rm-operand-number"])]
                        encoding.components.append(modrm)
                    elif xml_component.tag == "Immediate":
                        assert "size" in xml_component.attrib
                        immediate_size = int(xml_component.attrib["size"])
                        assert immediate_size in {1, 2, 4, 8}
                        if immediate_size == 1:
                            immediate_byte = ImmediateByte()
                            if "operand-number" in xml_component.attrib:
                                immediate_byte.byte = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            else:
                                assert False
                            encoding.components.append(immediate_byte)
                        elif immediate_size == 2:
                            immediate_word = ImmediateWord()
                            assert "operand-number" in xml_component.attrib
                            immediate_word.word = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(immediate_word)
                        elif immediate_size == 4:
                            immediate_dword = ImmediateDWord()
                            assert "operand-number" in xml_component.attrib
                            immediate_dword.dword = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(immediate_dword)
                        elif immediate_size == 8:
                            immediate_qword = ImmediateQWord()
                            assert "operand-number" in xml_component.attrib
                            immediate_qword.qword = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(immediate_qword)
                        else:
                            assert False
                    elif xml_component.tag == "CodeOffset":
                        offset_size = int(xml_component.attrib["size"])
                        assert offset_size in {1, 4}
                        if offset_size == 1:
                            code_offset = CodeOffset8()
                            code_offset.offset = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(code_offset)
                        elif offset_size == 4:
                            code_offset = CodeOffset32()
                            code_offset.offset = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(code_offset)
                        else:
                            assert False
                    elif xml_component.tag == "DataOffset":
                        offset_size = int(xml_component.attrib["size"])
                        assert offset_size in {4, 8}
                        if offset_size == 4:
                            data_offset = DataOffset32()
                            data_offset.offset = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(data_offset)
                        elif offset_size == 8:
                            data_offset = DataOffset64()
                            data_offset.offset = instruction_form.operands[int(xml_component.attrib["operand-number"])]
                            encoding.components.append(data_offset)
                        else:
                            assert False
                    else:
                        print("Unknown encoding tag: " + xml_component.tag)

                instruction_form.encodings.append(encoding)
            instruction.forms.append(instruction_form)
        instruction_set.append(instruction)
    return instruction_set