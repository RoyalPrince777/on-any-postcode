"""Bounded educational instruction core for OAP Digital Silicon.

Independent software-only execution experiment; not RISC-V, hardware, or SMI authority.
Instructions are immutable (opcode, destination, source, immediate) tuples.
"""
from __future__ import annotations

from dataclasses import dataclass

REGISTER_COUNT = 8
MAX_STEPS = 1000
WORD_MASK = (1 << 32) - 1
OPCODES = frozenset({"LI", "ADD", "ADDI", "XOR", "HALT"})


@dataclass(frozen=True)
class Instruction:
    opcode: str
    rd: int = 0
    rs: int = 0
    immediate: int = 0


@dataclass(frozen=True)
class ExecutionResult:
    registers: tuple[int, ...]
    steps: int
    halted: bool


def execute(program: tuple[Instruction, ...], *, max_steps: int = MAX_STEPS) -> ExecutionResult:
    """Execute a finite, deterministic program without I/O or external access.

    Register 0 is hardwired to zero. All arithmetic wraps to unsigned 32-bit.
    Programs must end in HALT and remain within the caller's step budget.
    """
    if not isinstance(program, tuple) or not program:
        raise ValueError("Program must be a nonempty instruction tuple")
    if not 1 <= max_steps <= MAX_STEPS:
        raise ValueError("Step budget must be between 1 and 1000")
    for instruction in program:
        if not isinstance(instruction, Instruction) or instruction.opcode not in OPCODES:
            raise ValueError("Unknown instruction")
        if not all(type(v) is int and 0 <= v < REGISTER_COUNT for v in (instruction.rd, instruction.rs)):
            raise ValueError("Invalid register index")
        if type(instruction.immediate) is not int or not -(1 << 31) <= instruction.immediate < (1 << 31):
            raise ValueError("Immediate out of signed 32-bit range")
    registers = [0] * REGISTER_COUNT
    for pc, instruction in enumerate(program):
        if pc >= max_steps:
            raise RuntimeError("Instruction budget exhausted")
        opcode = instruction.opcode
        if opcode == "HALT":
            return ExecutionResult(tuple(registers), pc + 1, True)
        if opcode == "LI":
            value = instruction.immediate
        elif opcode == "ADD":
            value = registers[instruction.rd] + registers[instruction.rs]
        elif opcode == "ADDI":
            value = registers[instruction.rs] + instruction.immediate
        else:
            value = registers[instruction.rd] ^ registers[instruction.rs]
        if instruction.rd != 0:
            registers[instruction.rd] = value & WORD_MASK
    raise RuntimeError("Program ended without HALT")
