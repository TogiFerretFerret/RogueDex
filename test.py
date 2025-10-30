from battledex_engine.roguescript.vm import VirtualMachine, InterpretResult
from battledex_engine.roguescript.errors import RogueScriptRuntimeError
vm=VirtualMachine()
code = """
        var a = "global";
        {
            var a = "local";
            print a;
        }
        print a;
        a; # Final expression should be "global"
        """
try:
    v=vm.interpret(code)
    print(v)
except RogueScriptRuntimeError as e:
    print(f"Runtime Error: {e}")
