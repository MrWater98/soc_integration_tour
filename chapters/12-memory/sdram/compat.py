"""Restore Migen's CSR variable-name tracing for Python 3.11 CALL bytecode."""
import dis


def enable_python311_csr_names():
    import migen.fhdl.tracer as tracer

    original = tracer.get_var_name

    def get_var_name(frame):
        try:
            found = original(frame)
            if found is not None:
                return found
        except (IndexError, KeyError):
            pass
        instructions = list(dis.get_instructions(frame.f_code))
        for index, instruction in enumerate(instructions):
            if instruction.offset != frame.f_lasti:
                continue
            for candidate in instructions[index + 1:]:
                if candidate.opname in ("STORE_ATTR", "STORE_FAST", "STORE_NAME", "STORE_DEREF"):
                    return candidate.argval
                if candidate.opname in ("POP_TOP", "RETURN_VALUE"):
                    return None
            return None
        return None

    tracer.get_var_name = get_var_name
