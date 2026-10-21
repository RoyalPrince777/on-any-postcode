"""Independent regression tests for the isolated Digital Silicon instruction core."""
import pytest

from mission_control.digital_silicon_instruction_core import Instruction, execute


def test_deterministic_execution_and_zero_register():
    program = (
        Instruction("LI", rd=1, immediate=7),
        Instruction("LI", rd=2, immediate=5),
        Instruction("ADD", rd=1, rs=2),
        Instruction("ADDI", rd=3, rs=1, immediate=-2),
        Instruction("XOR", rd=3, rs=2),
        Instruction("LI", rd=0, immediate=99),
        Instruction("HALT"),
    )
    first = execute(program)
    assert first == execute(program)
    assert first.registers == (0, 12, 5, 15, 0, 0, 0, 0)
    assert first.steps == 7 and first.halted


def test_unsigned_word_wrap():
    result = execute((Instruction("LI", rd=1, immediate=-1),
                      Instruction("ADDI", rd=1, rs=1, immediate=1),
                      Instruction("HALT")))
    assert result.registers[1] == 0


@pytest.mark.parametrize("program", [
    (),
    (Instruction("UNKNOWN"), Instruction("HALT")),
    (Instruction("LI", rd=8), Instruction("HALT")),
    (Instruction("LI", immediate=1 << 31), Instruction("HALT")),
    (Instruction("LI", rd=True), Instruction("HALT")),
])
def test_invalid_programs_fail_closed(program):
    with pytest.raises(ValueError):
        execute(program)


def test_missing_halt_and_budget_fail_closed():
    with pytest.raises(RuntimeError, match="without HALT"):
        execute((Instruction("LI", rd=1),))
    with pytest.raises(RuntimeError, match="budget"):
        execute((Instruction("LI", rd=1), Instruction("HALT")), max_steps=1)
    with pytest.raises(ValueError):
        execute((Instruction("HALT"),), max_steps=0)
